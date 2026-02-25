package ai;

import java.io.IOException;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Scanner;

/**
 * AiIntegration.java
 * -------------------
 * Starter template for Java-based AI integrations in the Chatlippytm.ai.Bots
 * platform.
 *
 * <p>This class demonstrates how to send a prompt to an AI provider over HTTP.
 * By default it targets the OpenAI Chat Completions API, but the
 * {@link #chat(String, String)} method can be extended to support any
 * provider.
 *
 * <p><b>Environment Variables</b>
 * <ul>
 *   <li>{@code OPENAI_API_KEY} – Required when using the {@code openai} provider.</li>
 * </ul>
 *
 * <p><b>Running from the command line</b>
 * <pre>{@code
 *   export OPENAI_API_KEY="sk-..."
 *   mvn -q package -DskipTests
 *   java -cp target/ai-integration-1.0.0.jar ai.AiIntegration "Hello!"
 * }</pre>
 */
public class AiIntegration {

    private static final String OPENAI_ENDPOINT =
            "https://api.openai.com/v1/chat/completions";
    private static final String DEFAULT_MODEL   = "gpt-4o-mini";
    private static final int    MAX_TOKENS      = 1024;

    /**
     * Send {@code prompt} to the default AI provider and return the response.
     *
     * @param prompt the user's input message
     * @return the AI's response text
     * @throws IOException          if the HTTP request fails
     * @throws IllegalStateException if a required environment variable is missing
     */
    public static String chat(String prompt) throws IOException {
        return chat(prompt, "openai");
    }

    /**
     * Send {@code prompt} to the specified AI provider and return the response.
     *
     * @param prompt   the user's input message
     * @param provider one of {@code "openai"} or {@code "local"}
     * @return the AI's response text
     * @throws IOException              if the HTTP request fails
     * @throws IllegalArgumentException if the provider is unsupported
     * @throws IllegalStateException    if a required environment variable is missing
     */
    public static String chat(String prompt, String provider) throws IOException {
        if ("openai".equalsIgnoreCase(provider)) {
            return callOpenAI(prompt);
        }
        if ("local".equalsIgnoreCase(provider)) {
            return callLocal(prompt);
        }
        throw new IllegalArgumentException(
                "Unsupported AI provider: '" + provider + "'. " +
                "Add a handler in AiIntegration.java or update config/config.yaml."
        );
    }

    // -------------------------------------------------------------------------
    // Provider implementations
    // -------------------------------------------------------------------------

    static String callOpenAI(String prompt) throws IOException {
        String apiKey = System.getenv("OPENAI_API_KEY");
        if (apiKey == null || apiKey.isBlank()) {
            throw new IllegalStateException(
                    "OPENAI_API_KEY environment variable is not set."
            );
        }

        String requestBody = "{"
                + "\"model\":\"" + DEFAULT_MODEL + "\","
                + "\"max_tokens\":" + MAX_TOKENS + ","
                + "\"messages\":[{\"role\":\"user\",\"content\":\""
                + escapeJson(prompt) + "\"}]"
                + "}";

        String responseBody = httpPost(OPENAI_ENDPOINT, requestBody,
                "Bearer " + apiKey);

        return extractContent(responseBody);
    }

    static String callLocal(String prompt) throws IOException {
        String endpoint  = "http://localhost:11434/api/generate";
        String requestBody = "{\"model\":\"llama3\",\"prompt\":\""
                + escapeJson(prompt) + "\",\"stream\":false}";
        String responseBody = httpPost(endpoint, requestBody, null);

        // Extract "response" field from JSON
        return extractJsonField(responseBody, "response");
    }

    // -------------------------------------------------------------------------
    // HTTP and JSON helpers
    // -------------------------------------------------------------------------

    /**
     * Perform an HTTP POST and return the response body as a String.
     *
     * @param endpoint      target URL
     * @param body          JSON request body
     * @param authorization value for the {@code Authorization} header, or {@code null}
     * @return raw response body
     */
    static String httpPost(String endpoint, String body,
                           String authorization) throws IOException {
        URL url = new URL(endpoint);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("POST");
        conn.setRequestProperty("Content-Type", "application/json");
        if (authorization != null) {
            conn.setRequestProperty("Authorization", authorization);
        }
        conn.setDoOutput(true);

        byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
        try (OutputStream os = conn.getOutputStream()) {
            os.write(bytes);
        }

        try (Scanner scanner = new Scanner(conn.getInputStream(),
                StandardCharsets.UTF_8)) {
            scanner.useDelimiter("\\A");
            return scanner.hasNext() ? scanner.next() : "";
        }
    }

    /** Naively extract the {@code "content"} field from an OpenAI response. */
    static String extractContent(String json) {
        return extractJsonField(json, "content");
    }

    /** Extract a simple string field from a flat JSON object by key name. */
    static String extractJsonField(String json, String fieldName) {
        String search = "\"" + fieldName + "\":\"";
        int start = json.indexOf(search);
        if (start < 0) return "";
        start += search.length();
        int end = json.indexOf("\"", start);
        if (end < 0) return "";
        return json.substring(start, end)
                .replace("\\n", "\n")
                .replace("\\\"", "\"")
                .trim();
    }

    /** Escape a string for safe embedding in a JSON literal. */
    static String escapeJson(String value) {
        return value
                .replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t");
    }

    // -------------------------------------------------------------------------
    // CLI entry point
    // -------------------------------------------------------------------------

    public static void main(String[] args) {
        if (args.length == 0) {
            System.err.println("Usage: java ai.AiIntegration \"<your prompt>\"");
            System.exit(1);
        }
        String prompt = String.join(" ", args);
        try {
            String response = chat(prompt);
            System.out.println("AI Response: " + response);
        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
            System.exit(1);
        }
    }
}
