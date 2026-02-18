import json
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

# Import Google Gemini directly (avoid LangChain wrapper issues)
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

# Import validator
from intent_validator import IntentValidator

load_dotenv()

class IntentGenerator:
    """Generates intents from step events using Google Gemini"""
    
    def __init__(self, use_gemini: bool = True):
        self.use_gemini = use_gemini
        self.llm = self._initialize_llm()
        self.intents = []
        self.validator = IntentValidator()  # Add validator for rules 1-3
        
    def _initialize_llm(self):
        """Initialize LLM - use Google Gemini directly"""
        if self.use_gemini and HAS_GEMINI:
            try:
                gemini_key = os.getenv("GEMINI_API_KEY")
                gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
                
                if not gemini_key:
                    print("[WARN] GEMINI_API_KEY not found, using fallback (rule-based)")
                    return None
                
                genai.configure(api_key=gemini_key)
                print(f"[OK] Google Gemini configured ({gemini_model})")
                return genai.GenerativeModel(gemini_model)
            except Exception as e:
                print(f"[WARN] Gemini initialization failed: {e}")
                print("Using fallback (rule-based)")
                return None
        else:
            print("Using fallback (rule-based intent generation)")
            return None
    
    def generate_intent_for_step(self, step: Dict, step_index: int) -> Dict:
        """Generate intent for a single step (works with preprocessed semantic steps)"""
        
        # Check if step is preprocessed (has normalized_action)
        if "normalized_action" in step:
            # This is a preprocessed semantic step
            return self._generate_intent_from_preprocessed(step)
        
        # Otherwise, use legacy fallback (for raw steps)
        event_type = step.get("eventType", "UNKNOWN")
        url = step.get("url", "")
        element = step.get("eventElement", "")
        event_data = step.get("eventData", "")
        
        # If LLM is not available, use fallback
        if self.llm is None:
            intent = self._generate_fallback_intent(step)
        else:
            try:
                prompt = f"""Analyze this user action step and provide a clear intent:
                Rules:
- NEVER output empty selectors
- NEVER output malformed CSS selectors
- If selector is empty or invalid → SKIP the step
- Remove duplicate consecutive actions
- Prefer stable selectors (id, name, data-testid)


Event Type: {event_type}
URL: {url}
Element: {element[:200]}
Data: {event_data[:200]}

Provide a concise intent description that describes what this step accomplishes.
Keep it to one sentence. Only return the intent, nothing else."""
                
                response = self.llm.generate_content(prompt)
                intent = response.text.strip()
            except Exception as e:
                print(f"Error generating intent for step {step_index}: {e}")
                intent = self._generate_fallback_intent(step)
        
        return {
            "step_index": step_index,
            "event_type": event_type,
            "intent": intent,
            "original_step": step
        }
    
    def _generate_intent_from_preprocessed(self, step: Dict) -> Dict:
        """
        Generate intent from preprocessed semantic step.
        Uses normalized_action, element_role, and human_identifier.
        """
        step_index = step.get("step_index", 0)
        action = step.get("normalized_action", "unknown")
        role = step.get("element_role", "element")
        identifier = step.get("human_identifier", "element")
        value = step.get("value", "")
        
        # Build intent from semantic representation
        intent_template = {
            "click": f"Click on {role}: {identifier}",
            "type": f"Type '{value}' in {role}: {identifier}",
            "select": f"Select '{value}' from {role}: {identifier}",
            "submit": f"Submit {role}: {identifier}",
            "hover": f"Hover over {role}: {identifier}",
            "navigate": f"Navigate to {identifier}",
        }
        
        intent = intent_template.get(action, f"Perform {action} on {identifier}")
        
        return {
            "step_index": step_index,
            "event_type": step.get("original_event_type", "PREPROCESSED"),
            "intent": intent,
            "action": action,
            "element_role": role,
            "human_identifier": identifier,
            "value": value,
            # Use element hints as selectors (these are semantic, safe hints)
            "selector": self._build_selector_from_hints(step.get("element_hints", {})),
            "original_step": step  # Full preprocessed step for reference
        }
    
    def _build_selector_from_hints(self, hints: Dict) -> str:
        """Build a selector from element hints (secondary information)"""
        # Priority: id > name > class > test_id
        if hints.get("id"):
            return f"#{hints['id']}"
        if hints.get("name"):
            return f"[name='{hints['name']}']"
        if hints.get("class"):
            # Take first class only
            classes = hints["class"].split()
            if classes:
                return f".{classes[0]}"
        if hints.get("test_id"):
            return f"[data-testid='{hints['test_id']}']"
        if hints.get("aria_label"):
            return f"[aria-label='{hints['aria_label']}']"
        return ""
    
    def _generate_fallback_intent(self, step: Dict) -> str:
        """Generate fallback intent based on event type (no LLM)"""
        event_type = step.get("eventType", "")
        event_data = step.get("eventData", "")
        
        intent_map = {
            "STEPS_FEATURE_TAB_VISIBLE_EVENT": "Navigate to page and wait for page to load",
            "STEPS_FEATURE_CLICK_EVENT": f"Click on element to interact",
            "STEPS_FEATURE_NAVIGATE_EVENT": f"Navigate to URL: {step.get('url', '')}",
            "STEPS_FEATURE_TYPE_EVENT": f"Type text: {event_data[:50]}",
            "STEPS_FEATURE_SCROLL_EVENT": "Scroll page to view more content",
            "STEPS_FEATURE_WAIT_EVENT": "Wait for element to appear",
        }
        
        return intent_map.get(event_type, f"Perform action: {event_type}")
    
    def generate_intents_for_all_steps(self, steps: List[Dict]) -> List[Dict]:
        """Generate intents for all steps - check if preprocessed first"""
        self.intents = []
        
        # Check if steps are preprocessed
        if steps and "normalized_action" in steps[0]:
            print(f"[OK] Generating intents from {len(steps)} preprocessed semantic steps...")
            return self._generate_intents_from_preprocessed_steps(steps)
        
        # Otherwise handle as raw steps with LLM or fallback
        if self.llm:
            print(f"[OK] Generating intents for {len(steps)} steps using Google Gemini...")
            return self._generate_intents_with_llm(steps)
        else:
            print(f"[WARN] Generating intents for {len(steps)} steps using fallback (rule-based)...")
            return self._generate_intents_fallback(steps)
    
    def _generate_intents_with_llm(self, steps: List[Dict]) -> List[Dict]:
        """Generate intents using Gemini LLM with strict validation"""
        self.intents = []
        raw_intents = []
        
        for idx, step in enumerate(steps):
            if idx % 10 == 0:
                print(f"  Processing step {idx}/{len(steps)}")
            
            try:
                event_type = step.get("eventType", "UNKNOWN")
                url = step.get("url", "")
                element = step.get("eventElement", "")[:100]
                event_data = step.get("eventData", "")[:50]
                
                # RULE 2: Strict LLM prompt with non-negotiable rules
                prompt = f"""Analyze this user action step and generate a STRICT intent.

MANDATORY RULES - VIOLATION OF ANY RULE = FAILED OUTPUT:
1. Output ONLY JSON intent, no additional text or explanation
2. Return a concise one-sentence intent description ONLY
3. FORBID empty selectors in any case
4. FORBID malformed CSS selectors
5. FORBID duplicate consecutive actions - identify and remove
6. PREFER STABLE selectors: element IDs, data-testid, name attributes
7. REJECT brittle selectors: random class names, nested paths
8. If insufficient info to generate safe selector → SKIP THIS STEP (return empty string for intent)
9. Never output JavaScript code or implementation details
10. Focus only on WHAT action to perform and on WHICH element

Event Type: {event_type}
URL: {url}
Element HTML: {element}
Event Data: {event_data}

Return ONLY the intent description in a single line. If cannot safely generate → return "SKIP".
"""
                
                response = self.llm.generate_content(prompt)
                intent = response.text.strip()
                
                # RULE 3: Filter out obviously bad responses
                if not intent or intent.upper() == "SKIP" or len(intent) == 0:
                    # Mark for removal in validation
                    intent = ""
                
            except Exception as e:
                print(f"  [WARN] Gemini error at step {idx}: {e}, using fallback")
                intent = self._generate_fallback_intent(step)
            
            intent_obj = {
                "step_index": idx,
                "event_type": step.get("eventType", "UNKNOWN"),
                "intent": intent,
                "original_step": step
            }
            raw_intents.append(intent_obj)
        
        # RULE 3: Validate and clean intents after LLM generation
        print(f"\n[OK] Generated {len(raw_intents)} raw intents")
        print("  Now validating and cleaning intents...")
        self.intents, validation_report = self.validator.validate_and_clean_intents(raw_intents)
        
        # Print validation report
        self.validator.print_validation_report(validation_report)
        
        print(f"[OK] After validation: {len(self.intents)} valid intents")
        return self.intents
    
    def _generate_intents_from_preprocessed_steps(self, steps: List[Dict]) -> List[Dict]:
        """Generate intents directly from preprocessed semantic steps"""
        raw_intents = []
        
        for idx, step in enumerate(steps):
            intent_obj = self._generate_intent_from_preprocessed(step)
            raw_intents.append(intent_obj)
        
        # RULE 3: Validate and clean intents after generation
        print(f"\n[OK] Generated {len(raw_intents)} raw intents from preprocessed steps")
        print("  Now validating and cleaning intents...")
        self.intents, validation_report = self.validator.validate_and_clean_intents(raw_intents)
        
        # Print validation report
        self.validator.print_validation_report(validation_report)
        
        print(f"[OK] After validation: {len(self.intents)} valid intents")
        return self.intents
    
    def _generate_intents_fallback(self, steps: List[Dict]) -> List[Dict]:
        """Generate intents using fallback rule-based approach with validation"""
        raw_intents = []
        
        for idx, step in enumerate(steps):
            if idx % 20 == 0:
                print(f"  Processing step {idx}/{len(steps)}")
            
            intent_text = self._generate_fallback_intent(step)
            
            intent_obj = {
                "step_index": idx,
                "event_type": step.get("eventType", "UNKNOWN"),
                "intent": intent_text,
                "original_step": step
            }
            raw_intents.append(intent_obj)
        
        print(f"\n[OK] Generated {len(raw_intents)} raw intents (fallback)")
        print("  Now validating and cleaning intents...")
        
        # RULE 3: Validate and clean intents
        self.intents, validation_report = self.validator.validate_and_clean_intents(raw_intents)
        self.validator.print_validation_report(validation_report)
        
        print(f"[OK] After validation: {len(self.intents)} valid intents")
        return self.intents
    
    def save_intents(self, filepath: str = "intents.json"):
        """Save intents to JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.intents, f, indent=2, ensure_ascii=False)
        print(f"Intents saved to {filepath}")
    
    def get_intents_formatted(self) -> str:
        """Get all intents as formatted string"""
        result = "Step Intents:\n\n"
        for intent_obj in self.intents:
            result += f"Step {intent_obj['step_index']}: {intent_obj['intent']}\n"
        return result


if __name__ == "__main__":
    generator = IntentGenerator()
    
    with open("steps.json", 'r') as f:
        steps = json.load(f)
    
    intents = generator.generate_intents_for_all_steps(steps)
    generator.save_intents()
    print(generator.get_intents_formatted())
