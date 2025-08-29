"""
Example script demonstrating different provider configurations for Memori

This shows how to use OpenAI, Azure, and custom endpoints with the new provider abstraction.
"""

from memori.core import Memori, ProviderConfig

# Example 1: Standard OpenAI configuration
print("Example 1: Standard OpenAI")
memori_openai = Memori(
    api_key="your-openai-key",
    model="gpt-4-turbo",  # Optional: specify model
    conscious_ingest=True,
)
print(f"Provider: {memori_openai.provider_config.api_type}")
print(
    f"Model: {memori_openai.memory_agent.model if memori_openai.memory_agent else 'N/A'}"
)
print()

# Example 2: Azure OpenAI configuration
print("Example 2: Azure OpenAI")
memori_azure = Memori(
    api_type="azure",
    api_key="your-azure-key",
    azure_endpoint="https://your-resource.openai.azure.com",
    azure_deployment="your-deployment",
    api_version="2024-02-01",
    model="gpt-4",  # Optional: specify model
    conscious_ingest=True,
)
print(f"Provider: {memori_azure.provider_config.api_type}")
print(f"Azure endpoint: {memori_azure.provider_config.azure_endpoint}")
print(
    f"Model: {memori_azure.memory_agent.model if memori_azure.memory_agent else 'N/A'}"
)
print()

# Example 3: Custom OpenAI-compatible endpoint (e.g., local LLM, Ollama, etc.)
print("Example 3: Custom endpoint")
memori_custom = Memori(
    api_type="custom",
    base_url="http://localhost:11434/v1",  # Example: Ollama endpoint
    api_key="not-needed",  # Some endpoints don't need keys
    model="llama2",  # Custom model name
    conscious_ingest=True,
)
print(f"Provider: {memori_custom.provider_config.api_type}")
print(f"Base URL: {memori_custom.provider_config.base_url}")
print(
    f"Model: {memori_custom.memory_agent.model if memori_custom.memory_agent else 'N/A'}"
)
print()

# Example 4: Using ProviderConfig directly
print("Example 4: Using ProviderConfig")
config = ProviderConfig.from_azure(
    api_key="your-key",
    azure_endpoint="https://your-resource.openai.azure.com",
    azure_deployment="gpt-4",
    api_version="2024-02-01",
    model="gpt-4-32k",  # Specify Azure model
)
memori_with_config = Memori(provider_config=config, conscious_ingest=True)
print(f"Provider: {memori_with_config.provider_config.api_type}")
print(
    f"Model: {memori_with_config.memory_agent.model if memori_with_config.memory_agent else 'N/A'}"
)
print()

# Example 5: Environment detection (when env vars are set)
print("Example 5: Auto-detect from environment")
# This will detect from environment variables:
# - OPENAI_API_KEY
# - AZURE_OPENAI_ENDPOINT (for Azure)
# - OPENAI_BASE_URL (for custom)
# - OPENAI_MODEL or LLM_MODEL (for model)
memori_auto = Memori(conscious_ingest=True)
print(f"Provider: {memori_auto.provider_config.api_type or 'openai'}")
print(f"Model: {memori_auto.memory_agent.model if memori_auto.memory_agent else 'N/A'}")
print()

# Example 6: Model override - environment model can be overridden
print("Example 6: Override environment model")
# Even if OPENAI_MODEL is set in environment, this will override it
memori_override = Memori(
    model="claude-3-opus", conscious_ingest=True  # Override environment model
)
print(
    f"Model from parameter: {memori_override.memory_agent.model if memori_override.memory_agent else 'N/A'}"
)
