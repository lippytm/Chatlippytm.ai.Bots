package ai;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.DisabledIfEnvironmentVariable;
import static org.junit.jupiter.api.Assertions.*;

/**
 * AiIntegrationTest.java
 * -----------------------
 * Unit tests for {@link AiIntegration}.
 *
 * Network calls are not made in these tests; only the dispatch logic, JSON
 * helpers, and guard conditions are exercised.
 */
class AiIntegrationTest {

    // -------------------------------------------------------------------------
    // Dispatch
    // -------------------------------------------------------------------------

    @Test
    void chat_unsupportedProvider_throwsIllegalArgumentException() {
        assertThrows(IllegalArgumentException.class,
                () -> AiIntegration.chat("hello", "unsupported_xyz"));
    }

    // -------------------------------------------------------------------------
    // callOpenAI guard
    // -------------------------------------------------------------------------

    @Test
    @DisabledIfEnvironmentVariable(named = "OPENAI_API_KEY", matches = ".+")
    void callOpenAI_missingApiKey_throwsIllegalStateException() {
        // Only runs when OPENAI_API_KEY is not set in CI
        assertThrows(IllegalStateException.class,
                () -> AiIntegration.callOpenAI("test"));
    }

    // -------------------------------------------------------------------------
    // JSON helpers
    // -------------------------------------------------------------------------

    @Test
    void escapeJson_specialCharacters() {
        String input    = "He said \"hello\"\nNew line\tTab";
        String escaped  = AiIntegration.escapeJson(input);
        assertTrue(escaped.contains("\\\""), "double quotes should be escaped");
        assertTrue(escaped.contains("\\n"),  "newlines should be escaped");
        assertTrue(escaped.contains("\\t"),  "tabs should be escaped");
    }

    @Test
    void extractJsonField_findsValue() {
        String json  = "{\"model\":\"gpt-4o\",\"response\":\"Hello world\"}";
        String value = AiIntegration.extractJsonField(json, "response");
        assertEquals("Hello world", value);
    }

    @Test
    void extractJsonField_missingKey_returnsEmpty() {
        String json  = "{\"model\":\"gpt-4o\"}";
        String value = AiIntegration.extractJsonField(json, "missing_key");
        assertEquals("", value);
    }

    @Test
    void extractContent_extractsContentField() {
        String json    = "{\"choices\":[{\"message\":{\"content\":\"Test response\"}}]}";
        // extractContent looks for "content":"..." anywhere in the string
        String content = AiIntegration.extractContent(json);
        assertEquals("Test response", content);
    }
}
