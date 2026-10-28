package ai.callguard;

import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.concurrent.Executors;

/**
 * Enterprise delivery bridge. Receives audit summaries from the Python API and forwards
 * them to a Symphony room webhook with retry and exponential backoff.
 *   POST /audit   body: {"callId","message","verdict","riskScore","pack"}
 *   GET  /health
 * Env: SYMPHONY_WEBHOOK_URL (required to deliver), PORT (default 8081)
 */
public class SymphonyBridge {
    private static final HttpClient HTTP = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build();

    public static void main(String[] args) throws IOException {
        int port = Integer.parseInt(System.getenv().getOrDefault("PORT", "8081"));
        String webhook = System.getenv("SYMPHONY_WEBHOOK_URL");
        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);
        server.setExecutor(Executors.newFixedThreadPool(8));

        server.createContext("/health", ex -> reply(ex, 200, "{\"ok\":true,\"webhookConfigured\":" + (webhook != null && !webhook.isBlank()) + "}"));

        server.createContext("/audit", ex -> {
            if (!"POST".equals(ex.getRequestMethod())) { reply(ex, 405, "{\"error\":\"POST only\"}"); return; }
            String body = new String(ex.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
            if (webhook == null || webhook.isBlank()) {
                System.out.println("[bridge] no webhook configured, logging only: " + body);
                reply(ex, 202, "{\"delivered\":false,\"reason\":\"SYMPHONY_WEBHOOK_URL not set\"}");
                return;
            }
            boolean ok = deliver(webhook, body);
            reply(ex, ok ? 200 : 502, "{\"delivered\":" + ok + "}");
        });

        server.start();
        System.out.println("[bridge] listening on :" + port);
    }

    /** Up to 4 attempts with 0.5s, 1s, 2s backoff. */
    static boolean deliver(String url, String json) {
        long wait = 500;
        for (int attempt = 1; attempt <= 4; attempt++) {
            try {
                HttpRequest req = HttpRequest.newBuilder(URI.create(url)).timeout(Duration.ofSeconds(5))
                        .header("Content-Type", "application/json")
                        .POST(HttpRequest.BodyPublishers.ofString(json)).build();
                HttpResponse<String> res = HTTP.send(req, HttpResponse.BodyHandlers.ofString());
                if (res.statusCode() / 100 == 2) return true;
                System.err.println("[bridge] attempt " + attempt + " got HTTP " + res.statusCode());
            } catch (Exception e) {
                System.err.println("[bridge] attempt " + attempt + " failed: " + e.getMessage());
                if (e instanceof InterruptedException) Thread.currentThread().interrupt();
            }
            try { Thread.sleep(wait); } catch (InterruptedException ie) { Thread.currentThread().interrupt(); return false; }
            wait *= 2;
        }
        return false;
    }

    private static void reply(com.sun.net.httpserver.HttpExchange ex, int code, String json) throws IOException {
        byte[] b = json.getBytes(StandardCharsets.UTF_8);
        ex.getResponseHeaders().set("Content-Type", "application/json");
        ex.sendResponseHeaders(code, b.length);
        try (var os = ex.getResponseBody()) { os.write(b); }
    }
}
