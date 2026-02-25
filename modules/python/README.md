# Python AI Module

This module provides a Python starter template for integrating AI providers (OpenAI, local LLMs, etc.) into the Chatlippytm.ai.Bots platform.

## Prerequisites

- Python 3.9+
- (Optional) An OpenAI API key for cloud-based inference

## Installation

```bash
cd modules/python
pip install -r requirements.txt
```

## Usage

### As a library

```python
from modules.python.ai_integration import chat

response = chat("What is machine learning?")
print(response)
```

### From the command line

```bash
# Set your API key
export OPENAI_API_KEY="sk-..."

# Run a prompt
python modules/python/ai_integration.py "Explain neural networks in simple terms."
```

### Using a local LLM (Ollama)

1. Start Ollama: `ollama serve`
2. Pull a model: `ollama pull llama3`
3. Set the provider in `config/config.yaml` to `local`:
   ```yaml
   ai:
     default_provider: local
   ```
4. Run: `python modules/python/ai_integration.py "Hello!"`

## Running Tests

```bash
cd modules/python
python -m pytest tests/ -v
```

## Extending

To add a new AI provider:

1. Add its settings to `config/config.yaml` under `ai.providers`.
2. Register it in `config/extensions.json`.
3. Add a `_call_<provider>` function in `ai_integration.py`.
4. Update the `chat()` dispatch block.
5. Write tests in `tests/test_ai_integration.py`.
