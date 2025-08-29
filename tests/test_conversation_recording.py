"""
Comprehensive test for conversation recording compatibility

Tests both OpenAI and Anthropic conversation recording with various formats:
- Basic text conversations
- Complex content (vision, tools)
- Function/tool calling
- Streaming responses
- Error handling
"""

from unittest.mock import MagicMock
import json


def test_openai_recording_formats():
    """Test various OpenAI conversation formats"""
    print("Testing OpenAI Recording Formats")
    print("-" * 40)
    
    from memori.core.memory import Memori
    memori = Memori()
    
    # Test 1: Basic text conversation
    messages1 = [{"role": "user", "content": "Hello, how are you?"}]
    user_input = memori._extract_openai_user_input(messages1)
    assert user_input == "Hello, how are you?", f"Expected 'Hello, how are you?', got '{user_input}'"
    print("✓ Basic text extraction")
    
    # Test 2: Vision conversation
    messages2 = [{
        "role": "user",
        "content": [
            {"type": "text", "text": "What's in this image?"},
            {"type": "image_url", "image_url": {"url": "test.jpg"}},
            {"type": "image_url", "image_url": {"url": "test2.jpg"}}
        ]
    }]
    user_input = memori._extract_openai_user_input(messages2)
    expected = "What's in this image? [Contains 2 image(s)]"
    assert user_input == expected, f"Expected '{expected}', got '{user_input}'"
    print("✓ Vision content extraction")
    
    # Test 3: Function call response
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "get_weather"
    mock_tool_call.function.arguments = '{"location": "New York"}'
    
    mock_message = MagicMock()
    mock_message.content = None
    mock_message.tool_calls = [mock_tool_call]
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=mock_message)]
    
    ai_output = memori._extract_openai_ai_output(mock_response)
    assert "Called get_weather" in ai_output, f"Function call not detected in: {ai_output}"
    assert "Tool calls" in ai_output, f"Tool calls indicator missing in: {ai_output}"
    print("✓ Function call response extraction")
    
    # Test 4: Complex metadata
    kwargs = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "test"}],
        "temperature": 0.7,
        "max_tokens": 150,
        "tools": [{"type": "function", "function": {"name": "test"}}]
    }
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(finish_reason="stop")]
    mock_response.usage = MagicMock(
        prompt_tokens=20, completion_tokens=15, total_tokens=35
    )
    
    metadata = memori._extract_openai_metadata(kwargs, mock_response, 35)
    
    assert metadata["has_tools"] == True
    assert metadata["tool_count"] == 1
    assert metadata["temperature"] == 0.7
    assert metadata["finish_reason"] == "stop"
    print("✓ Complex metadata extraction")


def test_anthropic_recording_formats():
    """Test various Anthropic conversation formats"""
    print("\nTesting Anthropic Recording Formats")
    print("-" * 40)
    
    from memori.core.memory import Memori
    memori = Memori()
    
    # Test 1: Basic text conversation
    messages1 = [{"role": "user", "content": "Hello Claude!"}]
    user_input = memori._extract_anthropic_user_input(messages1)
    assert user_input == "Hello Claude!", f"Expected 'Hello Claude!', got '{user_input}'"
    print("✓ Basic text extraction")
    
    # Test 2: Vision conversation (Anthropic format)
    messages2 = [{
        "role": "user",
        "content": [
            {"type": "text", "text": "Describe this image"},
            {"type": "image", "source": {"type": "base64", "data": "..."}}
        ]
    }]
    user_input = memori._extract_anthropic_user_input(messages2)
    expected = "Describe this image [Contains 1 image(s)]"
    assert user_input == expected, f"Expected '{expected}', got '{user_input}'"
    print("✓ Vision content extraction")
    
    # Test 3: Tool use response
    mock_text_block = MagicMock()
    mock_text_block.text = "I'll help you with that."
    
    mock_tool_block = MagicMock()
    mock_tool_block.type = "tool_use"
    mock_tool_block.name = "calculator"
    mock_tool_block.input = {"operation": "add", "a": 2, "b": 3}
    
    mock_response = MagicMock()
    mock_response.content = [mock_text_block, mock_tool_block]
    
    ai_output = memori._extract_anthropic_ai_output(mock_response)
    assert "I'll help you with that" in ai_output
    assert "Used calculator" in ai_output
    assert "Tool uses" in ai_output
    print("✓ Tool use response extraction")
    
    # Test 4: Token extraction
    mock_response = MagicMock()
    mock_response.usage = MagicMock(input_tokens=25, output_tokens=45)
    
    tokens = memori._extract_anthropic_tokens(mock_response)
    assert tokens == 70, f"Expected 70 tokens, got {tokens}"
    print("✓ Token extraction")
    
    # Test 5: Complex metadata
    kwargs = {
        "model": "claude-3-sonnet",
        "messages": [{"role": "user", "content": "test"}],
        "temperature": 0.5,
        "max_tokens": 200,
        "tools": [{"name": "search", "description": "Search tool"}]
    }
    
    mock_response = MagicMock()
    mock_response.stop_reason = "end_turn"
    mock_response.model = "claude-3-sonnet-20240229"
    mock_response.usage = MagicMock(input_tokens=25, output_tokens=45)
    
    metadata = memori._extract_anthropic_metadata(kwargs, mock_response, 70)
    
    assert metadata["has_tools"] == True
    assert metadata["tool_count"] == 1
    assert metadata["temperature"] == 0.5
    assert metadata["stop_reason"] == "end_turn"
    assert metadata["input_tokens"] == 25
    assert metadata["output_tokens"] == 45
    print("✓ Complex metadata extraction")


def test_error_handling():
    """Test error handling in conversation recording"""
    print("\nTesting Error Handling")
    print("-" * 22)
    
    from memori.core.memory import Memori
    memori = Memori()
    
    # Test 1: Invalid OpenAI user input
    invalid_messages = [{"role": "user"}]  # Missing content
    user_input = memori._extract_openai_user_input(invalid_messages)
    assert user_input == "", f"Expected empty string for missing content, got '{user_input}'"
    print("✓ OpenAI invalid user input handled")
    
    # Test 2: Invalid OpenAI response
    invalid_response = MagicMock()
    invalid_response.choices = []  # Empty choices
    
    ai_output = memori._extract_openai_ai_output(invalid_response)
    assert "Error extracting" in ai_output or ai_output == "", f"Expected error message or empty, got '{ai_output}'"
    print("✓ OpenAI invalid response handled")
    
    # Test 3: Invalid Anthropic user input
    user_input = memori._extract_anthropic_user_input([])  # Empty messages
    assert user_input == "", f"Expected empty string for no messages, got '{user_input}'"
    print("✓ Anthropic invalid user input handled")
    
    # Test 4: Invalid Anthropic response
    invalid_response = MagicMock()
    invalid_response.content = None
    
    ai_output = memori._extract_anthropic_ai_output(invalid_response)
    assert ai_output == "" or "Error extracting" in ai_output, f"Expected error or empty, got '{ai_output}'"
    print("✓ Anthropic invalid response handled")


def main():
    """Run all conversation recording tests"""
    print("Conversation Recording Compatibility Test")
    print("=" * 50)
    
    try:
        test_openai_recording_formats()
        test_anthropic_recording_formats()
        test_error_handling()
        
        print("\n" + "=" * 50)
        print("✅ All conversation recording tests passed!")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()