# llm-azure

[![PyPI](https://img.shields.io/pypi/v/llm-azure.svg)](https://pypi.org/project/llm-azure/)
[![Changelog](https://img.shields.io/github/v/release/fabge/llm-azure?include_prereleases&label=changelog)](https://github.com/fabge/llm-azure/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/fabge/llm-azure/blob/main/LICENSE)

[LLM](https://llm.datasette.io/) plugin for Azure AI Foundry with Entra ID authentication.

## Installation

```bash
llm install llm-azure

# For Claude models, also install:
llm install llm-azure[anthropic]
```

## Authentication

This plugin uses **Azure Entra ID** (formerly Azure AD) via `DefaultAzureCredential`. Make sure you're logged in:

```bash
az login
```

Your user needs the **"Cognitive Services User"** role on the Azure AI resource.

## Configuration

Create `azure/config.yaml` in your LLM config directory:

```bash
mkdir -p "$(dirname "$(llm logs path)")/azure"
```

### OpenAI-compatible models (GPT, Mistral, Llama)

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

```yaml
- model_id: claude-opus
  provider: anthropic
  model_name: claude-opus-4-5
  endpoint: https://YOUR_RESOURCE.openai.azure.com/anthropic/
  aliases: [opus]
```

## Usage

```bash
llm -m azure-gpt4o "Hello!"
llm -m mistral "Hello!"
llm -m opus "Hello!"
```

## API Key Authentication

If you prefer API keys over Entra ID, add `api_key_name` to your config. The name can be anything you choose:

```yaml
- model_id: azure-gpt4o
  provider: openai
  model_name: gpt-4o
  endpoint: https://YOUR_RESOURCE.openai.azure.com/openai/v1/
  api_key_name: azure-prod  # use any name you like

- model_id: claude-opus
  provider: anthropic
  model_name: claude-opus-4-5
  endpoint: https://YOUR_RESOURCE.openai.azure.com/anthropic/
  api_key_name: azure-prod  # can share keys across models
```

Then set the key:

```bash
llm keys set azure-prod
```

## Providers

| Provider    | Models                              | SDK         |
|-------------|-------------------------------------|-------------|
| `openai`    | GPT, Mistral, DeepSeek, Llama, etc. | `openai`    |
| `anthropic` | Claude                              | `anthropic` |

## Migrating from v1.x

Version 2.0 uses a new config format. Update your `azure/config.yaml`:

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
