#!/usr/bin/env python3
"""
Main orchestrator for RAG-based Playwright script generator
Combines preprocessing, chunking, intent generation, AST conversion, and code generation
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional

# Import all modules
from steps_preprocessor import StepsPreprocessor
from document_chunker import DocumentChunker
from intent_generator import IntentGenerator
from ast_converter import ASTConverter, PlaywrightAST, PlaywrightActionType
from javascript_code_generator import JavaScriptCodeGenerator
from javascript_code_tester import JavaScriptCodeTester
from dom_validator import validate_ast_sync


class PlaywrightScriptGenerator:
    """Main orchestrator for the entire pipeline"""
    
    def __init__(self, steps_file: str = "steps.json"):
        self.steps_file = steps_file
        self.raw_steps = []
        self.preprocessed_steps = []
        self.steps = []
        self.documents = []
        self.chunks = []
        self.intents = []
        self.ast_nodes = []
        self.generated_code = ""
        self.test_results = None
        
        # Initialize components
        self.preprocessor = StepsPreprocessor()
        self.chunker = DocumentChunker(chunk_size=500, chunk_overlap=100)
        self.intent_gen = IntentGenerator(use_gemini=True)
        self.ast_converter = ASTConverter()
        self.code_gen = JavaScriptCodeGenerator()
        self.code_tester = JavaScriptCodeTester()
        
    def run_pipeline(self, save_intermediates: bool = True, validate_dom: bool = True) -> Dict:
        """Run the complete pipeline"""
        
        print("\n" + "="*70)
        print("PLAYWRIGHT SCRIPT GENERATOR - FULL PIPELINE")
        print("="*70)
        
        # Step 0: Preprocess steps (NEW)
        print("\n[STEP 0/6] Preprocessing Steps: Classifying & Normalizing Events...")
        print("-" * 70)
        self.preprocess_steps()
        
        # Step 1: Load and chunk data
        print("\n[STEP 1/6] Loading and Chunking Preprocessed Steps...")
        print("-" * 70)
        self.load_and_chunk_steps()
        
        # Step 2: Generate intents
        print("\n[STEP 2/6] Generating Intents from Steps...")
        print("-" * 70)
        self.generate_intents()
        
        # RULE 11: Safety check after intent generation
        if len(self.intents) == 0:
            print("\n[FAIL] PIPELINE ABORTED: No valid intents generated")
            return self._get_failed_summary("No valid intents after validation")
        
        # Step 3: Convert intents to AST
        print("\n[STEP 3/6] Converting Intents to Abstract Syntax Trees...")
        print("-" * 70)
        self.convert_to_ast()
        
        # RULE 11: Safety check after AST conversion
        if len(self.ast_nodes) == 0:
            print("\n[FAIL] PIPELINE ABORTED: No valid AST nodes generated")
            return self._get_failed_summary("No valid AST nodes after conversion")
        
        # Step 3.5: Validation against live DOM (NEW)
        if validate_dom:
            print(f"\n[STEP 3.5/6] Validating AST against live DOM (Rule 9)...")
            print("-" * 70)
            self.validate_ast_with_dom()

        # Step 4: Generate Playwright code
        print("\n[STEP 4/6] Generating Playwright Code...")
        print("-" * 70)
        self.generate_code()
        
        # RULE 11: Safety check after code generation
        if not self.generated_code or len(self.generated_code.strip()) == 0:
            print("\n[FAIL] PIPELINE ABORTED: Code generation failed or produced empty output")
            return self._get_failed_summary("Code generation failed")
        
        # Step 5: Test generated code
        print("\n[STEP 5/6] Testing Generated Code...")
        print("-" * 70)
        self.test_code()
        
        # Save results
        if save_intermediates:
            print("\n[STEP 6/6] Saving Intermediate Results...")
            print("-" * 70)
            self.save_all_intermediates()
        
        print("\n" + "="*70)
        print("PIPELINE EXECUTION COMPLETED")
        print("="*70)
        
        return self.get_summary()
    
    def load_and_chunk_steps(self) -> None:
        """Load preprocessed steps and create chunks"""
        print(f"Loading preprocessed steps...")
        
        # Use preprocessed steps instead of raw steps
        self.steps = self.preprocessed_steps if self.preprocessed_steps else []
        print(f"[OK] Using {len(self.steps)} preprocessed action steps")
        
        if not self.steps:
            print("[WARN] No preprocessed steps available. Chunking skipped.")
            return
        
        # Convert to documents
        self.documents = self.chunker.convert_steps_to_documents(self.steps)
        print(f"[OK] Created {len(self.documents)} documents from preprocessed steps")
        
        # Chunk documents
        self.chunks = self.chunker.chunk_documents(self.documents)
        print(f"[OK] Chunked into {len(self.chunks)} pieces")
        
        # Setup vector store
        try:
            print("Setting up vector store (RAG)...")
            self.chunker.setup_vector_store(self.chunks)
            print("[OK] Vector store initialized")
        except Exception as e:
            print(f"[WARN] Vector store setup failed (non-critical): {e}")
    
    def preprocess_steps(self) -> None:
        """
        Preprocess raw steps into clean semantic representation.
        Filters context events, normalizes action events, strips tracking params.
        """
        print(f"Loading raw steps from {self.steps_file}...")
        self.raw_steps = self.preprocessor.load_steps(self.steps_file)
        
        if not self.raw_steps:
            print("[FAIL] Failed to load steps file")
            return
        
        print(f"\nPreprocessing {len(self.raw_steps)} raw events...")
        self.preprocessed_steps = self.preprocessor.preprocess(self.raw_steps)
        
        if not self.preprocessed_steps:
            print("[FAIL] Preprocessing produced no output")
            return
        
        # Save preprocessing outputs for reference/debugging
        self.preprocessor.save_preprocessed_steps("steps_preprocessed.json")
        self.preprocessor.save_context_events("steps_context_events.json")
    
    def generate_intents(self) -> None:
        """Generate intents for all steps"""
        print(f"Generating intents for {len(self.steps)} steps...")
        
        self.intents = self.intent_gen.generate_intents_for_all_steps(self.steps)
        print(f"[OK] Generated {len(self.intents)} valid intents after validation/cleaning")
        
        if len(self.intents) == 0:
            print("[WARN] WARNING: No valid intents generated. Pipeline may produce empty code.")
        
        # Show sample intents
        if self.intents:
            print("\nSample Intents (first 3):")
            for i, intent in enumerate(self.intents[:3]):
                selector_info = f" [selector: {intent.get('selector')}]" if intent.get('selector') else ""
                try:
                    intent_text = intent['intent'].encode('utf-8', errors='replace').decode('utf-8')
                    print(f"  Step {intent.get('step_index')}: {intent_text}{selector_info}")
                except Exception:
                    print(f"  Step {intent.get('step_index')}: [Intent with non-ASCII chars]{selector_info}")
    
    def convert_to_ast(self) -> None:
        """
        Convert intents to AST nodes
        RULE 4 & 11: Validates all intents before AST generation
        """
        print(f"Processing {len(self.intents)} validated intents...")
        
        self.ast_nodes = self.ast_converter.convert_all_intents_to_ast(self.intents)
        
        if len(self.ast_nodes) == 0:
            print("[WARN] WARNING: No valid AST nodes generated. Code generation will be skipped.")
        else:
            print(f"[OK] Created {len(self.ast_nodes)} valid AST nodes")
        
        # Show action type distribution
        action_types = {}
        for node in self.ast_nodes:
            action_type = node.action_type.value
            action_types[action_type] = action_types.get(action_type, 0) + 1
        
        if action_types:
            print("\nAction Types Distribution:")
            for action_type, count in sorted(action_types.items()):
                print(f"  {action_type}: {count}")
        
        # Report any conversion errors
        if hasattr(self.ast_converter, 'conversion_errors') and self.ast_converter.conversion_errors:
            print(f"\n[WARN] Conversion issues: {len(self.ast_converter.conversion_errors)} steps failed safety checks")
            
    def validate_ast_with_dom(self) -> None:
        """
        RULE 9: Validate AST candidates against live DOM
        Ensures high reliability before final code generation
        """
        if not self.ast_nodes:
            print("[WARN] No AST nodes to validate")
            return
            
        # Run live validation
        self.ast_nodes = validate_ast_sync(self.ast_nodes)
        print(f"[OK] AST nodes validated against live DOM")
    
    def generate_code(self) -> None:
        """
        Generate JavaScript code from AST
        RULE 11: Only generate code if all safety checks passed
        """
        # RULE 11: Safety gate - only proceed if AST nodes are available
        if not self.ast_nodes:
            print("[FAIL] CODE GENERATION STOPPED: No valid AST nodes available")
            print("  Reason: Intents did not pass validation or AST conversion failed")
            self.generated_code = ""
            return
        
        print("Generating Playwright JavaScript code...")
        
        # Pass intents to code generator so it can extract the base URL from the first step
        self.generated_code = self.code_gen.generate_code_from_ast(
            self.ast_nodes, 
            intents=self.intents
        )
        
        if not self.generated_code or len(self.generated_code.strip()) == 0:
            print("[FAIL] Code generation failed or produced empty output")
            self.generated_code = ""
            return
        
        print(f"[OK] Generated {len(self.generated_code.split(chr(10)))} lines of JavaScript code")
        
        # Show code statistics
        lines = self.generated_code.split('\n')
        print(f"\nCode Statistics:")
        print(f"  Total lines: {len(lines)}")
        print(f"  Await statements: {sum(1 for l in lines if 'await' in l)}")
        print(f"  Locator references (high-level API): {sum(1 for l in lines if 'page.locator' in l)}")
        print(f"  Explicit wait calls (waitFor): {sum(1 for l in lines if 'waitFor(' in l)}")
        print(f"  Error throw statements: {sum(1 for l in lines if 'throw new Error' in l)}")
        print(f"  Page navigation calls: {sum(1 for l in lines if 'page.goto' in l)}")
    
    def test_code(self) -> None:
        """Test the generated code"""
        print("Running code quality tests...")
        
        self.test_results = self.code_tester.test_code(self.generated_code)
        
        print(f"\nGenerated JavaScript Code - Error Analysis:")
        print(f"  Total Errors Found: {self.test_results['total_errors']}")
        
        if self.test_results['errors']:
            print(f"\n  Error Details:")
            for error in self.test_results['errors']:
                print(f"    - {error}")
    
    def save_all_intermediates(self) -> None:
        """Save generated code if it exists"""
        
        if not self.generated_code or len(self.generated_code.strip()) == 0:
            print("[WARN] No code to save (code generation failed or was skipped)")
            return
        
        # Save generated code
        self.code_gen.save_code("generated_script.js")
        
        print("[OK] Generated script saved:")
        print("  - generated_script.js")
    
    def get_summary(self) -> Dict:
        """Get pipeline execution summary"""
        return {
            "pipeline_status": "SUCCESS" if not self.test_results or self.test_results.get("status") == "PASS" else "FAILED",
            "steps_processed": len(self.steps),
            "intents_generated": len(self.intents),
            "ast_nodes_created": len(self.ast_nodes),
            "code_lines": len(self.generated_code.split('\n')) if self.generated_code else 0,
            "js_code_errors": self.test_results.get("total_errors", 0) if self.test_results else 0,
            "test_status": self.test_results.get("status", "UNKNOWN") if self.test_results else "UNKNOWN"
        }
    
    def _get_failed_summary(self, reason: str) -> Dict:
        """Get summary for failed pipeline"""
        return {
            "pipeline_status": "ABORTED",
            "failure_reason": reason,
            "steps_processed": len(self.steps),
            "intents_generated": len(self.intents),
            "ast_nodes_created": len(self.ast_nodes),
            "code_lines": 0,
            "js_code_errors": 0,
            "test_status": "SKIPPED"
        }
    
    def print_generated_code(self, lines_to_show: int = 50) -> None:
        """Print the generated code"""
        if not self.generated_code or len(self.generated_code.strip()) == 0:
            print("\n" + "="*70)
            print("NO GENERATED CODE")
            print("="*70)
            print("Code generation was skipped or failed due to failed safety checks.")
            return
        
        print("\n" + "="*70)
        print("GENERATED JAVASCRIPT SCRIPT (First 50 lines)")
        print("="*70)
        
        code_lines = self.generated_code.split('\n')
        for idx, line in enumerate(code_lines[:lines_to_show], 1):
            print(f"{idx:3d}: {line}")
        
        if len(code_lines) > lines_to_show:
            print(f"\n... ({len(code_lines) - lines_to_show} more lines)")


def main():
    """Main entry point"""
    
    # Check if steps.json exists
    if not os.path.exists("steps.json"):
        print("Error: steps.json not found!")
        sys.exit(1)
    
    # Run the pipeline
    generator = PlaywrightScriptGenerator()
    summary = generator.run_pipeline(save_intermediates=True)
    
    # Print generated code
    generator.print_generated_code()
    
    # Print final summary with enhanced status
    print("\n" + "="*70)
    print("FINAL SUMMARY - GENERATED JAVASCRIPT CODE")
    print("="*70)
    print(f"Pipeline Status:       {summary['pipeline_status']}")
    print(f"Steps Processed:       {summary['steps_processed']}")
    print(f"Intents Generated:     {summary['intents_generated']}")
    print(f"AST Nodes Created:     {summary['ast_nodes_created']}")
    print(f"Code Lines Generated:  {summary['code_lines']}")
    print(f"JavaScript Errors:     {summary['js_code_errors']}")
    
    if summary['pipeline_status'] == "ABORTED":
        print(f"Failure Reason:        {summary.get('failure_reason', 'Unknown')}")
        print("="*70)
        print("\n[FAIL] Pipeline aborted due to failed safety checks")
        sys.exit(1)
    
    print("="*70)
    
    if summary['code_lines'] > 0:
        print("\n[OK] Pipeline completed successfully!")
        print(f"[OK] Generated script: generated_script.js")
    else:
        print("\n[WARN] Pipeline completed but no code was generated")


if __name__ == "__main__":
    main()
