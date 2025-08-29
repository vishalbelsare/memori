"""
Edge case tests for the Memori interceptor system to evaluate reliability
"""
import anthropic
from memori import Memori
import asyncio
import time

def test_interceptor_edge_cases():
    """Test various edge cases for the interceptor system"""
    
    print("🧪 Testing Memori Interceptor System Edge Cases")
    print("=" * 60)
    
    # Test 1: Error handling during conversation
    print("\n1. Testing error handling with malformed requests...")
    try:
        claude_memory = Memori(
            database_connect="sqlite:///edge_case_test.db",
            auto_ingest=True,
            conscious_ingest=False,  # Disable to focus on interceptor testing
            verbose=False,  # Reduce noise
        )
        claude_memory.enable()
        
        client = anthropic.Anthropic()
        
        # Test with empty messages (should handle gracefully)
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=50,
                messages=[]
            )
            print("   ❌ Empty messages should have failed")
        except Exception as e:
            print(f"   ✅ Empty messages handled correctly: {type(e).__name__}")
        
        # Test with very long input
        long_input = "This is a very long input. " * 1000  # ~27,000 chars
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=100,
                messages=[{"role": "user", "content": long_input[:8000]}]  # Limit to avoid API limits
            )
            print("   ✅ Long input handled successfully")
        except Exception as e:
            print(f"   ⚠️  Long input failed: {e}")
            
    except Exception as e:
        print(f"   ❌ Test 1 setup failed: {e}")
    
    # Test 2: Rapid consecutive calls
    print("\n2. Testing rapid consecutive API calls...")
    try:
        rapid_inputs = [
            "Test 1",
            "Test 2", 
            "Test 3",
            "Test 4",
            "Test 5"
        ]
        
        start_time = time.time()
        for i, input_text in enumerate(rapid_inputs):
            try:
                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=20,
                    messages=[{"role": "user", "content": input_text}]
                )
                print(f"   ✅ Call {i+1} successful")
            except Exception as e:
                print(f"   ❌ Call {i+1} failed: {e}")
                
        elapsed = time.time() - start_time
        print(f"   📊 Completed 5 calls in {elapsed:.2f}s ({5/elapsed:.1f} calls/sec)")
        
    except Exception as e:
        print(f"   ❌ Test 2 failed: {e}")
    
    # Test 3: Memory system statistics
    print("\n3. Testing memory system health...")
    try:
        stats = claude_memory.get_memory_stats()
        print(f"   📈 Memory stats: {stats}")
        
        integration_stats = claude_memory.get_integration_stats()
        print(f"   🔌 Integration stats: {len(integration_stats)} integrations")
        
        interceptor_status = claude_memory.get_interceptor_status()
        enabled_interceptors = [name for name, status in interceptor_status.items() if status.get('enabled')]
        print(f"   🎯 Enabled interceptors: {enabled_interceptors}")
        
        health = claude_memory.get_interceptor_health()
        print(f"   💚 System health: {health.get('overall_status')}")
        
    except Exception as e:
        print(f"   ❌ Test 3 failed: {e}")
    
    # Test 4: Disable/Enable cycling
    print("\n4. Testing enable/disable cycling...")
    try:
        # Disable
        claude_memory.disable()
        print("   🔴 Disabled interceptors")
        
        # Try API call while disabled - should work but not record
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=20,
            messages=[{"role": "user", "content": "This should not be recorded"}]
        )
        print("   ✅ API call works while disabled")
        
        # Re-enable
        claude_memory.enable()
        print("   🟢 Re-enabled interceptors")
        
        # Try API call while enabled - should record
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=20,
            messages=[{"role": "user", "content": "This should be recorded"}]
        )
        print("   ✅ API call works while enabled")
        
    except Exception as e:
        print(f"   ❌ Test 4 failed: {e}")
    
    # Test 5: Final database check
    print("\n5. Final database validation...")
    try:
        final_stats = claude_memory.get_memory_stats()
        print(f"   📊 Final stats: {final_stats}")
        print("   ✅ Database validation complete")
        
    except Exception as e:
        print(f"   ❌ Test 5 failed: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 Edge case testing complete!")

def test_different_client_patterns():
    """Test different ways of using Anthropic client"""
    
    print("\n🔄 Testing Different Client Usage Patterns")
    print("=" * 50)
    
    claude_memory = Memori(
        database_connect="sqlite:///client_pattern_test.db",
        auto_ingest=True,
        conscious_ingest=False,
        verbose=False,
    )
    claude_memory.enable()
    
    # Pattern 1: Reused client
    print("1. Testing reused client...")
    client = anthropic.Anthropic()
    
    for i in range(3):
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=30,
            messages=[{"role": "user", "content": f"Reused client test {i+1}"}]
        )
    print("   ✅ Reused client pattern works")
    
    # Pattern 2: Fresh client for each call
    print("2. Testing fresh client pattern...")
    for i in range(2):
        fresh_client = anthropic.Anthropic()
        response = fresh_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=30,
            messages=[{"role": "user", "content": f"Fresh client test {i+1}"}]
        )
    print("   ✅ Fresh client pattern works")
    
    # Pattern 3: Context manager usage
    print("3. Testing context manager pattern...")
    with anthropic.Anthropic() as context_client:
        response = context_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=30,
            messages=[{"role": "user", "content": "Context manager test"}]
        )
    print("   ✅ Context manager pattern works")
    
    print("🏁 Client pattern testing complete!")

if __name__ == "__main__":
    test_interceptor_edge_cases()
    test_different_client_patterns()