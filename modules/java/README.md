# Java AI Module

This module provides a Java starter template for integrating AI providers into the Chatlippytm.ai.Bots platform.

## Prerequisites

- Java 17+
- Maven 3.8+
- (Optional) An OpenAI API key for cloud-based inference

## Installation

No additional dependencies beyond the JDK are required for the core module. JUnit 5 is fetched automatically by Maven for tests.

```bash
cd modules/java
mvn compile
```

## Usage

### As a library

```java
import ai.AiIntegration;

String response = AiIntegration.chat("What is machine learning?");
System.out.println(response);
```

### From the command line

```bash
# Set your API key
export OPENAI_API_KEY="sk-..."

# Build and run
cd modules/java
mvn -q package -DskipTests
java -cp target/ai-integration-1.0.0.jar ai.AiIntegration "Explain neural networks."
```

### Using a local LLM (Ollama)

```java
String response = AiIntegration.chat("Hello!", "local");
System.out.println(response);
```

## Running Tests

```bash
cd modules/java
mvn test
```

## Extending

To add a new AI provider:

1. Add its settings to `config/config.yaml` under `ai.providers`.
2. Register it in `config/extensions.json`.
3. Add a `callMyProvider(String prompt)` static method in `AiIntegration.java`.
4. Update the `chat(String, String)` dispatch block.
5. Write tests in `src/test/java/ai/AiIntegrationTest.java`.
