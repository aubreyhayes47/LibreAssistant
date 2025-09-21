#!/usr/bin/env python3
"""
Demo script to show plugin error propagation to LLM functionality.
This demonstrates how the LLM can handle plugin errors gracefully.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_protocol import LLMProtocol
import json

def demo_error_prompts():
    """Demonstrate the error prompts that are generated for the LLM"""
    print("=== Plugin Error Propagation Demo ===\n")
    
    llm_protocol = LLMProtocol()
    
    print("1. TIMEOUT ERROR SCENARIO")
    print("-" * 50)
    timeout_error = {
        'error_type': 'timeout',
        'plugin_id': 'brave-search',
        'message': 'Plugin brave-search processing timed out after 30 seconds.',
        'timeout_duration': 30,
        'suggestion': 'This was likely due to the plugin taking too long to respond.'
    }
    
    timeout_prompt = llm_protocol.create_plugin_error_prompt(
        'brave-search', timeout_error, "Search for the latest AI news"
    )
    
    print(f"Original user request: 'Search for the latest AI news'")
    print(f"Plugin that failed: brave-search (timeout)")
    print(f"\nPrompt sent to LLM for error handling:")
    print(timeout_prompt)
    print(f"\nExpected LLM behavior: The LLM should acknowledge the search timeout")
    print(f"and either try alternative approaches or provide a helpful response without the search results.\n")
    
    print("2. CONNECTION ERROR SCENARIO")
    print("-" * 50)
    connection_error = {
        'error_type': 'connection_error',
        'plugin_id': 'local-fileio',
        'message': 'Lost connection to server while processing plugin local-fileio.',
        'suggestion': 'This appears to be a connection issue.'
    }
    
    connection_prompt = llm_protocol.create_plugin_error_prompt(
        'local-fileio', connection_error, "Read the contents of my notes.txt file"
    )
    
    print(f"Original user request: 'Read the contents of my notes.txt file'")
    print(f"Plugin that failed: local-fileio (connection error)")
    print(f"\nPrompt sent to LLM for error handling:")
    print(connection_prompt)
    print(f"\nExpected LLM behavior: The LLM should explain the connection issue")
    print(f"and suggest the user try again or ask if they need help with something else.\n")
    
    print("3. GENERAL PLUGIN ERROR SCENARIO")
    print("-" * 50)
    general_error = {
        'error_type': 'plugin_error',
        'plugin_id': 'courtlistener',
        'message': 'Plugin courtlistener execution failed: Invalid API key',
        'error_details': 'Invalid API key',
        'suggestion': 'This plugin encountered an unexpected error.'
    }
    
    general_prompt = llm_protocol.create_plugin_error_prompt(
        'courtlistener', general_error, "Find cases about copyright fair use"
    )
    
    print(f"Original user request: 'Find cases about copyright fair use'")
    print(f"Plugin that failed: courtlistener (invalid API key)")
    print(f"\nPrompt sent to LLM for error handling:")
    print(general_prompt)
    print(f"\nExpected LLM behavior: The LLM should acknowledge the legal database issue")
    print(f"and provide general information about copyright fair use instead.\n")
    
    print("=== Key Benefits ===")
    print("✓ LLM can provide user-friendly error explanations")
    print("✓ LLM can try alternative approaches when plugins fail")
    print("✓ Users see helpful responses instead of raw technical errors")
    print("✓ System gracefully degrades when external services are unavailable")
    print("✓ LLM maintains conversational flow even when plugins fail")

def demo_successful_vs_error_flow():
    """Compare successful plugin flow vs error handling flow"""
    print("\n" + "="*70)
    print("COMPARISON: Successful Plugin Flow vs Error Handling Flow")
    print("="*70)
    
    llm_protocol = LLMProtocol()
    
    print("\nSUCCESSFUL PLUGIN FLOW:")
    print("-" * 30)
    success_result = {
        'results': [
            'New breakthrough in quantum computing achieved by Google',
            'OpenAI releases GPT-5 with enhanced reasoning capabilities',
            'Microsoft announces AI integration across all Office products'
        ],
        'total_results': 3,
        'search_time': 0.85
    }
    
    success_prompt = llm_protocol.create_plugin_result_prompt(
        'brave-search', success_result, "What are the latest AI developments?"
    )
    
    print("User asks: 'What are the latest AI developments?'")
    print("→ LLM invokes brave-search plugin")
    print("→ Plugin returns successful results")
    print("→ LLM receives this prompt:")
    print(f"\n{success_prompt}")
    print("\n→ LLM uses the results to provide a comprehensive answer")
    
    print("\nERROR HANDLING FLOW:")
    print("-" * 25)
    error_details = {
        'error_type': 'timeout',
        'plugin_id': 'brave-search',
        'message': 'Plugin brave-search processing timed out after 30 seconds.',
        'timeout_duration': 30
    }
    
    error_prompt = llm_protocol.create_plugin_error_prompt(
        'brave-search', error_details, "What are the latest AI developments?"
    )
    
    print("User asks: 'What are the latest AI developments?'")
    print("→ LLM invokes brave-search plugin")
    print("→ Plugin times out or fails")
    print("→ Instead of showing error to user, LLM receives this prompt:")
    print(f"\n{error_prompt}")
    print("\n→ LLM gracefully handles the error and provides helpful response")
    
    print("\nRESULT:")
    print("• User never sees technical error messages")
    print("• LLM maintains helpful, conversational tone")
    print("• System provides value even when external services fail")

if __name__ == "__main__":
    demo_error_prompts()
    demo_successful_vs_error_flow()
    print(f"\n{'='*70}")
    print("Demo completed! The plugin error propagation system allows")
    print("the LLM to handle failures gracefully and maintain a good user experience.")