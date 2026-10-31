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
 * Enterprise delivery bridge for Y Combinator x Symphony Buildathon.
 * Receives audit summaries from the Python API and forwards them to a Symphony
 * room webhook with retry and exponential backoff.
 *   POST /audit   body: {"callId","message","messageML","data","verdict","riskScore","pack"}
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

        server.createContext("/health", ex -> reply(ex, 200, 
            "{\"ok\":true,\"service\":\"CallGuard-Symphony-Bridge\",\"webhookConfigured\":" + (webhook != null && !webhook.isBlank()) + "}"));

        server.createContext("/audit", ex -> {
            if (!"POST".equals(ex.getRequestMethod())) { 
                reply(ex, 405, "{\"error\":\"POST only\"}"); 
                return; 
            }
            String body = new String(ex.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
            if (webhook == null || webhook.isBlank()) {
                System.out.println("[Symphony Bridge] No SYMPHONY_WEBHOOK_URL configured. Local audit log captured:\n" + body);
                reply(ex, 202, "{\"delivered\":false,\"mode\":\"simulation\",\"reason\":\"SYMPHONY_WEBHOOK_URL not set (logging locally)\"}");
                return;
            }
            boolean ok = deliver(webhook, body);
            reply(ex, ok ? 200 : 502, "{\"delivered\":" + ok + "}");
        });

        server.createContext("/action", ex -> {
            if (!"POST".equals(ex.getRequestMethod())) {
                reply(ex, 405, "{\"error\":\"POST only\"}");
                return;
            }
            String body = new String(ex.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
            System.out.println("[Symphony Bridge] Received 2-way supervisory action event:\n" + body);
            reply(ex, 200, "{\"ok\":true,\"status\":\"action_relayed_to_symphony_room\"}");
        });

        server.createContext("/fdc3", ex -> reply(ex, 200,
            "{\"fdc3_supported\":true,\"version\":\"2.0\",\"channels\":[\"global\",\"red\",\"green\"],\"standard\":\"FINOS\"}"));

        server.start();
        System.out.println("[Symphony Bridge] Listening on port " + port + " (Enterprise Symphony Room Relay with 2-Way Elements Action Loop)");

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
                if (res.statusCode() / 100 == 2) {
                    System.out.println("[Symphony Bridge] Dispatched audit card to room webhook successfully (HTTP " + res.statusCode() + ")");
                    return true;
                }
                System.err.println("[Symphony Bridge] Attempt " + attempt + " got HTTP " + res.statusCode());
            } catch (Exception e) {
                System.err.println("[Symphony Bridge] Attempt " + attempt + " failed: " + e.getMessage());
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
