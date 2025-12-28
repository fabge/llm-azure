# llm-azure

[![PyPI](https://img.shields.io/pypi/v/llm-azure.svg)](https://pypi.org/project/llm-azure/)
[![Changelog](https://img.shields.io/github/v/release/fabge/llm-azure?include_prereleases&label=changelog)](https://github.com/fabge/llm-azure/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/fabge/llm-azure/blob/main/LICENSE)

[LLM](https://llm.datasette.io/) plugin for Azure AI Foundry.

## Why this plugin?

LLM has built-in support for [OpenAI-compatible models](https://llm.datasette.io/en/stable/other-models.html#openai-compatible-models) via `extra-openai-models.yaml`, but it only supports API key authentication.

This plugin adds:

- **Entra ID authentication** - Use `az login` instead of managing API keys
- **Claude models on Azure** - Access Anthropic models through Azure AI Foundry

If you only need API key authentication for OpenAI-compatible models, you don't need this plugin.

## Installation

```bash
llm install llm-azure

# For Claude models:
llm install llm-azure[anthropic]
```

## Quick Start

1. Login to Azure:

   ```bash
   az login
   ```

1. Create config file:

   ```bash
   mkdir -p "$(dirname "$(llm logs path)")/azure"
   ```

1. Add models to `azure/config.yaml`:

   ```yaml
   - model_id: azure-gpt4o
     provider: openai
     model_name: gpt-4o
     endpoint: https://YOUR_RESOURCE.openai.azure.com/openai/v1/
   ```

1. Use it:

   ```bash
   llm -m azure-gpt4o "Hello!"
   ```

## Configuration

Models are configured in `azure/config.yaml` in your LLM config directory (find it with `dirname "$(llm logs path)"`).

### OpenAI-compatible models (GPT, Mistral, DeepSeek, Llama)

```yaml
- model_id: azure-gpt4o
  provider: openai
  model_name: gpt-4o
  endpoint: https://YOUR_RESOURCE.openai.azure.com/openai/v1/
  aliases: [agpt]

- model_id: mistral-large
  provider: openai
  model_name: Mistral-Large-3
  endpoint: https://YOUR_RESOURCE.openai.azure.com/openai/v1/
  aliases: [mistral]
```

### Claude models

Requires `llm install llm-azure[anthropic]`.

```yaml
- model_id: claude-opus
  provider: anthropic
  model_name: claude-opus-4-5
  endpoint: https://YOUR_RESOURCE.openai.azure.com/anthropic/
  aliases: [opus]
```

### Configuration options

| Field          | Required | Description                                      |
|----------------|----------|--------------------------------------------------|
| `model_id`     | Yes      | Name used with `llm -m`                          |
| `provider`     | Yes      | `openai` or `anthropic`                          |
| `model_name`   | Yes      | Model name as deployed in Azure                  |
| `endpoint`     | Yes      | Azure endpoint URL                               |
| `aliases`      | No       | Short names for the model                        |
| `api_key_name` | No       | Use API key instead of Entra ID (see below)      |

## Authentication

### Entra ID (default)

Uses `DefaultAzureCredential` from the Azure SDK. Make sure you're logged in:

```bash
az login
```

Your user needs the **"Cognitive Services User"** role on the Azure AI resource.

### API Key

Add `api_key_name` to your model config:

```yaml
- model_id: azure-gpt4o
  provider: openai
  model_name: gpt-4o
  endpoint: https://YOUR_RESOURCE.openai.azure.com/openai/v1/
  api_key_name: azure-prod
```

Then set the key (the name can be anything you choose):

```bash
llm keys set azure-prod
```

Multiple models can share the same key name.

## Providers

| Provider    | Models                              | SDK         |
|-------------|-------------------------------------|-------------|
| `openai`    | GPT, Mistral, DeepSeek, Llama, etc. | `openai`    |
| `anthropic` | Claude                              | `anthropic` |

## Migrating from v1.x

Version 2.0 has a new config format:

```yaml
# Old format (v1.x)
- model_id: gpt-4o
  model_name: gpt-4o
  api_base: https://YOUR_RESOURCE.openai.azure.com/
  api_version: '2024-12-01-preview'

# New format (v2.0)
- model_id: gpt-4o
  provider: openai
  model_name: gpt-4o
  endpoint: https://YOUR_RESOURCE.openai.azure.com/openai/v1/
```

Changes:

- `api_base` → `endpoint` (add `/openai/v1/` suffix)
- `api_version` → removed (no longer needed)
- `provider` → required (`openai` or `anthropic`)
