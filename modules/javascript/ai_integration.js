/**
 * modules/javascript/ai_integration.js
 * --------------------------------------
 * Starter template for JavaScript-based AI integrations.
 *
 * Reads configuration from ../../config/config.yaml (via a lightweight YAML
 * parser) and delegates prompts to the configured AI provider.
 *
 * Environment Variables
 * ---------------------
 * OPENAI_API_KEY   - Required when using the 'openai' provider.
 *
 * Usage (CLI)
 * -----------
 *   export OPENAI_API_KEY="sk-..."
 *   node modules/javascript/ai_integration.js "What is deep learning?"
 */

"use strict";

const fs   = require("fs");
const path = require("path");
const https = require("https");

// ---------------------------------------------------------------------------
// Minimal YAML key:value parser (avoids a runtime dependency in basic cases)
// ---------------------------------------------------------------------------
function parseSimpleYaml(text) {
  const result = {};
  const stack  = [{ indent: -1, obj: result }];

  for (const rawLine of text.split("\n")) {
    const line = rawLine.replace(/#.*$/, ""); // strip comments
    if (!line.trim()) continue;

    const indent = line.search(/\S/);
    const match  = line.trim().match(/^([^:]+):\s*(.*)?$/);
    if (!match) continue;

    const [, key, value] = match;

    while (stack.length > 1 && stack[stack.length - 1].indent >= indent) {
      stack.pop();
    }

    const parent = stack[stack.length - 1].obj;
    if (!value || value.trim() === "") {
      parent[key.trim()] = {};
      stack.push({ indent, obj: parent[key.trim()] });
    } else {
      parent[key.trim()] = value.trim().replace(/^["']|["']$/g, "");
    }
  }
  return result;
}

// ---------------------------------------------------------------------------
// Load global configuration
// ---------------------------------------------------------------------------
function loadConfig() {
  const configPath = path.resolve(__dirname, "../../config/config.yaml");
  if (!fs.existsSync(configPath)) {
    return {};
  }
  const text = fs.readFileSync(configPath, "utf8");
  return parseSimpleYaml(text);
}

// ---------------------------------------------------------------------------
// Core chat function
// ---------------------------------------------------------------------------

/**
 * Send a prompt to an AI provider and return the response as a Promise<string>.
 *
 * @param {string}      prompt   - The user's input message.
 * @param {string|null} provider - Override the default provider from config.
 * @returns {Promise<string>}
 */
async function chat(prompt, provider = null) {
  const config           = loadConfig();
  const aiConfig         = config.ai || {};
  const resolvedProvider = provider || aiConfig.default_provider || "openai";

  if (resolvedProvider === "openai") {
    return callOpenAI(prompt, aiConfig);
  }
  if (resolvedProvider === "local") {
    return callLocal(prompt, aiConfig);
  }

  throw new Error(
    `Unsupported AI provider: '${resolvedProvider}'. ` +
    "Add a handler in ai_integration.js or update config/config.yaml."
  );
}

// ---------------------------------------------------------------------------
// Provider implementations
// ---------------------------------------------------------------------------

async function callOpenAI(prompt, aiConfig) {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    throw new Error("OPENAI_API_KEY environment variable is not set.");
  }

  let OpenAI;
  try {
    ({ default: OpenAI } = await import("openai"));
  } catch {
    throw new Error(
      "openai package is not installed. Run: npm install openai"
    );
  }

  const providers   = (aiConfig.providers || {});
  const providerCfg = providers.openai || {};
  const client      = new OpenAI({ apiKey });

  const response = await client.chat.completions.create({
    model:       providerCfg.model       || "gpt-4o-mini",
    max_tokens:  Number(providerCfg.max_tokens  || 1024),
    temperature: Number(providerCfg.temperature || 0.7),
    messages:    [{ role: "user", content: prompt }],
  });

  return response.choices[0].message.content.trim();
}

async function callLocal(prompt, aiConfig) {
  const providers   = (aiConfig.providers || {});
  const providerCfg = providers.local || {};
  const endpoint    = providerCfg.endpoint || "http://localhost:11434/api/generate";
  const model       = providerCfg.model    || "llama3";

  const payload = JSON.stringify({ model, prompt, stream: false });
  const url     = new URL(endpoint);

  return new Promise((resolve, reject) => {
    const lib = url.protocol === "https:" ? require("https") : require("http");
    const req = lib.request(
      { hostname: url.hostname, port: url.port, path: url.pathname, method: "POST",
        headers: { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(payload) } },
      (res) => {
        let body = "";
        res.on("data", (chunk) => { body += chunk; });
        res.on("end",  () => {
          try {
            const data = JSON.parse(body);
            resolve((data.response || "").trim());
          } catch (e) {
            reject(new Error("Failed to parse local LLM response: " + e.message));
          }
        });
      }
    );
    req.on("error", reject);
    req.write(payload);
    req.end();
  });
}

// ---------------------------------------------------------------------------
// CLI entry point
// ---------------------------------------------------------------------------

if (require.main === module) {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    console.error('Usage: node ai_integration.js "<your prompt>"');
    process.exit(1);
  }
  chat(args.join(" "))
    .then((reply) => console.log("AI Response:", reply))
    .catch((err) => { console.error("Error:", err.message); process.exit(1); });
}

module.exports = { chat, callOpenAI, callLocal, loadConfig };
