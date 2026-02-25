# Contributing to Chatlippytm.ai.Bots

Thank you for your interest in contributing! This guide explains how to add new modules, extend existing ones, and follow the project's conventions.

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Adding a New Language Module](#adding-a-new-language-module)
3. [Adding a New AI Provider to an Existing Module](#adding-a-new-ai-provider-to-an-existing-module)
4. [Updating the Configuration](#updating-the-configuration)
5. [Writing Tests](#writing-tests)
6. [CI/CD](#cicd)
7. [Code Style](#code-style)

---

## Project Structure

```
.
├── modules/<language>/       # One directory per language
│   ├── README.md             # Module-level docs
│   ├── ai_integration.<ext>  # Core integration file
│   ├── requirements.txt / package.json / pom.xml
│   └── tests/                # Module-level tests
├── shared/utils/             # Cross-language utilities
├── config/
│   ├── config.yaml           # Global configuration
│   └── extensions.json       # Extensions registry
└── .github/workflows/        # CI/CD per language
```

---

## Adding a New Language Module

1. **Create the module directory**:
   ```bash
   mkdir -p modules/<language>/tests
   ```

2. **Add the integration file** following the pattern of an existing module (e.g., `modules/python/ai_integration.py`). At minimum implement:
   - A `chat(prompt, provider=None)` function (or equivalent for your language).
   - A dispatch block that delegates to provider-specific functions.
   - Guard conditions for missing API keys / unsupported providers.

3. **Add a `README.md`** in `modules/<language>/` documenting:
   - Prerequisites
   - Installation
   - Usage (library + CLI)
   - Running tests
   - How to extend

4. **Register the module** in `config/extensions.json`:
   ```json
   {
     "id": "my-language-ai",
     "name": "My Language AI Integration",
     "language": "<language>",
     "version": "1.0.0",
     "description": "...",
     "entry_point": "modules/<language>/ai_integration.<ext>",
     "enabled": true,
     "tags": ["<language>", "chat"]
   }
   ```

5. **Enable it** in `config/config.yaml` under `modules`:
   ```yaml
   modules:
     <language>:
       enabled: true
       entry_point: "modules/<language>/ai_integration.<ext>"
   ```

6. **Add a CI/CD workflow** in `.github/workflows/<language>-ci.yml` following the pattern of the existing workflows.

---

## Adding a New AI Provider to an Existing Module

1. Add provider settings in `config/config.yaml` under `ai.providers`:
   ```yaml
   ai:
     providers:
       myprovider:
         model: "my-model-id"
         api_key_env: "MY_PROVIDER_API_KEY"
   ```

2. Add a `_call_myprovider` (Python) / `callMyProvider` (JavaScript/Java) function in the relevant `ai_integration` file.

3. Update the `chat()` dispatch block to route `provider="myprovider"` to your new function.

4. Register the extension in `config/extensions.json`.

5. Write tests (see below).

---

## Updating the Configuration

- **`config/config.yaml`** — Global runtime settings. Follows standard YAML.
- **`config/extensions.json`** — Extensions registry. Each entry must include `id`, `language`, `version`, `entry_point`, and `enabled`.

---

## Writing Tests

- Tests must **not** make real network calls. Use mocking.
- Place tests in `modules/<language>/tests/`.
- Follow existing test patterns for each language.
- Aim for coverage of:
  - Dispatch logic (valid and invalid providers)
  - Guard conditions (missing env vars)
  - JSON/config helpers

Run all Python tests:
```bash
python -m pytest modules/python/tests/ -v
```

Run all JavaScript tests:
```bash
node --test modules/javascript/tests/ai_integration.test.js
```

Run all Java tests:
```bash
cd modules/java && mvn test
```

---

## CI/CD

Each language has a dedicated GitHub Actions workflow that runs on push/PR when relevant files change:

| Language   | Workflow file                         |
|------------|---------------------------------------|
| Python     | `.github/workflows/python-ci.yml`     |
| JavaScript | `.github/workflows/javascript-ci.yml` |
| Java       | `.github/workflows/java-ci.yml`       |

---

## Code Style

- **Python**: PEP 8, max line length 100. Run `flake8 modules/python/ shared/`.
- **JavaScript**: Standard Node.js conventions, `"use strict"`.
- **Java**: Standard Java conventions, Javadoc for public methods.
- **YAML/JSON**: 2-space indent, UTF-8 encoding.
