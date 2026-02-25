# JavaScript AI Module

This module provides a Node.js starter template for integrating AI providers into the Chatlippytm.ai.Bots platform.

## Prerequisites

- Node.js 18+
- (Optional) An OpenAI API key for cloud-based inference

## Installation

```bash
cd modules/javascript
npm install
```

## Usage

### As a library

```javascript
const { chat } = require("./ai_integration");

const response = await chat("What is machine learning?");
console.log(response);
```

### From the command line

```bash
# Set your API key
export OPENAI_API_KEY="sk-..."

# Run a prompt
node modules/javascript/ai_integration.js "Explain neural networks in simple terms."
```

### Using a local LLM (Ollama)

1. Start Ollama: `ollama serve`
2. Pull a model: `ollama pull llama3`
3. Set `ai.default_provider` to `local` in `config/config.yaml`
4. Run: `node modules/javascript/ai_integration.js "Hello!"`

## Running Tests

```bash
cd modules/javascript
node --test tests/ai_integration.test.js
```

Or via npm:

```bash
npm test
```

## Extending

To add a new AI provider:

1. Add its settings to `config/config.yaml` under `ai.providers`.
2. Register it in `config/extensions.json`.
3. Add a `callMyProvider(prompt, aiConfig)` function in `ai_integration.js`.
4. Update the `chat()` dispatch block.
5. Write tests in `tests/ai_integration.test.js`.
