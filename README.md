# llm-azure

[![PyPI](https://img.shields.io/pypi/v/llm-azure.svg)](https://pypi.org/project/llm-azure/)
[![Changelog](https://img.shields.io/github/v/release/fabge/llm-azure?include_prereleases&label=changelog)](https://github.com/fabge/llm-azure/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/fabge/llm-azure/blob/main/LICENSE)

LLM access to the Azure OpenAI SDK

## Installation

Install this plugin in the same environment as [LLM](https://llm.datasette.io/).

```bash
llm install llm-azure
```

## Usage

First, set an API key for Azure OpenAI:

```bash
llm keys set azure
# Paste key here
```

To add the `gpt-4-32k` model, deployed in your Azure Subscription, add this to your `azure/config.yaml` file:

```yaml
- model_id: gpt-4-32k
  deployment_name: gpt-4-32k
  endpoint: https://your_deployment.openai.azure.com/
  api_version: '2023-05-15'
```

the configuration file should be in the `azure` directory in the config of your `llm` installation.
Run this command to find the directory in which this file should be created:

```bash
dirname "$(llm logs path)"
```

The `model_id` is the name LLM will use for the model. The `deployment_name` is the name which needs to be passed to the API - this might differ from the `model_id`, especially if the `model_id` could potentially clash with other installed models.
