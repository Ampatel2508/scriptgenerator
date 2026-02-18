"""
Intent Validator - Enforces strict safety rules on LLM-generated intents
Implements rules 1-4 and 9: intent contract, validation, deduplication, and safety gates
"""

import json
import re
from typing import List, Dict, Tuple, Optional


class IntentValidator:
    """
    Validates intents to ensure they meet strict safety criteria:
    - No empty selectors
    - No malformed CSS selectors
    - No duplicate consecutive actions
    - All required fields present
    - Selectors are stable (prefer ID, attributes over classes)
    """

    def __init__(self):
        self.validation_errors = []
        self.validation_warnings = []

    def validate_single_intent(self, intent_obj: Dict, step_index: int) -> Tuple[bool, Optional[Dict]]:
        """
        Validate a single intent object
        Returns (is_valid, cleaned_intent_obj)
        Handles both action intents and context events
        """
        self.validation_errors = []
        self.validation_warnings = []

        # Check for required fields
        if not intent_obj:
            self.validation_errors.append(f"Step {step_index}: Intent is None or empty")
            return False, None

        intent = intent_obj.get("intent", "")
        event_type = intent_obj.get("event_type", "")
        original_step = intent_obj.get("original_step", {})

        # Check if this is a context event (non-executable)
        is_context_event = original_step.get("is_context_event", False)
        normalized_action = original_step.get("normalized_action", "")
        
        # Context events are always valid (they generate waits, not actions)
        if is_context_event or normalized_action == "wait":
            cleaned_intent = {
                "step_index": step_index,
                "event_type": event_type,
                "intent": intent.strip() or "Wait for context event",
                "selector": "",  # Context events don't need selectors
                "original_step": original_step,
                "is_context_event": True,
            }
            return True, cleaned_intent

        # Validate intent text is not empty for action events
        if not intent or not intent.strip():
            self.validation_errors.append(f"Step {step_index}: Intent text is empty")
            return False, None

        # For preprocessed steps, selector is already built and provided
        selector = intent_obj.get("selector", "")
        
        # If no selector in intent_obj, try to extract from original step
        if not selector:
            selector = self._extract_stable_selector(original_step)

        # Check if selector is required for this action type
        if self._action_requires_selector(event_type):
            if not selector or selector.strip() == "":
                self.validation_warnings.append(
                    f"Step {step_index}: Empty selector for {event_type}. Skipping step."
                )
                return False, None

            # Validate selector syntax
            if not self._is_valid_css_selector(selector):
                self.validation_errors.append(
                    f"Step {step_index}: Malformed CSS selector '{selector}'"
                )
                return False, None

        # Create cleaned intent object
        cleaned_intent = {
            "step_index": step_index,
            "event_type": event_type,
            "intent": intent.strip(),
            "selector": selector,
            "original_step": original_step,
            "is_context_event": False,
        }

        return True, cleaned_intent

    def validate_and_clean_intents(self, intents: List[Dict]) -> Tuple[List[Dict], Dict]:
        """
        Validate all intents, clean them, and remove duplicates
        Returns (cleaned_intents, validation_report)
        """
        cleaned_intents = []
        removed_steps = []
        total_input = len(intents)

        for idx, intent_obj in enumerate(intents):
            is_valid, cleaned = self.validate_single_intent(intent_obj, idx)
            if is_valid:
                cleaned_intents.append(cleaned)
            else:
                removed_steps.append((idx, self.validation_errors[-1] if self.validation_errors else "Unknown error"))

        # Deduplicate consecutive actions
        deduplicated_intents = self._deduplicate_consecutive_actions(cleaned_intents)
        removed_due_to_dedup = len(cleaned_intents) - len(deduplicated_intents)

        # Generate validation report
        report = {
            "total_input_intents": total_input,
            "total_valid_intents": len(cleaned_intents),
            "total_after_dedup": len(deduplicated_intents),
            "removed_by_validation": len(removed_steps),
            "removed_by_dedup": removed_due_to_dedup,
            "removed_steps_details": removed_steps,
            "validation_errors": self.validation_errors,
            "validation_warnings": self.validation_warnings,
        }

        return deduplicated_intents, report

    def _deduplicate_consecutive_actions(self, intents: List[Dict]) -> List[Dict]:
        """
        Remove duplicate consecutive actions on the same element
        Implements rule 9: Deduplicate steps globally before final generation
        """
        if not intents:
            return []

        deduplicated = [intents[0]]

        for i in range(1, len(intents)):
            current = intents[i]
            previous = deduplicated[-1]

            # Check if action is same as previous
            is_duplicate = (
                current.get("event_type") == previous.get("event_type")
                and current.get("selector") == previous.get("selector")
                and current.get("intent") == previous.get("intent")
            )

            if not is_duplicate:
                deduplicated.append(current)
            else:
                self.validation_warnings.append(
                    f"Step {current['step_index']}: Removed duplicate action "
                    f"(same as step {previous['step_index']})"
                )

        return deduplicated

    def _extract_stable_selector(self, step: Dict) -> Optional[str]:
        """
        Extract stable selector from element (prefer ID, attributes, data-* over classes)
        Implements rule 2: Prefer stable selectors
        """
        element_html = step.get("eventElement", "")

        if not element_html:
            return None

        # Priority 1: ID attribute (most stable)
        if 'id="' in element_html:
            try:
                start = element_html.find('id="') + 4
                end = element_html.find('"', start)
                element_id = element_html[start:end]
                if element_id and element_id.strip():
                    return f"#{element_id}"
            except Exception:
                pass

        # Priority 2: data-testid attribute
        if 'data-testid="' in element_html:
            try:
                start = element_html.find('data-testid="') + 13
                end = element_html.find('"', start)
                testid = element_html[start:end]
                if testid and testid.strip():
                    return f'[data-testid="{testid}"]'
            except Exception:
                pass

        # Priority 3: name attribute (for inputs)
        if 'name="' in element_html:
            try:
                start = element_html.find('name="') + 6
                end = element_html.find('"', start)
                name = element_html[start:end]
                if name and name.strip():
                    return f'[name="{name}"]'
            except Exception:
                pass

        # Priority 4: aria-label attribute
        if 'aria-label="' in element_html:
            try:
                start = element_html.find('aria-label="') + 12
                end = element_html.find('"', start)
                label = element_html[start:end]
                if label and label.strip():
                    return f'[aria-label="{label}"]'
            except Exception:
                pass

        # Priority 5: Class (less stable, only as fallback)
        if 'class="' in element_html:
            try:
                start = element_html.find('class="') + 7
                end = element_html.find('"', start)
                classes = element_html[start:end]
                if classes and classes.strip():
                    # Use first class (most specific)
                    first_class = classes.split()[0]
                    if first_class:
                        return f".{first_class}"
            except Exception:
                pass

        # Fallback: Element type
        try:
            tag_match = re.match(r"<([a-zA-Z0-9]+)", element_html)
            if tag_match:
                tag = tag_match.group(1)
                if tag and tag.strip():
                    return tag
        except Exception:
            pass

        return None

    def _action_requires_selector(self, event_type: str) -> bool:
        """Determine if an action type requires a selector"""
        action_types_needing_selector = [
            "STEPS_FEATURE_CLICK_EVENT",
            "STEPS_FEATURE_TYPE_EVENT",
            "STEPS_FEATURE_SCROLL_EVENT",
            "STEPS_FEATURE_HOVER_EVENT",
            # Preprocessed action types
            "click",
            "type",
            "select",
            "submit",
            "hover",
        ]

        actions_not_needing_selector = [
            "STEPS_FEATURE_TAB_VISIBLE_EVENT",
            "STEPS_FEATURE_NAVIGATE_EVENT",
            "STEPS_FEATURE_WAIT_EVENT",
            "PREPROCESSED",  # Will check action field instead
        ]

        if event_type in action_types_needing_selector:
            return True
        if event_type in actions_not_needing_selector:
            return False

        # Default: require selector for unknown types to be safe
        return True

    def _is_valid_css_selector(self, selector: str) -> bool:
        """
        Validate CSS selector syntax
        Implements rule 10: Selector sanity check as final guardrail
        """
        if not selector or not isinstance(selector, str):
            return False

        selector = selector.strip()

        # Check for empty selector
        if len(selector) == 0:
            return False

        # Check for obviously malformed patterns
        invalid_patterns = [
            r'^\s*$',  # Whitespace only
            r'^\[\]',  # Empty attribute
            r'^\(\)$',  # Empty parentheses
            r'^[{}()>]',  # Starts with invalid chars (including >)
            r'[{}()>]$',  # Ends with invalid chars (including >)
            r'\s{2,}',  # Multiple spaces
            r'[\<\>]',  # HTML brackets
            r'[\n\r]',  # Newlines
            r'^>\s*\w',  # Starts with > (child selector orphan)
        ]

        for pattern in invalid_patterns:
            if re.search(pattern, selector):
                return False

        # Validate bracket matching
        if selector.count('[') != selector.count(']'):
            return False
        if selector.count('(') != selector.count(')'):
            return False

        # Additional check for element followed by > (like "p>")
        if re.match(r'^[a-zA-Z]+\s*>\s*$', selector):
            return False

        # Check for valid selector start
        valid_start_patterns = [
            r'^#',  # ID
            r'^\.',  # Class
            r'^\[',  # Attribute
            r'^[a-zA-Z]',  # Element
        ]

        if not any(re.match(pattern, selector) for pattern in valid_start_patterns):
            return False

        # Try to compile as regex to catch malformed patterns
        try:
            # Test basic CSS structure
            if selector.startswith('#'):
                # ID selector: #id-name
                if not re.match(r'^#[a-zA-Z0-9_-]+$', selector):
                    return False
            elif selector.startswith('.'):
                # Class selector: .class-name
                if not re.match(r'^\.[a-zA-Z0-9_-]+$', selector):
                    return False
            elif selector.startswith('['):
                # Attribute selector: [attr="value"]
                if not re.match(r'^\[[a-zA-Z0-9_-]+.*\]$', selector):
                    return False
            elif re.match(r'^[a-zA-Z]+$', selector):
                # Pure element selector: must be valid HTML element
                # Common HTML elements
                valid_elements = {
                    'div', 'span', 'p', 'a', 'button', 'input', 'form', 'label',
                    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li',
                    'table', 'tr', 'td', 'th', 'img', 'video', 'audio',
                    'section', 'article', 'nav', 'header', 'footer', 'main',
                }
                if selector.lower() not in valid_elements:
                    # Allow custom elements too, just check they're reasonable
                    if not re.match(r'^[a-zA-Z][a-zA-Z0-9-]*$', selector):
                        return False
            # Element selectors are more flexible, just check they're not too weird
        except Exception:
            return False

        return True

    def print_validation_report(self, report: Dict) -> None:
        """Print validation report"""
        print("\n" + "=" * 70)
        print("INTENT VALIDATION REPORT")
        print("=" * 70)
        print(f"Input intents:           {report['total_input_intents']}")
        print(f"Valid after validation:  {report['total_valid_intents']}")
        print(f"Removed by dedup:        {report['removed_by_dedup']}")
        print(f"Final count:             {report['total_after_dedup']}")
        print(f"Removed by validation:   {report['removed_by_validation']}")

        if report["validation_errors"]:
            print(f"\nValidation Errors ({len(report['validation_errors'])} found):")
            for error in report["validation_errors"][:5]:
                print(f"  - {error}")
            if len(report["validation_errors"]) > 5:
                print(f"  ... and {len(report['validation_errors']) - 5} more")

        if report["validation_warnings"]:
            print(f"\nValidation Warnings ({len(report['validation_warnings'])} found):")
            for warning in report["validation_warnings"][:5]:
                print(f"  - {warning}")
            if len(report["validation_warnings"]) > 5:
                print(f"  ... and {len(report['validation_warnings']) - 5} more")

        print("=" * 70)


if __name__ == "__main__":
    # Test the validator
    validator = IntentValidator()

    test_intents = [
        {
            "step_index": 0,
            "event_type": "STEPS_FEATURE_CLICK_EVENT",
            "intent": "Click button to submit",
            "original_step": {"eventElement": '<button id="submit-btn">Submit</button>'},
        },
        {
            "step_index": 1,
            "event_type": "STEPS_FEATURE_CLICK_EVENT",
            "intent": "",  # Empty intent - should be removed
            "original_step": {"eventElement": ""},
        },
        {
            "step_index": 2,
            "event_type": "STEPS_FEATURE_TYPE_EVENT",
            "intent": "Type email address",
            "original_step": {"eventElement": "<input name=\"email\" />"},
        }
    ]

    cleaned, report = validator.validate_and_clean_intents(test_intents)
    validator.print_validation_report(report)

    print("\nCleaned intents:")
    for intent in cleaned:
        print(f"  {intent}")
