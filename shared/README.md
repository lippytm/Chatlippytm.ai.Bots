# Shared Utilities

This directory contains cross-language utilities that are shared across all modules.

## Contents

| File | Description |
|------|-------------|
| `utils/config_loader.py` | Python helper to load `config/config.yaml` and `config/extensions.json` |

## Usage (Python)

```python
from shared.utils.config_loader import load_config, load_extensions, get_enabled_extensions

# Load global configuration
config = load_config()
print(config["app"]["name"])        # Chatlippytm.ai.Bots
print(config["ai"]["default_provider"])  # openai

# Load all extensions
extensions = load_extensions()

# Load only enabled extensions
active = get_enabled_extensions()
for ext in active:
    print(ext["id"], ext["language"])
```

## Extending

To add a new shared utility:

1. Create a new file in `shared/utils/` (e.g., `logger.py`, `auth_helper.js`).
2. Document it in this README.
3. Import or require it from the relevant language module.
