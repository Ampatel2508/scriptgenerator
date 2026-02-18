#!/usr/bin/env python3
"""
JavaScript Code Tester - Tests generated Playwright JavaScript code
"""

import re
import subprocess
from typing import Tuple, List, Dict


class JavaScriptCodeTester:
    """Tests JavaScript code quality and structure"""
    
    def test_code(self, code: str) -> Dict:
        """Test JavaScript code and return error count"""
        errors = []
        
        # Test 1: Check for required Playwright imports
        if "require('playwright')" not in code:
            errors.append("Missing Playwright import")
        
        # Test 2: Check for async function definition
        if "async function" not in code:
            errors.append("Missing async function")
        
        # Test 3: Check for browser launch
        if "chromium.launch()" not in code:
            errors.append("Missing browser launch")
        
        # Test 4: Check for page creation
        if "newPage()" not in code:
            errors.append("Missing page creation")
        
        # Test 5: Check for browser close
        if "browser.close()" not in code:
            errors.append("Missing browser cleanup")
        
        # Test 6: Basic syntax validation
        syntax_errors = self._check_syntax(code)
        errors.extend(syntax_errors)
        
        # Test 7: Check for unclosed try-catch blocks
        unclosed_blocks = self._check_unclosed_blocks(code)
        errors.extend(unclosed_blocks)
        
        # Test 8: Check for invalid selectors
        invalid_selectors = self._check_invalid_selectors(code)
        errors.extend(invalid_selectors)
        
        # Test 9: Check for unescaped quotes
        unescaped_quotes = self._check_unescaped_quotes(code)
        errors.extend(unescaped_quotes)
        
        return {
            "total_errors": len(errors),
            "errors": errors,
            "status": "PASS" if len(errors) == 0 else "FAIL"
        }
    
    def _check_syntax(self, code: str) -> List[str]:
        """Check for basic syntax errors"""
        errors = []
        
        # Check for balanced braces
        open_braces = code.count('{')
        close_braces = code.count('}')
        if open_braces != close_braces:
            errors.append(f"Unbalanced braces: {open_braces} open, {close_braces} close")
        
        # Check for balanced parentheses
        open_parens = code.count('(')
        close_parens = code.count(')')
        if open_parens != close_parens:
            errors.append(f"Unbalanced parentheses: {open_parens} open, {close_parens} close")
        
        # Check for balanced square brackets
        open_brackets = code.count('[')
        close_brackets = code.count(']')
        if open_brackets != close_brackets:
            errors.append(f"Unbalanced brackets: {open_brackets} open, {close_brackets} close")
        
        return errors
    
    def _check_unclosed_blocks(self, code: str) -> List[str]:
        """Check for unclosed try-catch blocks"""
        errors = []
        
        try_count = len(re.findall(r'\btry\s*\{', code))
        catch_count = len(re.findall(r'\}\s*catch\s*\(', code))
        
        if try_count > 0 and catch_count != try_count:
            errors.append(f"Mismatched try-catch blocks: {try_count} try, {catch_count} catch")
        
        return errors
    
    def _check_invalid_selectors(self, code: str) -> List[str]:
        """Check for potentially invalid CSS selectors"""
        errors = []
        
        # Find all selectors
        selector_pattern = r'page\.\$\("([^"]+)"\)'
        selectors = re.findall(selector_pattern, code)
        
        invalid_chars = ['<', '>', '&', '|', '^', '$', '%']
        for selector in selectors:
            for char in invalid_chars:
                if char in selector:
                    errors.append(f"Invalid character '{char}' in selector: {selector}")
                    break
        
        return errors
    
    def _check_unescaped_quotes(self, code: str) -> List[str]:
        """Check for unescaped quotes in strings"""
        errors = []
        
        # Look for unescaped quotes in string literals
        pattern = r'(?<!\\)"[^"]*(?<!\\)"'
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Count quotes before escaped ones
            if '\"' in line or "\\'" in line:
                continue
            
            # Simple check: if line has unclosed quotes
            quote_count = line.count('"') - line.count('\\"')
            if quote_count % 2 != 0:
                errors.append(f"Unclosed quote on line {line_num}: {line.strip()[:50]}")
        
        return errors
    
    def count_goto_calls(self, code: str) -> int:
        """Count page.goto() calls"""
        return len(re.findall(r'page\.goto\(', code))
    
    def count_try_blocks(self, code: str) -> int:
        """Count try-catch blocks"""
        return len(re.findall(r'\btry\s*\{', code))
    
    def get_statistics(self, code: str) -> Dict:
        """Get code statistics"""
        lines = code.split('\n')
        
        return {
            "total_lines": len(lines),
            "non_empty_lines": len([l for l in lines if l.strip()]),
            "functions": len(re.findall(r'\bfunction\b', code)),
            "goto_calls": self.count_goto_calls(code),
            "try_blocks": self.count_try_blocks(code),
            "await_statements": len(re.findall(r'\bawait\b', code)),
            "comments": len(re.findall(r'//.*', code))
        }
