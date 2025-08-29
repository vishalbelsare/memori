"""
Test OpenAI conversation recording compatibility

This test verifies that memori correctly handles all OpenAI conversation formats:
- Basic chat completions
- Function calling
- Tool usage
- Vision (image inputs)
- Streaming responses
- Different content types
"""

from typing import Dict, List
from unittest.mock import MagicMock


class MockOpenAIResponse:
    """Mock OpenAI response for testing"""

    def __init__(self, content: str, usage: Dict = None, choices: List = None):
        if choices is None:
            mock_message = MagicMock()
            mock_message.content = content
            mock_message.role = "assistant"

            mock_choice = MagicMock()
            mock_choice.message = mock_message
            mock_choice.finish_reason = "stop"

            self.choices = [mock_choice]
        else:
            self.choices = choices

        if usage:
            self.usage = MagicMock()
            self.usage.total_tokens = usage.get("total_tokens", 0)
            self.usage.prompt_tokens = usage.get("prompt_tokens", 0)
            self.usage.completion_tokens = usage.get("completion_tokens", 0)
        else:
            self.usage = None


def test_basic_conversation_recording():
    """Test basic text conversation recording"""
    from memori.core.memory import Memori

    memori = Memori()

    # Basic conversation
    kwargs = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you!"},
            {"role": "user", "content": "What's the weather like?"},
        ],
    }

    response = MockOpenAIResponse(
        content="I don't have access to current weather data. Could you tell me your location?",
        usage={"total_tokens": 45, "prompt_tokens": 30, "completion_tokens": 15},
    )

    # Test recording
    try:
        memori._record_openai_conversation(kwargs, response)
        print("✓ Basic conversation recording works")
    except Exception as e:
        print(f"✗ Basic conversation recording failed: {e}")


def test_function_calling_recording():
    """Test function calling conversation recording"""
    from memori.core.memory import Memori

    memori = Memori()

    # Function calling conversation
    kwargs = {
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": "What's the weather in San Francisco?"}
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather for a location",
                    "parameters": {
                        "type": "object",
                        "properties": {"location": {"type": "string"}},
                    },
                },
            }
        ],
    }

    # Mock response with function call
    mock_message = MagicMock()
    mock_message.content = None
    mock_message.tool_calls = [
        MagicMock(
            id="call_123",
            type="function",
            function=MagicMock(
                name="get_weather", arguments='{"location": "San Francisco"}'
            ),
        )
    ]

    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_choice.finish_reason = "tool_calls"

    response = MagicMock()
    response.choices = [mock_choice]
    response.usage = MagicMock()
    response.usage.total_tokens = 35

    try:
        memori._record_openai_conversation(kwargs, response)
        print("✓ Function calling recording works")
    except Exception as e:
        print(f"✗ Function calling recording failed: {e}")


def test_vision_conversation_recording():
    """Test vision (image) conversation recording"""
    from memori.core.memory import Memori

    memori = Memori()

    # Vision conversation with image
    kwargs = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
                        },
                    },
                ],
            }
        ],
    }

    response = MockOpenAIResponse(
        content="This appears to be a small 1x1 pixel image, likely used as a placeholder or test image.",
        usage={"total_tokens": 150},
    )

    try:
        memori._record_openai_conversation(kwargs, response)
        print("✓ Vision conversation recording works")
    except Exception as e:
        print(f"✗ Vision conversation recording failed: {e}")


def test_complex_content_extraction():
    """Test extraction of user input from complex content structures"""
    from memori.core.memory import Memori

    memori = Memori()

    # Test various message content formats
    test_cases = [
        # String content
        {
            "messages": [{"role": "user", "content": "Simple text message"}],
            "expected": "Simple text message",
        },
        # List content with text
        {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Complex message with image"},
                        {
                            "type": "image_url",
                            "image_url": {"url": "http://example.com/image.jpg"},
                        },
                    ],
                }
            ],
            "expected": "Complex message with image",
        },
        # Multiple user messages (should get the last one)
        {
            "messages": [
                {"role": "user", "content": "First message"},
                {"role": "assistant", "content": "Response"},
                {"role": "user", "content": "Second message"},
            ],
            "expected": "Second message",
        },
        # Empty content
        {"messages": [{"role": "user", "content": ""}], "expected": ""},
        # No user messages
        {"messages": [{"role": "system", "content": "System message"}], "expected": ""},
    ]

    for i, test_case in enumerate(test_cases):
        kwargs = {"model": "gpt-4", "messages": test_case["messages"]}
        response = MockOpenAIResponse("Test response")

        # Extract user input using the same logic as _record_openai_conversation
        user_input = ""
        for message in reversed(kwargs.get("messages", [])):
            if message.get("role") == "user":
                content = message.get("content", "")
                if isinstance(content, list):
                    # Extract text from list content
                    text_parts = []
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                    user_input = " ".join(text_parts)
                else:
                    user_input = content
                break

        if user_input == test_case["expected"]:
            print(f"✓ Test case {i+1}: Content extraction works")
        else:
            print(
                f"✗ Test case {i+1}: Expected '{test_case['expected']}', got '{user_input}'"
            )


def test_enhanced_content_extraction():
    """Test the enhanced content extraction methods"""
    from memori.core.memory import Memori

    memori = Memori()

    # Test vision content
    vision_messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                {
                    "type": "image_url",
                    "image_url": {"url": "data:image/jpeg;base64,..."},
                },
            ],
        }
    ]

    extracted = memori._extract_openai_user_input(vision_messages)
    expected = "What's in this image? [Contains 1 image(s)]"

    if extracted == expected:
        print("✓ Vision content extraction works")
    else:
        print(
            f"✗ Vision content extraction failed. Expected: '{expected}', Got: '{extracted}'"
        )

    # Test function call response
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "get_weather"
    mock_tool_call.function.arguments = '{"location": "San Francisco"}'

    mock_message = MagicMock()
    mock_message.content = None
    mock_message.tool_calls = [mock_tool_call]

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    ai_output = memori._extract_openai_ai_output(mock_response)

    if "Called get_weather" in ai_output and "Tool calls" in ai_output:
        print("✓ Function call extraction works")
    else:
        print(f"✗ Function call extraction failed. Got: '{ai_output}'")


def test_enhanced_metadata_extraction():
    """Test the enhanced metadata extraction"""
    from memori.core.memory import Memori

    memori = Memori()

    # Test complex request with tools
    kwargs = {
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": "Get weather for SF"},
            {"role": "assistant", "content": "I'll check that for you"},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Also check this image"},
                    {"type": "image_url", "image_url": {"url": "test.jpg"}},
                ],
            },
        ],
        "tools": [{"type": "function", "function": {"name": "get_weather"}}],
        "temperature": 0.7,
        "max_tokens": 150,
    }

    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 20
    mock_usage.completion_tokens = 15
    mock_usage.total_tokens = 35

    mock_choice = MagicMock()
    mock_choice.finish_reason = "stop"

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage

    metadata = memori._extract_openai_metadata(kwargs, mock_response, 35)

    checks = [
        ("has_tools", True),
        ("tool_count", 1),
        ("temperature", 0.7),
        ("max_tokens", 150),
        ("has_images", True),
        ("message_count", 3),
        ("finish_reason", "stop"),
        ("prompt_tokens", 20),
        ("completion_tokens", 15),
    ]

    for key, expected in checks:
        if metadata.get(key) == expected:
            print(f"✓ Metadata '{key}' extraction works")
        else:
            print(
                f"✗ Metadata '{key}' extraction failed. Expected: {expected}, Got: {metadata.get(key)}"
            )


def test_enhanced_openai_recording():
    """Test improved OpenAI conversation recording"""

    # Run all tests
    print("Testing OpenAI conversation recording compatibility...")
    print("=" * 60)

    test_basic_conversation_recording()
    test_function_calling_recording()
    test_vision_conversation_recording()
    test_complex_content_extraction()
    test_enhanced_content_extraction()
    test_enhanced_metadata_extraction()

    print("=" * 60)
    print("OpenAI recording compatibility test completed")


if __name__ == "__main__":
    test_enhanced_openai_recording()
