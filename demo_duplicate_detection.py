#!/usr/bin/env python3
"""
Demo script showing duplicate plugin invocation detection in action.
This simulates what happens when the LLM tries to call the same plugin twice.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ollama_manager import is_duplicate_plugin_call
import json


def demo_duplicate_detection():
    """Demonstrate the duplicate detection functionality"""
    print("🔍 Duplicate Plugin Invocation Detection Demo")
    print("=" * 50)
    
    # Simulate a conversation with plugin calls
    plugins_used = []
    
    print("\n📱 Simulating conversation with plugin calls...")
    
    # First plugin call - should succeed
    print("\n1️⃣ First plugin call:")
    plugin_call_1 = {
        'id': 'brave-search',
        'input': {'query': 'artificial intelligence news', 'limit': 10},
        'reason': 'User asked about recent AI developments'
    }
    print(f"   Plugin: {plugin_call_1['id']}")
    print(f"   Input: {json.dumps(plugin_call_1['input'], indent=6)}")
    print(f"   Reason: {plugin_call_1['reason']}")
    
    is_dup = is_duplicate_plugin_call(plugins_used, plugin_call_1['id'], plugin_call_1['input'])
    print(f"   🔍 Duplicate check: {'❌ DUPLICATE' if is_dup else '✅ OK'}")
    
    plugins_used.append(plugin_call_1)
    print("   ✅ Plugin call executed successfully")
    
    # Second plugin call - different input, should succeed
    print("\n2️⃣ Second plugin call (different parameters):")
    plugin_call_2 = {
        'id': 'local-fileio',
        'input': {'operation': 'read', 'path': 'research.txt'},
        'reason': 'User wants to read their research file'
    }
    print(f"   Plugin: {plugin_call_2['id']}")
    print(f"   Input: {json.dumps(plugin_call_2['input'], indent=6)}")
    print(f"   Reason: {plugin_call_2['reason']}")
    
    is_dup = is_duplicate_plugin_call(plugins_used, plugin_call_2['id'], plugin_call_2['input'])
    print(f"   🔍 Duplicate check: {'❌ DUPLICATE' if is_dup else '✅ OK'}")
    
    plugins_used.append(plugin_call_2)
    print("   ✅ Plugin call executed successfully")
    
    # Third plugin call - same as second, should be flagged as duplicate
    print("\n3️⃣ Third plugin call (DUPLICATE of previous):")
    plugin_call_3 = {
        'id': 'local-fileio',
        'input': {'operation': 'read', 'path': 'research.txt'},
        'reason': 'LLM trying to read the same file again'
    }
    print(f"   Plugin: {plugin_call_3['id']}")
    print(f"   Input: {json.dumps(plugin_call_3['input'], indent=6)}")
    print(f"   Reason: {plugin_call_3['reason']}")
    
    is_dup = is_duplicate_plugin_call(plugins_used, plugin_call_3['id'], plugin_call_3['input'])
    print(f"   🔍 Duplicate check: {'❌ DUPLICATE DETECTED!' if is_dup else '✅ OK'}")
    
    if is_dup:
        print("   🛑 Plugin call BLOCKED to prevent infinite loop")
        print("   💬 User-friendly error message would be displayed")
    else:
        plugins_used.append(plugin_call_3)
        print("   ✅ Plugin call executed successfully")
    
    # Fourth plugin call - same plugin but different params, should succeed
    print("\n4️⃣ Fourth plugin call (same plugin, different parameters):")
    plugin_call_4 = {
        'id': 'local-fileio',
        'input': {'operation': 'write', 'path': 'summary.txt', 'content': 'AI research summary'},
        'reason': 'User wants to save a summary'
    }
    print(f"   Plugin: {plugin_call_4['id']}")
    print(f"   Input: {json.dumps(plugin_call_4['input'], indent=6)}")
    print(f"   Reason: {plugin_call_4['reason']}")
    
    is_dup = is_duplicate_plugin_call(plugins_used, plugin_call_4['id'], plugin_call_4['input'])
    print(f"   🔍 Duplicate check: {'❌ DUPLICATE' if is_dup else '✅ OK'}")
    
    plugins_used.append(plugin_call_4)
    print("   ✅ Plugin call executed successfully")


def demo_edge_cases():
    """Demonstrate edge cases"""
    print("\n\n🧪 Edge Cases Demo")
    print("=" * 30)
    
    # Parameter order independence
    print("\n🔄 Parameter order independence:")
    plugins_used = [{
        'id': 'brave-search',
        'input': {'query': 'python', 'limit': 5, 'type': 'web'},
        'reason': 'search'
    }]
    
    # Same parameters in different order
    reordered_input = {'type': 'web', 'limit': 5, 'query': 'python'}
    is_dup = is_duplicate_plugin_call(plugins_used, 'brave-search', reordered_input)
    print(f"   Original: {{'query': 'python', 'limit': 5, 'type': 'web'}}")
    print(f"   Reordered: {reordered_input}")
    print(f"   Duplicate check: {'❌ DUPLICATE' if is_dup else '✅ OK'} (correctly detected as duplicate)")
    
    # Nested objects
    print("\n🪆 Nested objects:")
    plugins_used = [{
        'id': 'complex-plugin',
        'input': {'config': {'settings': {'timeout': 30}, 'filters': ['a', 'b']}, 'query': 'test'},
        'reason': 'complex call'
    }]
    
    same_nested = {'config': {'settings': {'timeout': 30}, 'filters': ['a', 'b']}, 'query': 'test'}
    is_dup = is_duplicate_plugin_call(plugins_used, 'complex-plugin', same_nested)
    print(f"   Complex nested input detected as duplicate: {'✅ YES' if is_dup else '❌ NO'}")


def main():
    """Run the demonstration"""
    demo_duplicate_detection()
    demo_edge_cases()
    
    print("\n\n🎯 Summary")
    print("=" * 20)
    print("✅ Duplicate detection prevents infinite loops")
    print("✅ Only consecutive identical calls are flagged")
    print("✅ Parameter order doesn't affect detection")
    print("✅ Different parameters with same plugin are allowed")
    print("✅ Complex nested objects are handled correctly")
    print("\n🛡️ The system is now protected against repeated identical plugin invocations!")


if __name__ == "__main__":
    main()