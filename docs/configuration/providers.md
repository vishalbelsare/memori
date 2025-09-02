# LLM Provider Configuration

Comprehensive guide to configuring different LLM providers with Memori.

## Provider Configuration Overview

Memori supports multiple LLM providers through the `ProviderConfig` class. You can configure providers either through direct instantiation or by using environment variables.

## Supported Providers

### OpenAI

#### Direct Configuration
```python
from memori import Memori
from memori.core.providers import ProviderConfig

# Create OpenAI provider configuration
openai_provider = ProviderConfig.from_openai(
    api_key="sk-your-openai-api-key",
    organization="org-your-organization",  # Optional
    project="proj_your-project",           # Optional
    model="gpt-4o"                        # Optional, defaults to gpt-4o
)

# Initialize Memori with provider
memori = Memori(
    database_connect="sqlite:///openai_demo.db",
    provider_config=openai_provider,
    conscious_ingest=True,
    auto_ingest=True
)
```

#### Environment Variables
```bash
export OPENAI_API_KEY="sk-your-openai-api-key"
export OPENAI_ORG_ID="org-your-organization"
export OPENAI_PROJECT_ID="proj_your-project"
```

```python
from memori import Memori
from memori.core.providers import ProviderConfig

# Auto-detect from environment
openai_provider = ProviderConfig.from_openai(
    api_key=os.getenv("OPENAI_API_KEY"),
    organization=os.getenv("OPENAI_ORG_ID"),
    project=os.getenv("OPENAI_PROJECT_ID"),
    model="gpt-4o"
)

memori = Memori(provider_config=openai_provider)
```

### Azure OpenAI

#### Direct Configuration
```python
from memori import Memori
from memori.core.providers import ProviderConfig

# Create Azure OpenAI provider configuration
azure_provider = ProviderConfig.from_azure(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    api_version="2024-02-01",
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
)

# Initialize Memori with Azure provider
azure_memory = Memori(
    database_connect="sqlite:///azure_demo.db",
    conscious_ingest=True,
    auto_ingest=True,
    provider_config=azure_provider
)
```

#### Environment Variables
```bash
export AZURE_OPENAI_API_KEY="your-azure-openai-api-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o"
export AZURE_OPENAI_API_VERSION="2024-02-01"
```

```python
azure_provider = ProviderConfig.from_azure(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
)
```

#### Advanced Azure Configuration
```python
# With Azure AD authentication
azure_provider = ProviderConfig.from_azure(
    azure_endpoint="https://your-resource.openai.azure.com/",
    azure_deployment="gpt-4o",
    api_version="2024-02-01",
    azure_ad_token="your-azure-ad-token",  # Instead of API key
    model="gpt-4o"
)

# With custom timeout and retries
azure_provider = ProviderConfig.from_azure(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    api_version="2024-02-01",
    timeout=60.0,
    max_retries=5
)
```

### Ollama (Local LLMs)

#### Direct Configuration
```python
from memori import Memori
from memori.core.providers import ProviderConfig

# Create Ollama provider configuration
ollama_provider = ProviderConfig.from_custom(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # Placeholder - Ollama doesn't require a real API key
    model=os.getenv("OLLAMA_MODEL", "llama3.2:3b")
)

# Initialize Memori with Ollama
ollama_memory = Memori(
    database_connect="sqlite:///ollama_demo.db",
    conscious_ingest=True,
    auto_ingest=True,
    provider_config=ollama_provider
)
```

#### Environment Variables
```bash
export OLLAMA_HOST="http://localhost:11434"
export OLLAMA_MODEL="llama3.2:3b"
```

```python
ollama_provider = ProviderConfig.from_custom(
    base_url=f"{os.getenv('OLLAMA_HOST', 'http://localhost:11434')}/v1",
    api_key="ollama",
    model=os.getenv("OLLAMA_MODEL", "llama3.2:3b")
)
```

### Custom OpenAI-Compatible Providers

#### Generic Custom Provider
```python
# For providers like Together AI, Groq, etc.
custom_provider = ProviderConfig.from_custom(
    base_url="https://api.together.xyz/v1",
    api_key="your-together-api-key",
    model="meta-llama/Llama-2-70b-chat-hf"
)

# Groq
groq_provider = ProviderConfig.from_custom(
    base_url="https://api.groq.com/openai/v1",
    api_key="gsk_your-groq-api-key",
    model="mixtral-8x7b-32768"
)

# Perplexity
perplexity_provider = ProviderConfig.from_custom(
    base_url="https://api.perplexity.ai",
    api_key="pplx-your-api-key",
    model="llama-3.1-sonar-large-128k-online"
)
```

#### Custom Provider with Headers
```python
custom_provider = ProviderConfig(
    api_key="your-api-key",
    api_type="custom",
    base_url="https://api.custom-provider.com/v1",
    model="custom-model",
    default_headers={
        "X-Custom-Header": "value",
        "Authorization": "Bearer your-token"
    },
    timeout=30.0,
    max_retries=3
)
```

### LiteLLM Configuration

#### Universal LiteLLM Support
```python
from memori import Memori
from litellm import completion

# Initialize Memori (no provider config needed for LiteLLM)
litellm_memory = Memori(
    database_connect="sqlite:///litellm_demo.db",
    conscious_ingest=True,
    auto_ingest=True
)

# Enable memory tracking
litellm_memory.enable()

# Use any LiteLLM-supported model
response = completion(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}]
)

# Works with any provider through LiteLLM
response = completion(
    model="claude-3-sonnet-20240229",
    messages=[{"role": "user", "content": "Hello"}]
)

response = completion(
    model="gemini-pro",
    messages=[{"role": "user", "content": "Hello"}]
)
```

## Provider Configuration Patterns

### Multiple Providers
```python
# Configure multiple providers for different use cases
openai_provider = ProviderConfig.from_openai(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o"
)

azure_provider = ProviderConfig.from_azure(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment="gpt-4o"
)

# Use different providers for different projects
dev_memori = Memori(provider_config=openai_provider)
prod_memori = Memori(provider_config=azure_provider)
```

### Fallback Configuration
```python
# Primary provider
try:
    primary_provider = ProviderConfig.from_azure(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_deployment="gpt-4o"
    )
    memori = Memori(provider_config=primary_provider)
except Exception:
    # Fallback to OpenAI
    fallback_provider = ProviderConfig.from_openai(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o"
    )
    memori = Memori(provider_config=fallback_provider)
```

### Environment-Based Configuration
```python
import os
from memori import Memori
from memori.core.providers import ProviderConfig

def create_provider_from_env():
    """Create provider based on environment variables"""
    
    # Check for Azure configuration first
    if all([
        os.getenv("AZURE_OPENAI_API_KEY"),
        os.getenv("AZURE_OPENAI_ENDPOINT"),
        os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    ]):
        return ProviderConfig.from_azure(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
        )
    
    # Check for OpenAI configuration
    elif os.getenv("OPENAI_API_KEY"):
        return ProviderConfig.from_openai(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("OPENAI_MODEL", "gpt-4o")
        )
    
    # Check for custom provider
    elif os.getenv("CUSTOM_API_URL"):
        return ProviderConfig.from_custom(
            base_url=os.getenv("CUSTOM_API_URL"),
            api_key=os.getenv("CUSTOM_API_KEY"),
            model=os.getenv("CUSTOM_MODEL", "gpt-4o")
        )
    
    else:
        raise ValueError("No provider configuration found in environment")

# Use the dynamic provider
provider = create_provider_from_env()
memori = Memori(provider_config=provider)
```

## Environment Variable Reference

### OpenAI
```bash
OPENAI_API_KEY="sk-your-api-key"
OPENAI_ORG_ID="org-your-organization"
OPENAI_PROJECT_ID="proj_your-project"
OPENAI_MODEL="gpt-4o"
```

### Azure OpenAI
```bash
AZURE_OPENAI_API_KEY="your-azure-api-key"
AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o"
AZURE_OPENAI_API_VERSION="2024-02-01"
```

### Ollama
```bash
OLLAMA_HOST="http://localhost:11434"
OLLAMA_MODEL="llama3.2:3b"
```

### Custom Providers
```bash
CUSTOM_API_URL="https://api.provider.com/v1"
CUSTOM_API_KEY="your-api-key"
CUSTOM_MODEL="your-model"
```

## Best Practices

### Security
```python
# Use environment variables for sensitive data
azure_provider = ProviderConfig.from_azure(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),  # Never hardcode
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
)

# Use .env files for development
from dotenv import load_dotenv
load_dotenv()
```

### Error Handling
```python
try:
    provider = ProviderConfig.from_azure(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    )
    
    # Test the provider
    client = provider.create_client()
    memori = Memori(provider_config=provider)
    
except Exception as e:
    print(f"Provider configuration failed: {e}")
    # Use fallback or exit gracefully
```

### Performance
```python
# Configure timeouts and retries for production
provider = ProviderConfig.from_openai(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    timeout=60.0,      # 60 second timeout
    max_retries=3      # Retry failed requests
)
```

### Development vs Production
```python
# Development configuration
if os.getenv("ENVIRONMENT") == "development":
    provider = ProviderConfig.from_openai(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-mini"  # Cheaper model for development
    )
else:
    # Production configuration
    provider = ProviderConfig.from_azure(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_deployment="gpt-4o",
        max_retries=5
    )
```
