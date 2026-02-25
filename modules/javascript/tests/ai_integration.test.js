/**
 * modules/javascript/tests/ai_integration.test.js
 * -------------------------------------------------
 * Unit tests for modules/javascript/ai_integration.js.
 *
 * Uses the built-in Node.js test runner (node:test) so no additional
 * test framework needs to be installed.
 *
 * Run:
 *   node --test modules/javascript/tests/ai_integration.test.js
 */

"use strict";

const assert = require("assert");
const { describe, it, mock, beforeEach } = require("node:test");
const path   = require("path");

// Load module under test
const aiModule = require(path.resolve(__dirname, "../ai_integration.js"));

// ---------------------------------------------------------------------------
// loadConfig
// ---------------------------------------------------------------------------
describe("loadConfig", () => {
  it("returns an object", () => {
    const config = aiModule.loadConfig();
    assert.strictEqual(typeof config, "object");
    assert.ok(config !== null);
  });

  it("contains an 'ai' section", () => {
    const config = aiModule.loadConfig();
    assert.ok("ai" in config, "Expected 'ai' key in config");
  });
});

// ---------------------------------------------------------------------------
// chat() dispatch
// ---------------------------------------------------------------------------
describe("chat() dispatch", () => {
  it("rejects unsupported provider", async () => {
    await assert.rejects(
      () => aiModule.chat("hello", "unsupported_xyz"),
      /Unsupported AI provider/
    );
  });
});

// ---------------------------------------------------------------------------
// callOpenAI() guards
// ---------------------------------------------------------------------------
describe("callOpenAI()", () => {
  it("throws when OPENAI_API_KEY is missing", async () => {
    const savedKey = process.env.OPENAI_API_KEY;
    delete process.env.OPENAI_API_KEY;

    try {
      await assert.rejects(
        () => aiModule.callOpenAI("test", {}),
        /OPENAI_API_KEY/
      );
    } finally {
      if (savedKey !== undefined) process.env.OPENAI_API_KEY = savedKey;
    }
  });
});
