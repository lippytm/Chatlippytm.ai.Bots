# Chatlippytm.ai.Bots

An AI Hub for Building Business of Businesses. A modular, multi-language platform for "The Encyclopedia of Everything Applied" & "lippytm.AI", integrating ManyChat and BotBuilders.com capabilities.

## Overview

This repository provides a **modular, scalable, and flexible** framework for building AI Full Stack applications across multiple languages and platforms. It is designed to grow with your needs—whether you're adding a new AI integration, a new language, or a new deployment target.

## Repository Structure

```
.
├── modules/                  # Language-specific AI modules
│   ├── python/               # Python AI integrations
│   ├── javascript/           # JavaScript AI integrations
│   ├── java/                 # Java AI integrations
│   └── blockchain/           # Blockchain placeholder scaffolding
├── shared/                   # Cross-language shared utilities
│   └── utils/                # Config loaders, helpers
├── config/                   # Dynamic configuration files
│   ├── config.yaml           # Global runtime configuration
│   └── extensions.json       # Extensions registry
└── .github/workflows/        # CI/CD pipelines per language
```

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/lippytm/Chatlippytm.ai.Bots.git
   cd Chatlippytm.ai.Bots
   ```

2. Choose a language module and follow its `README.md`:
   - [Python Module](modules/python/README.md)
   - [JavaScript Module](modules/javascript/README.md)
   - [Java Module](modules/java/README.md)
   - [Blockchain Module](modules/blockchain/README.md)

3. Review the [shared utilities](shared/README.md) for cross-language helpers.

## Configuration

All modules are driven by configuration in the `config/` directory. See [`config/config.yaml`](config/config.yaml) for available options and [`config/extensions.json`](config/extensions.json) to register new integrations.

## CI/CD

GitHub Actions workflows run automatically on push and pull request for each language module:

| Workflow | File |
|----------|------|
| Python CI | `.github/workflows/python-ci.yml` |
| JavaScript CI | `.github/workflows/javascript-ci.yml` |
| Java CI | `.github/workflows/java-ci.yml` |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on adding new modules or extending existing ones.

## License

[MIT](LICENSE)
