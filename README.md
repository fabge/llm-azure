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

If you prefer API keys over Entra ID, add `api_key_name` to your config:

```yaml
- model_id: azure-gpt4o
  provider: openai
  model_name: gpt-4o
  endpoint: https://YOUR_RESOURCE.openai.azure.com/openai/v1/
  api_key_name: azure
```

Then set the key:

```bash
llm keys set azure
```

## Providers

| Provider    | Models                              | SDK         |
|-------------|-------------------------------------|-------------|
| `openai`    | GPT, Mistral, DeepSeek, Llama, etc. | `openai`    |
| `anthropic` | Claude                              | `anthropic` |
