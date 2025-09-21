#!/usr/bin/env python3
"""
Demonstration of Enhanced Plugin Usage Tracking

This script demonstrates the new plugin usage tracking capabilities
by simulating plugin invocations and showing the enhanced reporting.
"""

import sys
import os
import uuid
import time
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from plugin_usage_tracker import plugin_tracker
from ollama_manager import app


def simulate_plugin_session():
    """Simulate a realistic plugin usage session"""
    request_id = str(uuid.uuid4())
    print(f"🎯 Starting new request session: {request_id}")
    
    # Start tracking session
    plugin_tracker.start_request_session(request_id)
    
    # Simulate first plugin call - search
    print("  📡 Invoking brave-search plugin...")
    invocation1 = plugin_tracker.record_plugin_invocation(
        request_id,
        "brave-search",
        {"query": "latest artificial intelligence developments 2024"},
        "User requested information about recent AI developments"
    )
    
    # Simulate successful execution
    time.sleep(0.1)  # Simulate processing time
    plugin_tracker.update_invocation_result(
        request_id, invocation1.invocation_index, True,
        {
            "results": [
                {"title": "AI Breakthrough in 2024", "url": "https://example.com/ai-news"},
                {"title": "Machine Learning Advances", "url": "https://example.com/ml-news"}
            ],
            "total_results": 15
        },
        None, 125.5
    )
    print("    ✅ Search completed successfully (125.5ms)")
    
    # Simulate second plugin call - file save
    print("  💾 Invoking local-fileio plugin...")
    invocation2 = plugin_tracker.record_plugin_invocation(
        request_id,
        "local-fileio",
        {
            "operation": "write",
            "path": "ai_research_summary.md",
            "content": "# AI Research Summary\n\nLatest developments in AI..."
        },
        "Save research summary to file for user reference"
    )
    
    # Simulate failed execution
    time.sleep(0.05)  # Simulate processing time
    plugin_tracker.update_invocation_result(
        request_id, invocation2.invocation_index, False,
        None, "Permission denied: Cannot write to specified directory", 45.2
    )
    print("    ❌ File write failed (45.2ms): Permission denied")
    
    # Simulate third plugin call - alternative save location
    print("  💾 Invoking local-fileio plugin (retry)...")
    invocation3 = plugin_tracker.record_plugin_invocation(
        request_id,
        "local-fileio",
        {
            "operation": "write",
            "path": "/tmp/ai_research_summary.md",
            "content": "# AI Research Summary\n\nLatest developments in AI..."
        },
        "Retry saving to alternative location after permission error"
    )
    
    # Simulate successful execution
    time.sleep(0.03)  # Simulate processing time
    plugin_tracker.update_invocation_result(
        request_id, invocation3.invocation_index, True,
        {"file_size": 2048, "path": "/tmp/ai_research_summary.md"},
        None, 32.1
    )
    print("    ✅ File saved successfully (32.1ms)")
    
    return request_id


def demonstrate_duplicate_detection():
    """Demonstrate the enhanced duplicate detection"""
    print("\n🔍 Demonstrating duplicate detection...")
    
    request_id = str(uuid.uuid4())
    plugin_tracker.start_request_session(request_id)
    
    # First call
    plugin_tracker.record_plugin_invocation(
        request_id, "brave-search", {"query": "test search"}, "First search"
    )
    print("  📡 First search call recorded")
    
    # Test duplicate detection
    from ollama_manager import is_duplicate_plugin_call
    
    # This should be detected as duplicate
    is_dup = is_duplicate_plugin_call(request_id, "brave-search", {"query": "test search"})
    print(f"  🔄 Consecutive duplicate check: {is_dup} (should be True)")
    
    # This should NOT be detected as duplicate (different parameters)
    is_dup = is_duplicate_plugin_call(request_id, "brave-search", {"query": "different search"})
    print(f"  🆕 Different parameters check: {is_dup} (should be False)")
    
    # Add the different call
    plugin_tracker.record_plugin_invocation(
        request_id, "brave-search", {"query": "different search"}, "Different search"
    )
    
    # Now the original should NOT be duplicate (not consecutive)
    is_dup = is_duplicate_plugin_call(request_id, "brave-search", {"query": "test search"})
    print(f"  🚫 Non-consecutive duplicate check: {is_dup} (should be False)")


def show_session_analytics(request_id):
    """Display detailed session analytics"""
    print(f"\n📊 Session Analytics for {request_id}:")
    
    # Get detailed session information
    plugins_used = plugin_tracker.get_plugins_used_list(request_id)
    session_summary = plugin_tracker.get_session_summary(request_id)
    
    if not plugins_used:
        print("  ⚠️  Session not found or has been archived")
        return
    
    print(f"  Total invocations: {len(plugins_used)}")
    print(f"  Unique plugins: {session_summary['unique_plugins']}")
    
    if session_summary['session_start_time'] and session_summary['session_end_time']:
        duration = session_summary['session_end_time'] - session_summary['session_start_time']
        print(f"  Session duration: {duration:.2f}s")
    
    print("\n  📋 Detailed invocations:")
    for i, plugin in enumerate(plugins_used):
        status = "✅" if plugin['success'] else "❌"
        print(f"    {i+1}. {status} {plugin['id']}")
        print(f"       Reason: {plugin['reason']}")
        print(f"       Input: {json.dumps(plugin['input'], indent=8)}")
        print(f"       Time: {time.strftime('%H:%M:%S', time.localtime(plugin['timestamp']))}")
        print()


def test_api_endpoints():
    """Test the enhanced API endpoints"""
    print("\n🌐 Testing enhanced API endpoints...")
    
    with app.test_client() as client:
        # Test enhanced plugins accessed endpoint
        response = client.get('/api/plugins/accessed')
        data = response.get_json()
        
        print(f"  📊 /api/plugins/accessed response:")
        print(f"    Active request: {data.get('request_id', 'None')}")
        print(f"    Plugins used: {len(data.get('plugins_used', []))}")
        print(f"    Legacy format: {data.get('plugins', [])}")
        
        # Test new usage analytics endpoint
        response = client.get('/api/plugins/usage')
        data = response.get_json()
        
        if data['success']:
            analytics = data['analytics']
            print(f"\n  📈 /api/plugins/usage analytics:")
            print(f"    Total sessions: {analytics['total_sessions']}")
            print(f"    Total invocations: {analytics['total_invocations']}")
            print(f"    Average per session: {analytics['average_invocations_per_session']:.2f}")
            
            if analytics['most_used_plugins']:
                print(f"    Most used plugins:")
                for plugin, count in analytics['most_used_plugins']:
                    print(f"      - {plugin}: {count} times")


def main():
    """Main demonstration function"""
    print("🚀 Enhanced Plugin Usage Tracking Demonstration")
    print("=" * 55)
    
    # Simulate several plugin sessions
    session_ids = []
    
    print("\n1️⃣ Simulating realistic plugin usage sessions...")
    for i in range(3):
        print(f"\n--- Session {i+1} ---")
        session_id = simulate_plugin_session()
        session_ids.append(session_id)
        
        # Archive session by starting a new one (except for the last)
        if i < 2:
            plugin_tracker.start_request_session(str(uuid.uuid4()))
    
    # Demonstrate duplicate detection
    demonstrate_duplicate_detection()
    
    # Show detailed analytics for the current active session
    active_session_id = plugin_tracker.get_active_request_id()
    if active_session_id:
        show_session_analytics(active_session_id)
    else:
        print("\n📊 No active session - showing recent sessions in API test")
    
    # Test API endpoints
    test_api_endpoints()
    
    print("\n🎉 Demonstration completed!")
    print("\nKey improvements demonstrated:")
    print("✅ Thread-safe request-scoped tracking")
    print("✅ Detailed invocation metadata (timestamps, results, timing)")
    print("✅ Enhanced duplicate detection")
    print("✅ Comprehensive session analytics")
    print("✅ Enhanced API endpoints with backward compatibility")
    print("✅ Performance monitoring and success/failure tracking")


if __name__ == "__main__":
    main()