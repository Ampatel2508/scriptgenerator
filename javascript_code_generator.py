#!/usr/bin/env python3
"""
JavaScript Code Generator - Converts AST to Playwright JavaScript code
Implements rules 5-11: High-level APIs with auto-wait, navigation handling, explicit errors, 
and safety gates
"""

from typing import List, Dict, Optional
from ast_converter import PlaywrightAST, PlaywrightActionType


class JavaScriptCodeGenerator:
    """
    Generates Playwright JavaScript code from AST nodes using best practices:
    - Rules 5-6: High-level APIs with automatic waiting
    - Rule 7: Explicit navigation handling
    - Rule 8: Clear error reporting (no silent failures)
    - Rule 10: Selector sanity checks before code generation
    - Rule 11: Only generate if all safety checks pass
    """
    
    def __init__(self):
        self.generated_code = ""
        self.code_warnings = []
        self.code_errors = []
        self.selector_usage_count = {}  # Track how many times each selector is used
        self.selector_index_map = {}    # Map selector to index for nth() usage
    
    def generate_code_from_ast(self, ast_nodes: List[PlaywrightAST], intents: List[Dict] = None, first_url: str = None) -> str:
        """
        Generate JavaScript code from AST nodes
        RULE 11: Only generate if all safety checks pass
        Parameters:
            ast_nodes: List of AST nodes to generate code from
            intents: Optional list of intents to extract base URL from
            first_url: Optional explicit first URL to use (overrides intents)
        """
        if not ast_nodes:
            print("[WARN] No AST nodes to generate code from")
            return ""
        
        # RULE 11: Verify all nodes are safe before generating code
        safe_nodes = self._validate_all_nodes_before_codegen(ast_nodes)
        
        if not safe_nodes:
            print("[FAIL] Code generation STOPPED: No safe AST nodes to generate code from")
            self.code_errors.append("No valid AST nodes passed safety checks")
            return ""
        
        # Analyze selector usage to handle duplicates
        self._analyze_selector_usage(safe_nodes)
        
        lines = []
        
        # Header
        lines.append("// Auto-generated Playwright JavaScript test script")
        lines.append("// This script uses Playwright's high-level APIs with automatic waiting")
        lines.append("// All elements are located by ID or class name with proper handling for duplicates")
        lines.append("const { chromium } = require('playwright');")
        lines.append("")
        lines.append("async function runTests() {")
        lines.append("    const browser = await chromium.launch();")
        lines.append("    const page = await browser.newPage();")
        lines.append("    let lastError = null;")
        
        # Extract base URL for initial navigation
        base_url = first_url or self._extract_base_url_from_intents(intents) or self._extract_base_url_from_ast(safe_nodes) or "https://www.example.com"
        lines.append("")
        lines.append("    try {")
        lines.append("")
        
        # Generate initial navigation block with the first navigation URL
        initial_block = self._generate_initial_navigation_block(safe_nodes, base_url)
        if initial_block:
            lines.append(initial_block)
            lines.append("")
        
        # Track selector occurrences as we generate code
        selector_occurrence_counter = {}
        
        # Generate code for each safe AST node (skip first NAVIGATE since it's in initial block)
        skip_first_navigate = True
        for idx, node in enumerate(safe_nodes):
            # Skip the first navigation node as it's already handled by initial navigation block
            if skip_first_navigate and node.action_type == PlaywrightActionType.NAVIGATE:
                skip_first_navigate = False
                continue
            
            # Track which occurrence this selector is
            if node.selector:
                if node.selector not in selector_occurrence_counter:
                    selector_occurrence_counter[node.selector] = 0
                occurrence = selector_occurrence_counter[node.selector]
                selector_occurrence_counter[node.selector] += 1
            else:
                occurrence = 0
            
            generated_action = self._generate_action(node, idx, occurrence)
            if generated_action:
                lines.append(generated_action)
        
        # Footer with error reporting
        lines.append("")
        lines.append("        console.log('[OK] All steps completed successfully');")
        lines.append("    } catch (error) {")
        lines.append("        console.error('[FAIL] Test execution failed:', error.message);")
        lines.append("        lastError = error;")
        lines.append("    } finally {")
        lines.append("        await browser.close();")
        lines.append("    }")
        lines.append("}")
        lines.append("")
        lines.append("runTests().catch(error => {")
        lines.append("    console.error('[FAIL] Unrecoverable error:', error);")
        lines.append("    process.exit(1);")
        lines.append("});")
        
        self.generated_code = '\n'.join(lines)
        return self.generated_code
    
    def _analyze_selector_usage(self, ast_nodes: List[PlaywrightAST]) -> None:
        """
        Analyze and count selector usage across all nodes
        Maps selectors to indices for proper nth-child or first() usage
        """
        self.selector_usage_count = {}
        self.selector_index_map = {}
        
        for node in ast_nodes:
            if node.selector and node.action_type in [
                PlaywrightActionType.CLICK,
                PlaywrightActionType.FILL_TEXT,
                PlaywrightActionType.SELECT,
                PlaywrightActionType.HOVER,
            ]:
                selector = node.selector
                
                # Count this selector
                if selector not in self.selector_usage_count:
                    self.selector_usage_count[selector] = 0
                    self.selector_index_map[selector] = []
                
                self.selector_index_map[selector].append(self.selector_usage_count[selector])
                self.selector_usage_count[selector] += 1
    
    def _get_locator_string(self, selector: str, occurrence: int = 0) -> str:
        """
        Get the proper Playwright locator string with nth/first handling
        If selector appears multiple times, adds .first() or .nth()
        """
        # Ensure selector uses CSS/attribute selector format
        if selector.startswith("#"):
            # ID selector
            locator = f"page.locator('{selector}')"
        elif selector.startswith("."):
            # Class selector
            locator = f"page.locator('{selector}')"
        elif selector.startswith("["):
            # Attribute selector
            locator = f"page.locator('{selector}')"
        else:
            # If it's just a tag name or complex selector
            locator = f"page.locator('{selector}')"
        
        # If this selector is used multiple times, add index
        total_count = self.selector_usage_count.get(selector, 1)
        
        if total_count > 1:
            # For multiple elements with same selector, use nth()
            locator += f".nth({occurrence})"
        
        return locator
    
    def _get_locator_with_occurrence(self, selector: str, occurrence: int = 0) -> str:
        """
        Generate proper Playwright locator code with nd-child handling
        Uses .nth() when multiple elements share the same selector
        """
        if not selector:
            return "page.locator('body')"
        
        # Escape selector for JavaScript string
        escaped_selector = selector.replace("'", "\\'").replace('"', '\\"')
        
        # Check if this selector appears multiple times
        total_count = self.selector_usage_count.get(selector, 1)
        
        if total_count > 1:
            # Use nth() for multiple occurrences
            return f"page.locator('{escaped_selector}').nth({occurrence})"
        else:
            # Use first() for single occurrence (more readable)
            return f"page.locator('{escaped_selector}').first()"
    
    def _extract_base_url_from_intents(self, intents: List[Dict]) -> Optional[str]:
        """Extract base URL from the first intent's original_step"""
        if not intents or len(intents) == 0:
            return None
        
        try:
            first_intent = intents[0]
            original_step = first_intent.get("original_step", {})
            url = original_step.get("clean_url") or original_step.get("url")
            
            if url:
                # Extract base URL (domain + path, no query params or fragments)
                from urllib.parse import urlparse
                parsed = urlparse(url)
                base = f"{parsed.scheme}://{parsed.netloc}"
                return base
        except Exception:
            pass
        
        return None
    
    def _extract_base_url_from_ast(self, ast_nodes: List[PlaywrightAST]) -> Optional[str]:
        """Extract base URL from first node that has a URL"""
        if not ast_nodes:
            return None
        
        try:
            for node in ast_nodes:
                if node.url:
                    from urllib.parse import urlparse
                    parsed = urlparse(node.url)
                    base = f"{parsed.scheme}://{parsed.netloc}"
                    return base
        except Exception:
            pass
        
        return None
    
    def _generate_initial_navigation_block(self, ast_nodes: List[PlaywrightAST], base_url: str = None) -> str:
        """
        Generate the initial navigation block with proper format
        Uses provided base_url, or extracts from first navigate action
        """
        indent = "        "
        
        # Priority 1: Use provided base_url
        if base_url:
            initial_url = base_url
        else:
            # Priority 2: Find first navigation node
            initial_url = None
            for node in ast_nodes:
                if node.action_type == PlaywrightActionType.NAVIGATE:
                    initial_url = node.url
                    break
            
            # Priority 3: Use a generic base URL
            if not initial_url:
                initial_url = "https://www.example.com"
        
        # Escape the URL for JavaScript
        escaped_url = self._escape_string(initial_url)
        
        return (f'{indent}// Initial Navigation: Load the base page\n'
               f'{indent}console.log("Initial: Navigating to {escaped_url}...");\n'
               f'{indent}try {{\n'
               f'{indent}    await page.goto("{escaped_url}", {{ waitUntil: "load", timeout: 30000 }});\n'
               f'{indent}    await page.waitForTimeout(1000);\n'
               f'{indent}    console.log("  [OK] Page loaded successfully");\n'
               f'{indent}}} catch (error) {{\n'
               f'{indent}    console.warn("  [WARN] Page load warning: " + error.message + " (continuing anyway)");\n'
               f'{indent}}}')
    
    def _validate_all_nodes_before_codegen(self, ast_nodes: List[PlaywrightAST]) -> List[PlaywrightAST]:
        """
        RULE 11: Final safety gate - validate all nodes before code generation
        Filters out nodes that cannot be safely converted
        """
        safe_nodes = []
        
        for idx, node in enumerate(ast_nodes):
            if self._is_node_safe_for_codegen(node, idx):
                safe_nodes.append(node)
            else:
                self.code_warnings.append(
                    f"Step {idx}: Node failed safety check, skipped from code generation"
                )
        
        return safe_nodes
    
    def _is_node_safe_for_codegen(self, node: PlaywrightAST, step_idx: int) -> bool:
        """Check if AST node is safe for code generation"""
        if not node:
            return False
        
        if not node.action_type:
            return False
        
        # WAIT actions (context events) don't require selectors or URLs
        if node.action_type == PlaywrightActionType.WAIT:
            return True
        
        # RULE 10: Selector sanity check for actions that need selectors
        if node.action_type in [
            PlaywrightActionType.CLICK,
            PlaywrightActionType.FILL_TEXT,
            PlaywrightActionType.SELECT,
            PlaywrightActionType.HOVER,
        ]:
            if not node.selector or not isinstance(node.selector, str) or not node.selector.strip():
                self.code_errors.append(f"Step {step_idx}: Missing selector for {node.action_type.value}")
                return False
            
            # RULE 10: Additional selector validation - check for malformed patterns
            if not self._is_valid_selector(node.selector):
                self.code_errors.append(f"Step {step_idx}: Malformed selector '{node.selector}' rejected")
                return False
        
        # RULE 10: Validate URL for navigation
        if node.action_type == PlaywrightActionType.NAVIGATE:
            if not node.url or not isinstance(node.url, str) or not node.url.strip():
                self.code_errors.append(f"Step {step_idx}: Missing URL for navigate action")
                return False
        
        return True
    
    def _is_valid_selector(self, selector: str) -> bool:
        """Final validation of selectors to prevent malformed ones"""
        if not selector or not isinstance(selector, str):
            return False
        
        import re
        
        # Check for obviously malformed patterns
        malformed_patterns = [
            r'^[{}()>]',           # Starts with invalid
            r'[{}()>]$',           # Ends with invalid
            r'[\<\>]',             # HTML brackets (except in attributes)
            r'^[a-zA-Z]+\s*>\s*$', # Element followed by >
        ]
        
        for pattern in malformed_patterns:
            if re.search(pattern, selector):
                return False
        
        return True
    
    def _generate_action(self, node: PlaywrightAST, step_index: int, occurrence: int = 0) -> str:
        """
        Generate JavaScript code for a single action
        RULE 5: Use high-level APIs with auto-wait (locator-based, not page.$)
        RULE 6: Automatic waiting before every interaction
        RULE 7: Explicitly handle navigation
        RULE 8: Clear error reporting
        Parameters:
            node: PlaywrightAST node with action details
            step_index: Index of this step
            occurrence: Which occurrence of this selector (for nth-child handling)
        """
        indent = "        "
        action_type = node.action_type.value
        
        if action_type == "navigate":
            # RULE 7: Explicit navigation handling with await
            url = self._escape_string(node.url)
            return (f'{indent}// Step {step_index}: Navigate to {url}\n'
                   f'{indent}console.log("Step {step_index}: Navigating to {url}...");\n'
                   f'{indent}try {{\n'
                   f'{indent}    await page.goto("{url}", {{ waitUntil: "networkidle" }});\n'
                   f'{indent}    console.log("  [OK] Navigation complete");\n'
                   f'{indent}}} catch (error) {{\n'
                   f'{indent}    throw new Error("Navigation failed at step {step_index}: " + error.message);\n'
                   f'{indent}}}')
        
        elif action_type == "click":
            # RULE 5: Use locator API with auto-wait instead of page.$()
            # RULE 6: Implicit wait through waitForSelector
            # ENHANCED: Use nth() for duplicate selectors
            selector = node.selector
            locator_code = self._get_locator_with_occurrence(selector, occurrence)
            return (f'{indent}// Step {step_index}: Click on element\n'
                   f'{indent}console.log("Step {step_index}: Clicking on element...");\n'
                   f'{indent}try {{\n'
                   f'{indent}    const locator = {locator_code};\n'
                   f'{indent}    await locator.waitFor({{ state: "visible", timeout: 5000 }});\n'
                   f'{indent}    await locator.click();\n'
                   f'{indent}    await page.waitForTimeout(500);\n'
                   f'{indent}    console.log("  [OK] Click action complete");\n'
                   f'{indent}}} catch (error) {{\n'
                   f'{indent}    throw new Error("Click failed at step {step_index}: " + error.message);\n'
                   f'{indent}}}')
        
        elif action_type == "fill":
            # RULE 5 & 6: Use locator with auto-wait and implicit waiting
            # ENHANCED: Use nth() for duplicate selectors
            selector = node.selector
            value = self._escape_string(node.value)
            locator_code = self._get_locator_with_occurrence(selector, occurrence)
            return (f'{indent}// Step {step_index}: Fill input field\n'
                   f'{indent}console.log("Step {step_index}: Filling input field...");\n'
                   f'{indent}try {{\n'
                   f'{indent}    const locator = {locator_code};\n'
                   f'{indent}    await locator.waitFor({{ state: "visible", timeout: 5000 }});\n'
                   f'{indent}    await locator.fill("{value}");\n'
                   f'{indent}    console.log("  [OK] Fill action complete");\n'
                   f'{indent}}} catch (error) {{\n'
                   f'{indent}    throw new Error("Fill failed at step {step_index}: " + error.message);\n'
                   f'{indent}}}')
        
        elif action_type == "select":
            # RULE 5 & 6: Use locator API with auto-wait
            # ENHANCED: Use nth() for duplicate selectors
            selector = node.selector
            value = self._escape_string(node.value)
            locator_code = self._get_locator_with_occurrence(selector, occurrence)
            return (f'{indent}// Step {step_index}: Select option\n'
                   f'{indent}console.log("Step {step_index}: Selecting option...");\n'
                   f'{indent}try {{\n'
                   f'{indent}    const locator = {locator_code};\n'
                   f'{indent}    await locator.waitFor({{ state: "visible", timeout: 5000 }});\n'
                   f'{indent}    await locator.selectOption("{value}");\n'
                   f'{indent}    console.log("  [OK] Select action complete");\n'
                   f'{indent}}} catch (error) {{\n'
                   f'{indent}    throw new Error("Select failed at step {step_index}: " + error.message);\n'
                   f'{indent}}}')
        
        elif action_type == "wait":
            # Explicit wait
            wait_time = node.wait_time or 5000
            return (f'{indent}// Step {step_index}: Wait for element\n'
                   f'{indent}console.log("Step {step_index}: Waiting {wait_time}ms...");\n'
                   f'{indent}try {{\n'
                   f'{indent}    await page.waitForTimeout({wait_time});\n'
                   f'{indent}    console.log("  [OK] Wait complete");\n'
                   f'{indent}}} catch (error) {{\n'
                   f'{indent}    throw new Error("Wait failed at step {step_index}: " + error.message);\n'
                   f'{indent}}}')
        
        elif action_type == "scroll":
            # Explicit scroll with error handling
            return (f'{indent}// Step {step_index}: Scroll page\n'
                   f'{indent}console.log("Step {step_index}: Scrolling down...");\n'
                   f'{indent}try {{\n'
                   f'{indent}    await page.evaluate(() => window.scrollBy(0, window.innerHeight));\n'
                   f'{indent}    await page.waitForTimeout(500);\n'
                   f'{indent}    console.log("  [OK] Scroll complete");\n'
                   f'{indent}}} catch (error) {{\n'
                   f'{indent}    throw new Error("Scroll failed at step {step_index}: " + error.message);\n'
                   f'{indent}}}')
        
        elif action_type == "hover":
            # RULE 5 & 6: Use locator with auto-wait
            # ENHANCED: Use nth() for duplicate selectors
            selector = node.selector
            locator_code = self._get_locator_with_occurrence(selector, occurrence)
            return (f'{indent}// Step {step_index}: Hover on element\n'
                   f'{indent}console.log("Step {step_index}: Hovering on element...");\n'
                   f'{indent}try {{\n'
                   f'{indent}    const locator = {locator_code};\n'
                   f'{indent}    await locator.waitFor({{ state: "visible", timeout: 5000 }});\n'
                   f'{indent}    await locator.hover();\n'
                   f'{indent}    console.log("  [OK] Hover complete");\n'
                   f'{indent}}} catch (error) {{\n'
                   f'{indent}    throw new Error("Hover failed at step {step_index}: " + error.message);\n'
                   f'{indent}}}')
        
        elif action_type == "press":
            # Press key
            key = node.value or "Enter"
            return (f'{indent}// Step {step_index}: Press key\n'
                   f'{indent}console.log("Step {step_index}: Pressing {key}...");\n'
                   f'{indent}try {{\n'
                   f'{indent}    await page.press("body", "{key}");\n'
                   f'{indent}    await page.waitForTimeout(500);\n'
                   f'{indent}    console.log("  [OK] Key press complete");\n'
                   f'{indent}}} catch (error) {{\n'
                   f'{indent}    throw new Error("Key press failed at step {step_index}: " + error.message);\n'
                   f'{indent}}}')
        
        elif action_type == "keyboard":
            # Type text
            keys = node.value or ""
            return (f'{indent}// Step {step_index}: Type text\n'
                   f'{indent}console.log("Step {step_index}: Typing text...");\n'
                   f'{indent}try {{\n'
                   f'{indent}    await page.keyboard.type("{self._escape_string(keys)}");\n'
                   f'{indent}    console.log("  [OK] Text input complete");\n'
                   f'{indent}}} catch (error) {{\n'
                   f'{indent}    throw new Error("Text input failed at step {step_index}: " + error.message);\n'
                   f'{indent}}}')
        
        elif action_type == "screenshot":
            # Take screenshot
            filename = f"screenshot_step_{step_index}.png"
            return (f'{indent}// Step {step_index}: Take screenshot\n'
                   f'{indent}console.log("Step {step_index}: Taking screenshot...");\n'
                   f'{indent}try {{\n'
                   f'{indent}    await page.screenshot({{ path: "{filename}" }});\n'
                   f'{indent}    console.log("  [OK] Screenshot saved to {filename}");\n'
                   f'{indent}}} catch (error) {{\n'
                   f'{indent}    throw new Error("Screenshot failed at step {step_index}: " + error.message);\n'
                   f'{indent}}}')
        
        else:
            # Default fallback
            return f'{indent}// Step {step_index}: {action_type}'
    
    def _escape_selector(self, selector: str) -> str:
        """Escape selector for JavaScript string"""
        if not selector:
            return ""
        return selector.replace('"', '\\"').replace("'", "\\'")
    
    def _escape_string(self, text: str) -> str:
        """Escape string for JavaScript"""
        if not text:
            return ""
        return text.replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
    
    def save_code(self, filepath: str = "generated_script.js"):
        """Save generated code to file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.generated_code)
        print(f"[OK] Generated JavaScript script saved to {filepath}")
        
        # Print code statistics
        lines = self.generated_code.split('\n')
        print(f"  Script size: {len(lines)} lines")
        print(f"  Locator uses (high-level): {sum(1 for l in lines if 'page.locator' in l)}")
        print(f"  Explicit wait calls: {sum(1 for l in lines if 'waitFor' in l)}")
        print(f"  Error handling blocks: {sum(1 for l in lines if 'throw new Error' in l)}")
        
        # Print any warnings/errors
        if self.code_errors:
            print(f"\n  Code Generation Errors ({len(self.code_errors)}):")
            for error in self.code_errors[:3]:
                print(f"    - {error}")
            if len(self.code_errors) > 3:
                print(f"    ... and {len(self.code_errors) - 3} more")
