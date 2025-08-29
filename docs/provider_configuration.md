# Provider Configuration Guide

Memori now supports multiple LLM providers including OpenAI, Azure OpenAI, and custom OpenAI-compatible endpoints.

## Quick Start

### Standard OpenAI
```python
from memori.core import Memori

# Simple configuration
memori = Memori(
    api_key="your-openai-key",
    model="gpt-4-turbo"  # Optional, defaults to gpt-4o
)
```

### Azure OpenAI
```python
memori = Memori(
    api_type="azure",
    api_key="your-azure-key",
    azure_endpoint="https://your-resource.openai.azure.com",
    azure_deployment="your-deployment",
    api_version="2024-02-01",
    model="gpt-4"  # Optional
)
```

### Custom Endpoints (Ollama, LocalAI, etc.)
```python
memori = Memori(
    api_type="custom",
    base_url="http://localhost:11434/v1",
    api_key="optional-key",
    model="llama2"
)
```

## Configuration Methods

### 1. Direct Parameters
Pass configuration directly to Memori constructor:
```python
memori = Memori(
    api_key="key",
    model="gpt-4-turbo",
    organization="org-id",
    project="project-id"
)
```

### 2. Environment Variables
Set environment variables and Memori will auto-detect:
```bash
# OpenAI
export OPENAI_API_KEY="your-key"
export OPENAI_MODEL="gpt-4-turbo"  # or LLM_MODEL
export OPENAI_ORGANIZATION="org-id"
export OPENAI_PROJECT="project-id"

# Azure
export AZURE_OPENAI_ENDPOINT="https://your.openai.azure.com"
export AZURE_OPENAI_API_KEY="your-key"
export AZURE_OPENAI_DEPLOYMENT="deployment-name"
export OPENAI_API_VERSION="2024-02-01"

# Custom endpoint
export OPENAI_BASE_URL="http://localhost:11434/v1"
export OPENAI_API_KEY="your-key"
```

Then initialize without parameters:
```python
memori = Memori()  # Auto-detects from environment
```

### 3. Provider Config Object
Use ProviderConfig for advanced configuration:
```python
from memori.core import ProviderConfig

# Create config
config = ProviderConfig.from_azure(
    api_key="key",
    azure_endpoint="https://your.openai.azure.com",
    azure_deployment="gpt-4",
    model="gpt-4-32k"
)

# Use with Memori
memori = Memori(provider_config=config)
```

## Model Configuration

### Priority Order
Model selection follows this priority (highest to lowest):
1. Direct `model` parameter to Memori()
2. Model in `provider_config` if provided
3. Environment variable (`OPENAI_MODEL` or `LLM_MODEL`)
4. Default: `"gpt-4o"`

### Examples
```python
# Method 1: Direct parameter (highest priority)
memori = Memori(model="gpt-3.5-turbo")

# Method 2: Via environment
# export OPENAI_MODEL="gpt-4-turbo"
memori = Memori()  # Uses gpt-4-turbo from env

# Method 3: Override environment
# Even if OPENAI_MODEL is set, this overrides it
memori = Memori(model="claude-3-opus")

# Method 4: Default fallback
memori = Memori()  # Uses gpt-4o if no model specified
```

## Available Parameters

### Common Parameters
- `api_key`: API key for authentication
- `model`: Model to use (e.g., "gpt-4", "gpt-3.5-turbo")
- `api_type`: Provider type ("openai", "azure", "custom")
- `base_url`: Custom endpoint URL
- `timeout`: Request timeout in seconds
- `max_retries`: Maximum retry attempts

### OpenAI-Specific
- `organization`: Organization ID
- `project`: Project ID

### Azure-Specific
- `azure_endpoint`: Azure OpenAI endpoint URL
- `azure_deployment`: Deployment name
- `api_version`: API version (e.g., "2024-02-01")
- `azure_ad_token`: Azure AD token for authentication

## Advanced Usage

### Multiple Providers
```python
# Create different Memori instances with different providers
openai_memori = Memori(
    api_key="openai-key",
    model="gpt-4"
)

azure_memori = Memori(
    api_type="azure",
    azure_endpoint="https://azure.openai.azure.com",
    api_key="azure-key",
    model="gpt-4"
)

local_memori = Memori(
    api_type="custom",
    base_url="http://localhost:8080/v1",
    model="local-llm"
)
```

### Custom Headers and Query Parameters
```python
config = ProviderConfig(
    api_key="key",
    base_url="https://custom-api.com",
    default_headers={"X-Custom-Header": "value"},
    default_query={"custom_param": "value"}
)

memori = Memori(provider_config=config)
```

## Backward Compatibility

The old `openai_api_key` parameter is still supported for backward compatibility:
```python
# Old way (still works)
memori = Memori(openai_api_key="your-key")

# New way (recommended)
memori = Memori(api_key="your-key")
```

## Troubleshooting

### Check Current Configuration
```python
memori = Memori(api_key="key", model="gpt-4")

# Check provider type
print(f"Provider: {memori.provider_config.api_type}")

# Check model being used
if memori.memory_agent:
    print(f"Model: {memori.memory_agent.model}")

# Check full configuration
print(f"Config: {memori.provider_config.get_openai_client_kwargs()}")
```

### Common Issues

1. **Model not changing**: Direct parameters override environment variables
2. **Azure not working**: Ensure all Azure parameters are provided (endpoint, deployment, api_version)
3. **Custom endpoint failing**: Check base_url format (should end with /v1 for OpenAI compatibility)