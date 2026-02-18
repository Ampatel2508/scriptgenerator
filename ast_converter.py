import ast
import json
from typing import List, Dict, Any, Optional
from enum import Enum
import re

# Import validator for safety checks
from intent_validator import IntentValidator

class PlaywrightActionType(Enum):
    """Enum for Playwright action types"""
    NAVIGATE = "navigate"
    CLICK = "click"
    FILL_TEXT = "fill"
    SELECT = "select"
    WAIT = "wait"
    SCROLL = "scroll"
    HOVER = "hover"
    PRESS = "press"
    KEYBOARD = "keyboard"
    SCREENSHOT = "screenshot"

class PlaywrightAST:
    """Abstract Syntax Tree node for Playwright actions"""
    
    def __init__(self, action_type: PlaywrightActionType, **kwargs):
        self.action_type = action_type
        self.selector = kwargs.get("selector", None)
        self.value = kwargs.get("value", None)
        self.url = kwargs.get("url", None)
        self.wait_time = kwargs.get("wait_time", 5000)
        self.description = kwargs.get("description", "")
        self.element_html = kwargs.get("element_html", None)  # Store element HTML for better selectors
        self.children = []
        
    def to_dict(self) -> Dict:
        """Convert AST to dictionary"""
        return {
            "action_type": self.action_type.value,
            "selector": self.selector,
            "value": self.value,
            "url": self.url,
            "wait_time": self.wait_time,
            "description": self.description,
            "element_html": self.element_html,
            "children": [child.to_dict() for child in self.children]
        }

class ASTConverter:
    """Converts step intents to Playwright AST with strict safety validation"""
    
    def __init__(self):
        self.ast_nodes = []
        self.selector_cache = {}
        self.validator = IntentValidator()  # Rule 4: Pre-conversion safety checks
        self.conversion_errors = []
        self.conversion_warnings = []
        
    def convert_intent_to_ast(self, intent_obj: Dict, step_data: Dict) -> Optional[PlaywrightAST]:
        """
        Convert an intent to Playwright AST node
        RULE 4: Reject unsafe intent before building the AST
        RULE 10: Apply a selector sanity check as a final guardrail
        Handles both action intents and context events (waits)
        """
        
        # RULE 4: Pre-conversion safety check
        if not self._is_intent_safe_for_ast(intent_obj):
            self.conversion_errors.append(
                f"Step {intent_obj.get('step_index')}: Intent failed safety check, AST generation refused"
            )
            return None
        
        intent = intent_obj.get("intent", "")
        event_type = intent_obj.get("event_type", "")
        original_step = intent_obj.get("original_step", {})
        is_context_event = intent_obj.get("is_context_event", False)
        
        # Handle context events
        if is_context_event:
            # If the context event represents a navigation, emit a NAVIGATE node
            normalized_action = original_step.get("normalized_action", "").lower()
            if normalized_action == "navigate" or original_step.get("context_type", "").lower() == "navigation":
                nav_url = original_step.get("clean_url") or original_step.get("url")
                ast_node = PlaywrightAST(
                    action_type=PlaywrightActionType.NAVIGATE,
                    selector=None,
                    value=None,
                    url=nav_url,
                    description=intent or "Navigate (context event)"
                )
                return ast_node

            # Otherwise emit a WAIT node for other context events
            ast_node = PlaywrightAST(
                action_type=PlaywrightActionType.WAIT,
                selector=None,
                value=None,
                url=original_step.get("url", ""),
                wait_time=2000,  # Default wait for context events
                description=intent or "Wait for context event"
            )
            return ast_node
        
        # Determine action type based on intent and event type
        action_type = self._determine_action_type(intent, event_type)
        
        # Extract necessary parameters
        # PRIORITY: Use pre-built selector from intent_obj (from preprocessing), fallback to extraction
        selector = intent_obj.get("selector") or self._extract_selector(original_step)
        url = original_step.get("url", "")
        value = original_step.get("eventData", "")
        element_html = original_step.get("eventElement", "")  # Store HTML for better selector generation
        
        # RULE 10: Final selector sanity check
        if selector and not self.validator._is_valid_css_selector(selector):
            self.conversion_warnings.append(
                f"Step {intent_obj.get('step_index')}: Selector '{selector}' failed sanity check, skipping"
            )
            return None
        
        # Create AST node
        ast_node = PlaywrightAST(
            action_type=action_type,
            selector=selector,
            value=value,
            url=url,
            description=intent,
            element_html=element_html  # Pass element HTML for accessibility-based selectors
        )
        
        return ast_node
    
    def _is_intent_safe_for_ast(self, intent_obj: Dict) -> bool:
        """
        RULE 4: Re-check intent safety before AST generation
        Verify all required fields are present and valid
        """
        if not intent_obj:
            return False
        
        # Check required fields
        intent = intent_obj.get("intent", "").strip()
        event_type = intent_obj.get("event_type", "").strip()
        selector = intent_obj.get("selector")
        
        # Intent must not be empty
        if not intent:
            return False
        
        # Event type must not be empty
        if not event_type:
            return False
        
        # If selector is needed, validate it
        if selector and isinstance(selector, str):
            if not selector.strip():  # Empty selector string
                return False
            if not self.validator._is_valid_css_selector(selector):
                return False
        
        return True
        

    
    def _determine_action_type(self, intent: str, event_type: str) -> PlaywrightActionType:
        """
        Determine Playwright action type from intent and event.
        Prioritizes semantic 'Action:' field if present.
        """
        
        intent_lower = intent.lower()
        event_lower = event_type.lower()
        
        # Priority 1: Extract from semantic "Action: [type]" field
        action_match = re.search(r"action:\s*(\w+)", intent_lower)
        if action_match:
            action_val = action_match.group(1)
            action_map = {
                "click": PlaywrightActionType.CLICK,
                "type": PlaywrightActionType.FILL_TEXT,
                "fill": PlaywrightActionType.FILL_TEXT,
                "select": PlaywrightActionType.SELECT,
                "navigate": PlaywrightActionType.NAVIGATE,
                "wait": PlaywrightActionType.WAIT,
                "scroll": PlaywrightActionType.SCROLL,
                "hover": PlaywrightActionType.HOVER,
                "submit": PlaywrightActionType.CLICK, # submit usually results in click
            }
            if action_val in action_map:
                return action_map[action_val]

        # Priority 2: Fallback Pattern matching logic
        if "navigate" in intent_lower or "tab_visible" in event_lower or "go to" in intent_lower:
            return PlaywrightActionType.NAVIGATE
        elif "click" in intent_lower or "click_event" in event_lower:
            return PlaywrightActionType.CLICK
        elif "type" in intent_lower or "fill" in intent_lower or "input" in intent_lower:
            return PlaywrightActionType.FILL_TEXT
        elif "select" in intent_lower or "choose" in intent_lower:
            return PlaywrightActionType.SELECT
        elif "wait" in intent_lower:
            return PlaywrightActionType.WAIT
        elif "scroll" in intent_lower:
            return PlaywrightActionType.SCROLL
        elif "hover" in intent_lower:
            return PlaywrightActionType.HOVER
        elif "press" in intent_lower:
            return PlaywrightActionType.PRESS
        else:
            return PlaywrightActionType.CLICK  # Default fallback
    
    def _extract_selector(self, step: Dict) -> Optional[str]:
        """Extract selector from step element HTML - prioritizes ID and class names"""
        element_html = step.get("eventElement", "")
        
        if not element_html:
            return None
        
        # Try to extract id first (most specific)
        if 'id="' in element_html:
            try:
                start = element_html.find('id="') + 4
                end = element_html.find('"', start)
                element_id = element_html[start:end]
                if element_id and element_id.strip():
                    # Store both selector and indicate it's an ID for potential deduplication
                    return f"#{element_id}"
            except:
                pass
        
        # Try to extract class (second priority)
        if 'class="' in element_html:
            try:
                start = element_html.find('class="') + 7
                end = element_html.find('"', start)
                classes = element_html[start:end]
                if classes and classes.strip():
                    # Use first class only
                    first_class = classes.split()[0]
                    if first_class:
                        return f".{first_class}"
            except:
                pass
        
        # Try to extract placeholder attribute (for input fields)
        if 'placeholder="' in element_html:
            try:
                start = element_html.find('placeholder="') + 13
                end = element_html.find('"', start)
                placeholder = element_html[start:end]
                if placeholder and placeholder.strip():
                    return f'[placeholder="{placeholder}"]'
            except:
                pass
        
        # Try to extract name attribute (for form elements)
        if 'name="' in element_html:
            try:
                start = element_html.find('name="') + 6
                end = element_html.find('"', start)
                name = element_html[start:end]
                if name and name.strip():
                    tag_end = element_html.find(" ")
                    if tag_end == -1:
                        tag_end = element_html.find(">")
                    tag = element_html[1:tag_end].strip()
                    return f'{tag}[name="{name}"]'
            except:
                pass
        
        # Extract element type as fallback
        try:
            tag_end = element_html.find(" ")
            if tag_end == -1:
                tag_end = element_html.find(">")
            tag = element_html[1:tag_end].strip()
            return tag if tag else "div"
        except:
            return None
    
    def convert_all_intents_to_ast(self, intents: List[Dict]) -> List[PlaywrightAST]:
        """
        Convert all intents to AST nodes
        RULE 4 & 11: Only create AST for intents that passed all safety checks
        """
        print(f"Converting {len(intents)} validated intents to AST...")
        self.ast_nodes = []
        self.conversion_errors = []
        self.conversion_warnings = []
        
        skipped_count = 0
        
        for idx, intent_obj in enumerate(intents):
            try:
                ast_node = self.convert_intent_to_ast(intent_obj, intent_obj.get("original_step", {}))
                
                if ast_node is None:
                    skipped_count += 1
                    continue
                
                self.ast_nodes.append(ast_node)
                
            except Exception as e:
                self.conversion_errors.append(
                    f"Step {intent_obj.get('step_index')}: Unexpected error: {e}"
                )
                skipped_count += 1
        
        print(f"[OK] Converted to {len(self.ast_nodes)} valid AST nodes")
        if skipped_count > 0:
            print(f"[WARN] Skipped {skipped_count} steps that failed safety checks")
        
        # Print any errors
        if self.conversion_errors:
            print(f"\nConversion Errors ({len(self.conversion_errors)} found):")
            for error in self.conversion_errors[:5]:
                print(f"  - {error}")
            if len(self.conversion_errors) > 5:
                print(f"  ... and {len(self.conversion_errors) - 5} more")
        
        if self.conversion_warnings:
            print(f"\nConversion Warnings ({len(self.conversion_warnings)} found):")
            for warning in self.conversion_warnings[:5]:
                print(f"  - {warning}")
            if len(self.conversion_warnings) > 5:
                print(f"  ... and {len(self.conversion_warnings) - 5} more")
        
        return self.ast_nodes
    
    def save_ast(self, filepath: str = "ast_nodes.json"):
        """Save AST nodes to JSON"""
        ast_dicts = [node.to_dict() for node in self.ast_nodes]
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(ast_dicts, f, indent=2)
        print(f"AST nodes saved to {filepath}")


if __name__ == "__main__":
    converter = ASTConverter()
    
    with open("intents.json", 'r') as f:
        intents = json.load(f)
    
    ast_nodes = converter.convert_all_intents_to_ast(intents)
    converter.save_ast()
    print(f"Created {len(ast_nodes)} AST nodes")
