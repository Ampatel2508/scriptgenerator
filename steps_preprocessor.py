#!/usr/bin/env python3
"""
Steps Preprocessor - Filters and normalizes browser events before LLM intent generation.

This module implements a preprocessing layer that:
1. Classifies events into Context (non-interactive) and Action (interactive) events
2. Drops or marks context events as non-executable
3. Normalizes action events into semantic representations safe for LLM
4. Strips raw selectors, absolute xpaths, tracking params, and metadata
5. Extracts human-visible identifiers (text, labels, placeholders)

This ensures clean, semantic steps that prevent selector conflicts and LLM hallucination.
"""

import json
import re
from typing import Dict, List, Optional, Tuple
from enum import Enum
import urllib.parse


class EventCategory(Enum):
    """Classification of browser events"""
    CONTEXT = "context"  # Non-executable (page visibility, navigation)
    ACTION = "action"    # Executable (click, type, select, hover)


class NormalizedAction(Enum):
    """Normalized action types"""
    CLICK = "click"
    TYPE = "type"
    SELECT = "select"
    SUBMIT = "submit"
    HOVER = "hover"
    NAVIGATE = "navigate"


class ElementRole(Enum):
    """Semantic element roles"""
    BUTTON = "button"
    TEXTBOX = "textbox"
    LINK = "link"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    DROPDOWN = "dropdown"
    TEXTAREA = "textarea"
    IMAGE = "image"
    OTHER = "other"


class StepsPreprocessor:
    """
    Preprocesses raw browser event steps into clean semantic representations.
    
    Workflow:
    1. Load raw steps.json
    2. Classify each event (context vs action)
    3. Filter/mark context events
    4. Normalize action events
    5. Output clean semantic steps
    """
    
    # Event types that are context events (non-executable)
    CONTEXT_EVENT_TYPES = {
        "STEPS_FEATURE_TAB_VISIBLE_EVENT",
        "STEPS_FEATURE_TAB_ACTIVATED_EVENT",
        "STEPS_FEATURE_NAVIGATE_EVENT",  # Navigation is context, not an interaction
        "STEPS_FEATURE_PAGE_LOAD_EVENT",
        "STEPS_FEATURE_PAGE_VISIBLE_EVENT",
        "STEPS_FEATURE_URL_CHANGED_EVENT",
        "STEPS_FEATURE_WINDOW_FOCUS_EVENT",
        "STEPS_FEATURE_WINDOW_BLUR_EVENT",
    }
    
    # Event types that are action events (executable)
    ACTION_EVENT_TYPES = {
        "STEPS_FEATURE_CLICK_EVENT",
        "STEPS_FEATURE_TYPE_EVENT",
        "STEPS_FEATURE_CHANGE_EVENT",
        "STEPS_FEATURE_SELECT_EVENT",
        "STEPS_FEATURE_SUBMIT_EVENT",
        "STEPS_FEATURE_HOVER_EVENT",
        "STEPS_FEATURE_FOCUS_EVENT",
        "STEPS_FEATURE_BLUR_EVENT",
        "STEPS_FEATURE_KEY_DOWN_EVENT",
        "STEPS_FEATURE_KEY_UP_EVENT",
    }
    
    def __init__(self):
        self.raw_steps = []
        self.preprocessed_steps = []
        self.context_events = []
        self.filtered_count = 0
        self.action_count = 0
        self.statistics = {}
    
    def load_steps(self, steps_file: str = "steps.json") -> List[Dict]:
        """Load raw steps from JSON file"""
        try:
            with open(steps_file, 'r', encoding='utf-8') as f:
                self.raw_steps = json.load(f)
            print(f"[OK] Loaded {len(self.raw_steps)} raw steps from {steps_file}")
            return self.raw_steps
        except FileNotFoundError:
            print(f"[ERROR] Steps file not found: {steps_file}")
            return []
    
    def preprocess(self, steps: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Main preprocessing pipeline - INCLUDES BOTH ACTION AND CONTEXT EVENTS
        
        Returns:
            List of all semantic steps (action + context) ready for code generation
        """
        if steps is not None:
            self.raw_steps = steps
        
        if not self.raw_steps:
            print("[WARN] No steps to preprocess")
            return []
        
        print("\n" + "="*70)
        print("PREPROCESSING STEPS: CLASSIFICATION & NORMALIZATION")
        print("="*70)
        
        self.preprocessed_steps = []
        self.context_events = []
        self.filtered_count = 0
        self.action_count = 0
        
        for idx, step in enumerate(self.raw_steps):
            # Classify event
            category, event_type = self._classify_event(step)
            
            if category == EventCategory.CONTEXT:
                # Include context events as waits/navigation steps (NOT executable actions)
                context_step = self._normalize_context_event(step, event_type, idx)
                if context_step:
                    self.preprocessed_steps.append(context_step)
                    self.context_events.append(context_step)
                    # Don't increment action_count for context events
                    self.filtered_count += 1
            
            elif category == EventCategory.ACTION:
                # Normalize action event
                normalized_step = self._normalize_action_event(step, idx)
                if normalized_step:
                    self.preprocessed_steps.append(normalized_step)
                    self.action_count += 1
        
        # Print statistics
        self._print_statistics()
        
        return self.preprocessed_steps
    
    def _classify_event(self, step: Dict) -> Tuple[EventCategory, str]:
        """Classify event as context or action"""
        event_type = step.get("eventType", "").strip()
        
        if event_type in self.CONTEXT_EVENT_TYPES:
            return EventCategory.CONTEXT, event_type
        elif event_type in self.ACTION_EVENT_TYPES:
            return EventCategory.ACTION, event_type
        else:
            # Default: treat as action if it has actionable content
            if step.get("eventElement") or step.get("eventData"):
                return EventCategory.ACTION, event_type
            return EventCategory.CONTEXT, event_type
    
    def _extract_context_info(self, step: Dict, event_type: str) -> Dict:
        """Extract high-level context from context events"""
        context_map = {
            "STEPS_FEATURE_TAB_VISIBLE_EVENT": "tab_visible",
            "STEPS_FEATURE_TAB_ACTIVATED_EVENT": "tab_activated",
            "STEPS_FEATURE_NAVIGATE_EVENT": "navigation",
            "STEPS_FEATURE_PAGE_LOAD_EVENT": "page_loaded",
            "STEPS_FEATURE_PAGE_VISIBLE_EVENT": "page_visible",
            "STEPS_FEATURE_URL_CHANGED_EVENT": "url_changed",
        }
        
        context_type = context_map.get(event_type, "other")
        
        return {
            "type": "context",
            "context_type": context_type,
            "url": step.get("url", ""),
            "event_type": event_type,
            "timestamp": step.get("timestamp", ""),
            "note": f"Non-executable context event: {context_type}"
        }
    
    def _normalize_context_event(self, step: Dict, event_type: str, idx: int) -> Optional[Dict]:
        """
        Normalize a context event (non-action) to include in the pipeline.
        
        Context events include: TAB_VISIBLE, PAGE_LOAD, NAVIGATE, URL_CHANGED, WINDOW_FOCUS/BLUR
        These generate wait steps and navigation checks in the final code.
        """
        context_map = {
            "STEPS_FEATURE_TAB_VISIBLE_EVENT": ("wait", "Tab visibility check"),
            "STEPS_FEATURE_TAB_ACTIVATED_EVENT": ("wait", "Tab activation"),
            "STEPS_FEATURE_NAVIGATE_EVENT": ("navigate", "Page navigation"),
            "STEPS_FEATURE_PAGE_LOAD_EVENT": ("wait", "Page load complete"),
            "STEPS_FEATURE_PAGE_VISIBLE_EVENT": ("wait", "Page visibility check"),
            "STEPS_FEATURE_URL_CHANGED_EVENT": ("wait", "URL changed - wait for navigation"),
            "STEPS_FEATURE_WINDOW_FOCUS_EVENT": ("wait", "Window focused"),
            "STEPS_FEATURE_WINDOW_BLUR_EVENT": ("wait", "Window blurred"),
        }
        
        action_desc = context_map.get(event_type, ("wait", "Context event"))
        action, description = action_desc
        
        url = step.get("url", "")
        
        normalized_step = {
            "step_index": idx,
            "normalized_action": action,  # "wait" or "navigate"
            "element_role": "context_event",  # Special role for context events
            "human_identifier": description,  # Human-readable description
            "visibility": "context",  # Not a UI element
            "interactable": False,  # Not an interactive element
            
            # Context event hints
            "element_hints": {
                "id": "",
                "class": "",
                "name": "",
                "test_id": "",
                "aria_label": "",
                "tag": "context",
            },
            
            "value": "",
            "clean_url": self._strip_tracking_params(url),
            "original_event_type": event_type,
            "original_step_id": step.get("stepId", f"context_{idx}"),
            
            # Mark as context event
            "is_context_event": True,
            "context_type": event_type,
        }
        
        return normalized_step
    
    def _normalize_action_event(self, step: Dict, idx: int) -> Optional[Dict]:

        """
        Normalize an action event into semantic representation.
        
        Returns semantic action with:
        - normalized_action: click, type, select, submit
        - element_role: button, textbox, link, etc.
        - human_identifier: visible text, label, placeholder
        - visibility_state: visible, hidden, etc.
        - id, class, name as SECONDARY hints only
        - NO raw selectors, xpaths, DOM-depth CSS, tracking params, etc.
        """
        
        event_type = step.get("eventType", "")
        event_element = step.get("eventElement", "")
        event_data = step.get("eventData", "")
        url = step.get("url", "")
        
        # Step 1: Determine normalized action
        action = self._determine_normalized_action(event_type, event_element, event_data)
        if not action:
            return None
        
        # Step 2: Extract element information
        element_info = self._extract_element_info(event_element)
        
        # Step 3: Extract human-visible identifiers
        human_identifier = self._extract_human_identifier(event_element, event_data, element_info)
        
        # Step 4: Determine element role
        element_role = self._determine_element_role(event_element, element_info)
        
        # Step 5: Build normalized step (NO raw selectors, NO tracking params)
        normalized_step = {
            "step_index": idx,
            "normalized_action": action.value,
            "element_role": element_role.value,
            "human_identifier": human_identifier,
            "visibility": "visible",  # Assume visible if being interacted with
            "interactable": True,
            
            # Secondary hints ONLY - NOT FOR SELECTION
            "element_hints": {
                "id": element_info.get("id", ""),
                "class": element_info.get("class", ""),
                "name": element_info.get("name", ""),
                "test_id": element_info.get("test_id", ""),
                "aria_label": element_info.get("aria_label", ""),
                "tag": element_info.get("tag", ""),
            },
            
            # Value for type/select actions
            "value": event_data if action in [NormalizedAction.TYPE, NormalizedAction.SELECT] else "",
            
            # Clean URL (stripped of tracking params)
            "clean_url": self._strip_tracking_params(url),
            
            # Original event type for reference
            "original_event_type": event_type,
            
            # Reference to original step (for debugging only)
            "original_step_id": step.get("id", ""),
        }
        
        return normalized_step
    
    def _determine_normalized_action(
        self, event_type: str, event_element: str, event_data: str
    ) -> Optional[NormalizedAction]:
        """Determine normalized action from event type and content"""
        
        event_lower = event_type.lower()
        
        if "click" in event_lower:
            # Check element type to determine actual action
            if "<input" in event_element.lower() and 'type="text"' in event_element:
                return NormalizedAction.CLICK  # Clicking on textbox
            elif "<select" in event_element.lower():
                return NormalizedAction.SELECT
            elif "<a " in event_element.lower():
                return NormalizedAction.CLICK  # Link click
            elif "<button" in event_element.lower():
                return NormalizedAction.CLICK
            return NormalizedAction.CLICK
        
        elif "type" in event_lower or "keyboard" in event_lower or "key_" in event_lower:
            return NormalizedAction.TYPE
        
        elif "change" in event_lower or "select" in event_lower:
            return NormalizedAction.SELECT
        
        elif "submit" in event_lower:
            return NormalizedAction.SUBMIT
        
        elif "hover" in event_lower or "mouseover" in event_lower:
            return NormalizedAction.HOVER
        
        elif "focus" in event_lower and "text" in event_element.lower():
            return NormalizedAction.CLICK  # Focus on textbox = click
        
        return None
    
    def _extract_element_info(self, element_html: str) -> Dict:
        """Extract element attributes from HTML"""
        info = {
            "id": "",
            "class": "",
            "name": "",
            "test_id": "",
            "aria_label": "",
            "tag": "",
            "placeholder": "",
            "value": "",
        }
        
        if not element_html:
            return info
        
        # Extract tag
        tag_match = re.search(r'^<(\w+)', element_html)
        if tag_match:
            info["tag"] = tag_match.group(1).lower()
        
        # Extract id
        id_match = re.search(r'id=["\']([^"\']+)["\']', element_html)
        if id_match:
            info["id"] = id_match.group(1)
        
        # Extract class
        class_match = re.search(r'class=["\']([^"\']+)["\']', element_html)
        if class_match:
            info["class"] = class_match.group(1)
        
        # Extract name
        name_match = re.search(r'name=["\']([^"\']+)["\']', element_html)
        if name_match:
            info["name"] = name_match.group(1)
        
        # Extract data-testid
        testid_match = re.search(r'data-testid=["\']([^"\']+)["\']', element_html)
        if testid_match:
            info["test_id"] = testid_match.group(1)
        
        # Extract aria-label
        aria_match = re.search(r'aria-label=["\']([^"\']+)["\']', element_html)
        if aria_match:
            info["aria_label"] = aria_match.group(1)
        
        # Extract placeholder
        placeholder_match = re.search(r'placeholder=["\']([^"\']+)["\']', element_html)
        if placeholder_match:
            info["placeholder"] = placeholder_match.group(1)
        
        # Extract value
        value_match = re.search(r'value=["\']([^"\']+)["\']', element_html)
        if value_match:
            info["value"] = value_match.group(1)
        
        return info
    
    def _extract_human_identifier(
        self, element_html: str, event_data: str, element_info: Dict
    ) -> str:
        """
        Extract human-visible identifier for the element.
        Priority: visible text > label > placeholder > aria-label > name
        """
        
        # Priority 1: Visible text from event_data
        if event_data and event_data.strip():
            text_clean = event_data.strip()[:100]  # First 100 chars
            if len(text_clean) > 0:
                return text_clean
        
        # Priority 2: Inner text from element HTML
        inner_text_match = re.search(r'>([^<]+)</', element_html)
        if inner_text_match:
            text = inner_text_match.group(1).strip()
            if text:
                return text[:100]
        
        # Priority 3: Placeholder
        if element_info.get("placeholder"):
            return f"[Input: {element_info['placeholder']}]"
        
        # Priority 4: Aria-label
        if element_info.get("aria_label"):
            return f"[{element_info['aria_label']}]"
        
        # Priority 5: Label from associated label element (if available)
        if element_info.get("id"):
            return f"[Element with ID: {element_info['id']}]"
        
        # Priority 6: Name
        if element_info.get("name"):
            return f"[Named: {element_info['name']}]"
        
        # Fallback
        return f"[{element_info.get('tag', 'element')}]"
    
    def _determine_element_role(self, element_html: str, element_info: Dict) -> ElementRole:
        """Determine the semantic role of the element"""
        
        tag = element_info.get("tag", "").lower()
        html_lower = element_html.lower()
        
        if tag == "button":
            return ElementRole.BUTTON
        
        elif tag == "a":
            return ElementRole.LINK
        
        elif tag == "input":
            input_type = re.search(r'type=["\']([^"\']+)["\']', element_html)
            if input_type:
                type_val = input_type.group(1).lower()
                if type_val == "checkbox":
                    return ElementRole.CHECKBOX
                elif type_val == "radio":
                    return ElementRole.RADIO
                elif type_val == "text":
                    return ElementRole.TEXTBOX
                elif type_val == "submit":
                    return ElementRole.BUTTON
            return ElementRole.TEXTBOX
        
        elif tag == "textarea":
            return ElementRole.TEXTAREA
        
        elif tag == "select":
            return ElementRole.DROPDOWN
        
        elif tag == "img":
            return ElementRole.IMAGE
        
        elif "button" in html_lower:
            return ElementRole.BUTTON
        
        return ElementRole.OTHER
    
    def _strip_tracking_params(self, url: str) -> str:
        """
        Remove tracking and advertising parameters from URL.
        Strips: utm_*, gad*, ref=tracking, etc.
        """
        if not url:
            return ""
        
        try:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            
            # Remove tracking parameters
            tracking_patterns = [
                'utm_', 'gad', 'ref=', 'adgrp', 'hvp', 'hvt', 'hvr',
                'tag=', 'crid=', 'sprefix=', 'rps=', 'lpg='
            ]
            
            filtered_params = {}
            for key, value in params.items():
                # Keep only if not a tracking parameter
                if not any(key.startswith(t) for t in tracking_patterns):
                    filtered_params[key] = value
            
            # Reconstruct URL with only essential params
            new_query = urllib.parse.urlencode(filtered_params, doseq=True)
            clean_url = urllib.parse.urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment
            ))
            
            return clean_url
        except Exception:
            return url
    
    def _print_statistics(self):
        """Print preprocessing statistics"""
        total = self.action_count + self.filtered_count
        
        print(f"\n[PREPROCESSING RESULTS]")
        print(f"  Total events: {total}")
        print(f"  [OK] Action events (processed): {self.action_count}")
        print(f"  [OK] Context events (included as waits): {self.filtered_count}")
        print(f"  Total steps in pipeline: {len(self.preprocessed_steps)}")
        
        if self.preprocessed_steps:
            action_types = {}
            context_types = {}
            for step in self.preprocessed_steps:
                action = step.get("normalized_action", "unknown")
                action_types[action] = action_types.get(action, 0) + 1
            
            print(f"\n  Action breakdown:")
            for action, count in sorted(action_types.items()):
                print(f"    - {action}: {count}")
    
    def save_preprocessed_steps(self, filepath: str = "steps_preprocessed.json") -> bool:
        """Save preprocessed steps to JSON file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.preprocessed_steps, f, indent=2, ensure_ascii=False)
            print(f"\n[OK] Preprocessed steps saved to {filepath}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save preprocessed steps: {e}")
            return False
    
    def save_context_events(self, filepath: str = "steps_context_events.json") -> bool:
        """Save filtered context events for reference"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.context_events, f, indent=2, ensure_ascii=False)
            print(f"[OK] Context events (for reference) saved to {filepath}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save context events: {e}")
            return False


def main():
    """Run preprocessing pipeline"""
    preprocessor = StepsPreprocessor()
    
    # Load raw steps
    steps = preprocessor.load_steps("steps.json")
    
    # Preprocess
    preprocessed = preprocessor.preprocess(steps)
    
    # Save outputs
    preprocessor.save_preprocessed_steps("steps_preprocessed.json")
    preprocessor.save_context_events("steps_context_events.json")
    
    print(f"\n[OK] Preprocessing complete!")
    print(f"  Input: steps.json ({len(steps)} raw events)")
    print(f"  Output: steps_preprocessed.json ({len(preprocessed)} action events)")
    
    return preprocessed


if __name__ == "__main__":
    main()
