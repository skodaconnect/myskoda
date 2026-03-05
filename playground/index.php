<?php
/**
 * Skoda Connect API Playground
 *
 * Single-file PHP/HTML app to interact with the Skoda Connect API.
 * Implements the full OAuth2 PKCE authentication flow.
 */

session_start();

// ── Constants ────────────────────────────────────────────────────────────────

define('BASE_URL_SKODA', 'https://mysmob.api.connect.skoda-auto.cz');
define('BASE_URL_IDENT', 'https://identity.vwgroup.io');
define('CLIENT_ID', '7f045eee-7003-4379-9968-9355ed2adb06@apps_vw-dilab_com');
define('REDIRECT_URI', 'myskoda://redirect/login/');
define('OIDC_SCOPES', 'address badge birthdate cars driversLicense dealers email mileage mbb nationalIdentifier openid phone profession profile vin');

// ── Helper functions ─────────────────────────────────────────────────────────

function generateNonce(int $length = 16): string {
    $chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    $nonce = '';
    for ($i = 0; $i < $length; $i++) {
        $nonce .= $chars[random_int(0, strlen($chars) - 1)];
    }
    return $nonce;
}

function generatePKCE(): array {
    $verifier = generateNonce(64);
    $hash = hash('sha256', $verifier, true);
    $challenge = rtrim(strtr(base64_encode($hash), '+/', '-_'), '=');
    return ['verifier' => $verifier, 'challenge' => $challenge];
}

function extractCSRF(string $html): array {
    $result = ['csrf' => '', 'relay_state' => '', 'hmac' => ''];

    // Python reference: myskoda/auth/csrf_parser.py
    // The HTML contains a <script> with: window._IDK = { csrf_token: "...", templateModel: {...} }
    // templateModel is a JSON object containing "hmac" and "relayState" among other fields.
    // We search the full HTML directly — these field names are unique enough.

    // csrf_token — try multiple patterns:
    // 1. Unquoted key in window._IDK block: csrf_token: "..."
    if (preg_match('/csrf_token\s*:\s*"([^"]+)"/s', $html, $m)) {
        $result['csrf'] = $m[1];
    }
    // 2. Quoted key: "csrf_token": "..."
    elseif (preg_match('/"csrf_token"\s*:\s*"([^"]+)"/s', $html, $m)) {
        $result['csrf'] = $m[1];
    }
    // 3. Hidden input field: <input type="hidden" name="_csrf" value="...">
    elseif (preg_match('/name=["\']_csrf["\']\s+value=["\']([^"\']+)["\']/i', $html, $m)) {
        $result['csrf'] = $m[1];
    }
    // 4. Hidden input (reversed attr order): <input value="..." name="_csrf">
    elseif (preg_match('/value=["\']([^"\']+)["\']\s+name=["\']_csrf["\']/i', $html, $m)) {
        $result['csrf'] = $m[1];
    }
    // 5. Meta tag: <meta name="_csrf" content="...">
    elseif (preg_match('/name=["\']_csrf["\']\s+content=["\']([^"\']+)["\']/i', $html, $m)) {
        $result['csrf'] = $m[1];
    }
    // 6. Any key containing "csrf" with a quoted value
    elseif (preg_match('/["\']?csrf[_-]?token["\']?\s*:\s*["\']([^"\']+)["\']/i', $html, $m)) {
        $result['csrf'] = $m[1];
    }

    // hmac and relayState are quoted keys inside the templateModel JSON value
    if (preg_match('/"hmac"\s*:\s*"([^"]+)"/', $html, $m)) {
        $result['hmac'] = $m[1];
    }

    if (preg_match('/"relayState"\s*:\s*"([^"]+)"/', $html, $m)) {
        $result['relay_state'] = $m[1];
    }

    return $result;
}

function curlRequest(string $url, array $options = []): array {
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_HEADER => true,
        CURLOPT_FOLLOWLOCATION => $options['follow'] ?? false,
        CURLOPT_MAXREDIRS => $options['max_redirects'] ?? 10,
        CURLOPT_TIMEOUT => 30,
        CURLOPT_SSL_VERIFYPEER => true,
        CURLOPT_COOKIEFILE => $options['cookie_file'] ?? '',
        CURLOPT_COOKIEJAR => $options['cookie_file'] ?? '',
    ]);

    if (isset($options['post_fields'])) {
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $options['post_fields']);
    }

    if (isset($options['json'])) {
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($options['json']));
        curl_setopt($ch, CURLOPT_HTTPHEADER, array_merge(
            $options['headers'] ?? [],
            ['Content-Type: application/json']
        ));
    }

    if (isset($options['method'])) {
        curl_setopt($ch, CURLOPT_CUSTOMREQUEST, strtoupper($options['method']));
        if (isset($options['json'])) {
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($options['json']));
            curl_setopt($ch, CURLOPT_HTTPHEADER, array_merge(
                $options['headers'] ?? [],
                ['Content-Type: application/json']
            ));
        }
    }

    if (isset($options['headers']) && !isset($options['json']) && !isset($options['method'])) {
        curl_setopt($ch, CURLOPT_HTTPHEADER, $options['headers']);
    }

    $response = curl_exec($ch);
    $err = curl_error($ch);
    $info = curl_getinfo($ch);
    curl_close($ch);

    $header_size = $info['header_size'] ?? 0;
    $headers_raw = substr($response, 0, $header_size);
    $body = substr($response, $header_size);

    // Extract Location header
    $location = '';
    if (preg_match('/^Location:\s*(.+)$/mi', $headers_raw, $m)) {
        $location = trim($m[1]);
    }

    return [
        'body' => $body,
        'status' => $info['http_code'],
        'location' => $location,
        'error' => $err,
        'url' => $info['url'] ?? $url,
    ];
}

function apiRequest(string $method, string $path, ?array $json = null): array {
    $token = $_SESSION['access_token'] ?? '';
    $url = BASE_URL_SKODA . '/api' . $path;

    $options = [
        'headers' => ["Authorization: Bearer $token"],
        'method' => $method,
    ];

    if ($json !== null) {
        $options['json'] = $json;
        $options['headers'][] = 'Content-Type: application/json';
    }

    $start = microtime(true);
    $result = curlRequest($url, $options);
    $duration = round((microtime(true) - $start) * 1000);

    return [
        'method' => $method,
        'url' => $url,
        'status' => $result['status'],
        'body' => $result['body'],
        'error' => $result['error'],
        'duration_ms' => $duration,
    ];
}

// ── Auth Flow ────────────────────────────────────────────────────────────────

function performLogin(string $email, string $password): array {
    $cookieFile = tempnam(sys_get_temp_dir(), 'skoda_');
    $cookieOpts = ['cookie_file' => $cookieFile];

    // Step 1: OIDC Authorize
    $pkce = generatePKCE();
    $params = http_build_query([
        'client_id' => CLIENT_ID,
        'nonce' => generateNonce(),
        'redirect_uri' => REDIRECT_URI,
        'response_type' => 'code',
        'scope' => OIDC_SCOPES,
        'code_challenge' => $pkce['challenge'],
        'code_challenge_method' => 's256',
        'prompt' => 'login',
    ]);

    $authorizeUrl = BASE_URL_IDENT . "/oidc/v1/authorize?$params";
    $resp = curlRequest($authorizeUrl, array_merge($cookieOpts, ['follow' => true]));

    $debug = [];
    $debug['step1'] = [
        'url' => $authorizeUrl,
        'final_url' => $resp['url'],
        'status' => $resp['status'],
        'curl_error' => $resp['error'] ?: null,
        'body_length' => strlen($resp['body']),
        'body_snippet' => substr($resp['body'], 0, 500),
        'has_window_idk' => str_contains($resp['body'], 'window._IDK'),
    ];

    if ($resp['error']) return ['error' => "Step 1 failed: {$resp['error']}", 'debug' => $debug];

    $csrf = extractCSRF($resp['body']);
    $debug['step1']['csrf_result'] = $csrf;

    if (!$csrf['csrf']) {
        // Show the full window._IDK script tag content for debugging
        if (preg_match('/(window\._IDK\s*=\s*\{.{0,3000})/s', $resp['body'], $idkMatch)) {
            $debug['step1']['idk_block_3000chars'] = $idkMatch[1];
        }
        // Check if the literal strings exist in the body
        $debug['step1']['has_csrf_token_string'] = str_contains($resp['body'], 'csrf_token');
        $debug['step1']['has__csrf_string'] = str_contains($resp['body'], '_csrf');
        $debug['step1']['has_csrfToken_string'] = str_contains($resp['body'], 'csrfToken');
        // Find all occurrences of "csrf" with context
        preg_match_all('/(.{0,60}csrf.{0,60})/i', $resp['body'], $csrfMatches);
        $debug['step1']['csrf_occurrences'] = array_values(array_unique(
            array_map(fn($s) => trim(preg_replace('/\s+/', ' ', $s)), $csrfMatches[0] ?? [])
        ));
        // Also check for hidden input fields
        preg_match_all('/<input[^>]*type=["\']hidden["\'][^>]*>/i', $resp['body'], $hiddenInputs);
        $debug['step1']['hidden_inputs'] = $hiddenInputs[0] ?? [];
        return ['error' => 'Step 1: Could not extract CSRF token', 'debug' => $debug];
    }

    // Step 2: Submit email
    $postData = http_build_query([
        'relayState' => $csrf['relay_state'],
        'email' => $email,
        'hmac' => $csrf['hmac'],
        '_csrf' => $csrf['csrf'],
    ]);

    $step2Url = BASE_URL_IDENT . "/signin-service/v1/" . CLIENT_ID . "/login/identifier";
    $resp = curlRequest(
        $step2Url,
        array_merge($cookieOpts, ['post_fields' => $postData, 'follow' => true])
    );

    $debug['step2'] = [
        'url' => $step2Url,
        'final_url' => $resp['url'],
        'status' => $resp['status'],
        'curl_error' => $resp['error'] ?: null,
        'body_length' => strlen($resp['body']),
        'body_snippet' => substr($resp['body'], 0, 500),
        'has_window_idk' => str_contains($resp['body'], 'window._IDK'),
    ];

    if ($resp['error']) return ['error' => "Step 2 failed: {$resp['error']}", 'debug' => $debug];

    $csrf = extractCSRF($resp['body']);
    $debug['step2']['csrf_result'] = $csrf;

    if (!$csrf['csrf']) {
        preg_match_all('/<script[^>]*>(.*?)<\/script>/si', $resp['body'], $scripts);
        $debug['step2']['script_contents'] = array_map(fn($s) => substr(trim($s), 0, 300), $scripts[1] ?? []);
        return ['error' => 'Step 2: Could not extract CSRF token from email step', 'debug' => $debug];
    }

    // Step 3: Submit password (no follow, manual redirect chase)
    $postData = http_build_query([
        'relayState' => $csrf['relay_state'],
        'email' => $email,
        'password' => $password,
        'hmac' => $csrf['hmac'],
        '_csrf' => $csrf['csrf'],
    ]);

    $resp = curlRequest(
        BASE_URL_IDENT . "/signin-service/v1/" . CLIENT_ID . "/login/authenticate",
        array_merge($cookieOpts, ['post_fields' => $postData, 'follow' => false])
    );

    $location = $resp['location'];
    $maxRedirects = 20;
    $i = 0;

    while ($location && !str_starts_with($location, 'myskoda://') && $i < $maxRedirects) {
        if (str_contains($location, 'terms-and-conditions')) {
            @unlink($cookieFile);
            return ['error' => 'Terms and Conditions müssen zuerst im Browser akzeptiert werden.'];
        }
        if (str_contains($location, 'consent/marketing')) {
            @unlink($cookieFile);
            return ['error' => 'Marketing Consent muss zuerst im Browser akzeptiert werden.'];
        }
        $resp = curlRequest($location, array_merge($cookieOpts, ['follow' => false]));
        $location = $resp['location'];
        $i++;
    }

    @unlink($cookieFile);

    if (!$location || !str_starts_with($location, 'myskoda://')) {
        return ['error' => 'Step 3: Could not follow redirects to myskoda:// URL'];
    }

    // Extract code from redirect URL
    parse_str(parse_url($location, PHP_URL_QUERY) ?? '', $queryParams);
    $code = $queryParams['code'] ?? '';
    if (!$code) return ['error' => 'Step 3: No authorization code in redirect URL'];

    // Step 4: Exchange code for tokens
    $resp = curlRequest(
        BASE_URL_SKODA . '/api/v1/authentication/exchange-authorization-code?tokenType=CONNECT',
        ['json' => [
            'code' => $code,
            'redirectUri' => REDIRECT_URI,
            'verifier' => $pkce['verifier'],
        ]]
    );

    $tokens = json_decode($resp['body'], true);
    if (!$tokens || !isset($tokens['accessToken'])) {
        return ['error' => 'Step 4: Failed to exchange authorization code', 'raw' => $resp['body']];
    }

    return [
        'access_token' => $tokens['accessToken'],
        'refresh_token' => $tokens['refreshToken'],
        'id_token' => $tokens['idToken'] ?? '',
    ];
}

function refreshToken(string $refresh_token): array {
    $resp = curlRequest(
        BASE_URL_SKODA . '/api/v1/authentication/refresh-token?tokenType=CONNECT',
        ['json' => ['token' => $refresh_token]]
    );

    $tokens = json_decode($resp['body'], true);
    if (!$tokens || !isset($tokens['accessToken'])) {
        return ['error' => 'Token refresh failed', 'raw' => $resp['body']];
    }

    return [
        'access_token' => $tokens['accessToken'],
        'refresh_token' => $tokens['refreshToken'],
        'id_token' => $tokens['idToken'] ?? '',
    ];
}

// ── Handle AJAX requests ─────────────────────────────────────────────────────

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action'])) {
    header('Content-Type: application/json');

    $action = $_POST['action'];

    if ($action === 'login') {
        $email = $_POST['email'] ?? '';
        $password = $_POST['password'] ?? '';
        if (!$email || !$password) {
            echo json_encode(['error' => 'E-Mail und Passwort sind erforderlich.']);
            exit;
        }
        $result = performLogin($email, $password);
        if (isset($result['access_token'])) {
            $_SESSION['access_token'] = $result['access_token'];
            $_SESSION['refresh_token'] = $result['refresh_token'];
            $_SESSION['id_token'] = $result['id_token'];
            $_SESSION['logged_in'] = true;
        }
        echo json_encode($result);
        exit;
    }

    if ($action === 'refresh') {
        $rt = $_SESSION['refresh_token'] ?? '';
        if (!$rt) {
            echo json_encode(['error' => 'Kein Refresh Token vorhanden.']);
            exit;
        }
        $result = refreshToken($rt);
        if (isset($result['access_token'])) {
            $_SESSION['access_token'] = $result['access_token'];
            $_SESSION['refresh_token'] = $result['refresh_token'];
            $_SESSION['id_token'] = $result['id_token'];
        }
        echo json_encode($result);
        exit;
    }

    if ($action === 'logout') {
        session_destroy();
        echo json_encode(['ok' => true]);
        exit;
    }

    if ($action === 'api_call') {
        if (empty($_SESSION['access_token'])) {
            echo json_encode(['error' => 'Nicht eingeloggt.']);
            exit;
        }
        $method = strtoupper($_POST['method'] ?? 'GET');
        $path = $_POST['path'] ?? '';
        $body = $_POST['body'] ?? '';

        $json = null;
        if ($body) {
            $json = json_decode($body, true);
            if ($json === null && $body !== 'null') {
                echo json_encode(['error' => 'Ungültiges JSON im Request Body.']);
                exit;
            }
        }

        $result = apiRequest($method, $path, $json);
        // Try to pretty-print the response
        $decoded = json_decode($result['body'], true);
        if ($decoded !== null) {
            $result['body_formatted'] = json_encode($decoded, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
        }
        echo json_encode($result);
        exit;
    }

    echo json_encode(['error' => 'Unknown action']);
    exit;
}

$isLoggedIn = !empty($_SESSION['logged_in']);
?>
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Skoda Connect API Playground</title>
    <style>
        :root {
            --bg: #0f1117;
            --surface: #1a1d27;
            --surface2: #242836;
            --border: #2e3345;
            --text: #e1e4ed;
            --text-dim: #8b90a0;
            --green: #4ade80;
            --green-dim: #166534;
            --blue: #60a5fa;
            --red: #f87171;
            --yellow: #fbbf24;
            --accent: #818cf8;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.5;
        }

        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 24px;
        }

        header h1 { font-size: 1.4rem; font-weight: 600; }
        header h1 span { color: var(--green); }

        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
        }

        .status-badge.online { background: var(--green-dim); color: var(--green); }
        .status-badge.offline { background: #3b1c1c; color: var(--red); }
        .status-badge .dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; }

        /* Login form */
        .login-card {
            max-width: 420px;
            margin: 80px auto;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 32px;
        }

        .login-card h2 { margin-bottom: 24px; font-size: 1.2rem; }

        .form-group { margin-bottom: 16px; }
        .form-group label { display: block; font-size: 0.85rem; color: var(--text-dim); margin-bottom: 6px; }

        input, select, textarea {
            width: 100%;
            padding: 10px 12px;
            background: var(--surface2);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text);
            font-size: 0.9rem;
            font-family: inherit;
        }

        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: var(--accent);
        }

        textarea { resize: vertical; font-family: 'SF Mono', 'Fira Code', monospace; font-size: 0.85rem; }

        button, .btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
            transition: opacity 0.2s;
            font-family: inherit;
        }

        button:hover { opacity: 0.85; }
        button:disabled { opacity: 0.5; cursor: not-allowed; }

        .btn-primary { background: var(--accent); color: white; }
        .btn-green { background: var(--green); color: #000; }
        .btn-red { background: #dc2626; color: white; }
        .btn-ghost { background: var(--surface2); color: var(--text); border: 1px solid var(--border); }
        .btn-sm { padding: 6px 12px; font-size: 0.8rem; }

        /* Layout */
        .main-grid {
            display: grid;
            grid-template-columns: 320px 1fr;
            gap: 20px;
            min-height: calc(100vh - 140px);
        }

        @media (max-width: 900px) {
            .main-grid { grid-template-columns: 1fr; }
        }

        /* Sidebar */
        .sidebar {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px;
            overflow-y: auto;
            max-height: calc(100vh - 140px);
            position: sticky;
            top: 20px;
        }

        .sidebar h3 {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-dim);
            margin: 16px 0 8px;
        }

        .sidebar h3:first-child { margin-top: 0; }

        .endpoint-btn {
            display: flex;
            align-items: center;
            gap: 8px;
            width: 100%;
            padding: 8px 10px;
            background: transparent;
            border: 1px solid transparent;
            border-radius: 6px;
            color: var(--text);
            font-size: 0.8rem;
            text-align: left;
            cursor: pointer;
            transition: background 0.15s;
        }

        .endpoint-btn:hover { background: var(--surface2); border-color: var(--border); opacity: 1; }
        .endpoint-btn.active { background: var(--surface2); border-color: var(--accent); }

        .method-tag {
            display: inline-block;
            padding: 1px 6px;
            border-radius: 4px;
            font-size: 0.65rem;
            font-weight: 700;
            font-family: 'SF Mono', 'Fira Code', monospace;
            flex-shrink: 0;
            min-width: 38px;
            text-align: center;
        }

        .method-tag.get { background: #1e3a5f; color: var(--blue); }
        .method-tag.post { background: #1a3328; color: var(--green); }
        .method-tag.put { background: #3b2e10; color: var(--yellow); }

        .endpoint-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

        /* Request panel */
        .request-panel {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
        }

        .request-panel h2 { font-size: 1.1rem; margin-bottom: 16px; }

        .request-bar {
            display: flex;
            gap: 8px;
            margin-bottom: 16px;
        }

        .request-bar select { width: 100px; flex-shrink: 0; }
        .request-bar input { flex: 1; font-family: 'SF Mono', 'Fira Code', monospace; font-size: 0.85rem; }

        .param-row {
            display: flex;
            gap: 8px;
            margin-bottom: 8px;
            align-items: center;
        }

        .param-row input { flex: 1; }
        .param-row .btn-sm { flex-shrink: 0; }

        .section-label {
            font-size: 0.8rem;
            color: var(--text-dim);
            margin: 16px 0 8px;
            font-weight: 600;
        }

        /* Response */
        .response-section { margin-top: 24px; }

        .response-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }

        .response-meta { display: flex; gap: 16px; font-size: 0.8rem; }
        .response-meta span { color: var(--text-dim); }
        .response-meta .status-ok { color: var(--green); font-weight: 600; }
        .response-meta .status-err { color: var(--red); font-weight: 600; }

        .response-body {
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            font-family: 'SF Mono', 'Fira Code', monospace;
            font-size: 0.8rem;
            line-height: 1.6;
            overflow-x: auto;
            white-space: pre-wrap;
            word-break: break-word;
            max-height: 500px;
            overflow-y: auto;
            color: var(--text-dim);
        }

        .response-body .key { color: var(--accent); }
        .response-body .string { color: var(--green); }
        .response-body .number { color: var(--yellow); }
        .response-body .bool { color: var(--blue); }
        .response-body .null { color: var(--red); }

        .loading {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid var(--border);
            border-top-color: var(--accent);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin { to { transform: rotate(360deg); } }

        .toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 12px 20px;
            background: var(--surface2);
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 0.85rem;
            z-index: 1000;
            animation: fadeIn 0.3s ease;
        }

        .toast.error { border-color: var(--red); color: var(--red); }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        .vin-bar {
            display: flex;
            gap: 8px;
            margin-bottom: 16px;
            padding: 12px;
            background: var(--surface2);
            border-radius: 8px;
        }

        .vin-bar label { font-size: 0.8rem; color: var(--text-dim); white-space: nowrap; align-self: center; }
        .vin-bar input { flex: 1; background: var(--surface); }

        .info-text { font-size: 0.8rem; color: var(--text-dim); margin-bottom: 16px; }
        .info-text code { background: var(--surface2); padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; }

        .header-actions { display: flex; align-items: center; gap: 12px; }
    </style>
</head>
<body>

<div class="container">
    <header>
        <h1><span>Skoda</span> API Playground</h1>
        <div class="header-actions">
            <span class="status-badge <?= $isLoggedIn ? 'online' : 'offline' ?>" id="statusBadge">
                <span class="dot"></span>
                <span id="statusText"><?= $isLoggedIn ? 'Verbunden' : 'Nicht verbunden' ?></span>
            </span>
            <?php if ($isLoggedIn): ?>
                <button class="btn-ghost btn-sm" onclick="doRefresh()">Token Refresh</button>
                <button class="btn-red btn-sm" onclick="doLogout()">Logout</button>
            <?php endif; ?>
        </div>
    </header>

    <?php if (!$isLoggedIn): ?>

    <!-- LOGIN -->
    <div class="login-card">
        <h2>Anmelden</h2>
        <p class="info-text">Login über den VW Identity Server (OAuth2 PKCE). Verwendet die gleiche Authentifizierung wie die MySkoda App.</p>
        <form id="loginForm" onsubmit="doLogin(event)">
            <div class="form-group">
                <label>E-Mail</label>
                <input type="email" id="loginEmail" required placeholder="name@example.com" autocomplete="email">
            </div>
            <div class="form-group">
                <label>Passwort</label>
                <input type="password" id="loginPassword" required placeholder="Passwort" autocomplete="current-password">
            </div>
            <button type="submit" class="btn-primary" id="loginBtn" style="width:100%; justify-content:center;">
                Anmelden
            </button>
        </form>
        <div id="loginError" style="margin-top:12px; color:var(--red); font-size:0.85rem; display:none;"></div>
        <div id="loginDebug" style="margin-top:12px; display:none; background:var(--bg); border:1px solid var(--border); border-radius:8px; padding:12px; max-height:400px; overflow:auto;">
            <div style="font-size:0.75rem; color:var(--text-dim); margin-bottom:8px; font-weight:600;">Debug-Informationen</div>
            <pre id="loginDebugContent" style="font-family:'SF Mono','Fira Code',monospace; font-size:0.75rem; color:var(--text-dim); white-space:pre-wrap; word-break:break-all;"></pre>
        </div>
    </div>

    <?php else: ?>

    <!-- PLAYGROUND -->
    <div class="main-grid">
        <aside class="sidebar">
            <div class="vin-bar">
                <label>VIN</label>
                <input type="text" id="vinInput" placeholder="TMBJM0..." value="">
            </div>

            <h3>Benutzer & Garage</h3>
            <button class="endpoint-btn" onclick="loadEndpoint('GET', '/v1/users', 'Benutzer')">
                <span class="method-tag get">GET</span>
                <span class="endpoint-name">Benutzer-Info</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('GET', '/v2/garage?connectivityGenerations=MOD1&connectivityGenerations=MOD2&connectivityGenerations=MOD3&connectivityGenerations=MOD4', 'Garage')">
                <span class="method-tag get">GET</span>
                <span class="endpoint-name">Garage (alle Fahrzeuge)</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('GET', '/v2/garage/vehicles/{vin}?connectivityGenerations=MOD1&connectivityGenerations=MOD2&connectivityGenerations=MOD3&connectivityGenerations=MOD4', 'Fahrzeug-Details')">
                <span class="method-tag get">GET</span>
                <span class="endpoint-name">Fahrzeug-Details</span>
            </button>

            <h3>Fahrzeugstatus</h3>
            <button class="endpoint-btn" onclick="loadEndpoint('GET', '/v2/vehicle-status/{vin}', 'Status')">
                <span class="method-tag get">GET</span>
                <span class="endpoint-name">Fahrzeugstatus</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('GET', '/v2/vehicle-status/{vin}/driving-range', 'Reichweite')">
                <span class="method-tag get">GET</span>
                <span class="endpoint-name">Reichweite</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('GET', '/v2/connection-status/{vin}/readiness', 'Verbindung')">
                <span class="method-tag get">GET</span>
                <span class="endpoint-name">Verbindungsstatus</span>
            </button>

            <h3>Laden</h3>
            <button class="endpoint-btn" onclick="loadEndpoint('GET', '/v1/charging/{vin}', 'Ladestatus')">
                <span class="method-tag get">GET</span>
                <span class="endpoint-name">Ladestatus</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('GET', '/v1/charging/{vin}/profiles', 'Ladeprofile')">
                <span class="method-tag get">GET</span>
                <span class="endpoint-name">Ladeprofile</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('GET', '/v1/charging/{vin}/history?userTimezone=UTC&limit=50', 'Lade-Verlauf')">
                <span class="method-tag get">GET</span>
                <span class="endpoint-name">Lade-Verlauf</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('POST', '/v1/charging/{vin}/start', 'Laden starten')">
                <span class="method-tag post">POST</span>
                <span class="endpoint-name">Laden starten</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('POST', '/v1/charging/{vin}/stop', 'Laden stoppen')">
                <span class="method-tag post">POST</span>
                <span class="endpoint-name">Laden stoppen</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('POST', '/v1/charging/{vin}/set-charge-mode', 'Lademodus', JSON.stringify({chargeMode: 'MANUAL'}, null, 2))">
                <span class="method-tag post">POST</span>
                <span class="endpoint-name">Lademodus setzen</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('PUT', '/v1/charging/{vin}/set-charge-limit', 'Ladelimit', JSON.stringify({targetSOCInPercent: 80}, null, 2))">
                <span class="method-tag put">PUT</span>
                <span class="endpoint-name">Ladelimit setzen</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('PUT', '/v1/charging/{vin}/set-care-mode', 'Batteriepflege', JSON.stringify({chargingCareMode: 'ACTIVATED'}, null, 2))">
                <span class="method-tag put">PUT</span>
                <span class="endpoint-name">Batteriepflege</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('PUT', '/v1/charging/{vin}/set-auto-unlock-plug', 'Auto-Unlock', JSON.stringify({autoUnlockPlug: 'PERMANENT'}, null, 2))">
                <span class="method-tag put">PUT</span>
                <span class="endpoint-name">Auto-Unlock Stecker</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('PUT', '/v1/charging/{vin}/set-charging-current', 'Ladestrom', JSON.stringify({chargingCurrent: 'MAXIMUM'}, null, 2))">
                <span class="method-tag put">PUT</span>
                <span class="endpoint-name">Ladestrom</span>
            </button>

            <h3>Klimaanlage</h3>
            <button class="endpoint-btn" onclick="loadEndpoint('GET', '/v2/air-conditioning/{vin}', 'Klima-Status')">
                <span class="method-tag get">GET</span>
                <span class="endpoint-name">Klima-Status</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('POST', '/v2/air-conditioning/{vin}/start', 'Klima starten', JSON.stringify({heaterSource: 'ELECTRIC', targetTemperature: {temperatureValue: 22.0, unitInCar: 'CELSIUS'}}, null, 2))">
                <span class="method-tag post">POST</span>
                <span class="endpoint-name">Klima starten</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('POST', '/v2/air-conditioning/{vin}/stop', 'Klima stoppen')">
                <span class="method-tag post">POST</span>
                <span class="endpoint-name">Klima stoppen</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('POST', '/v2/air-conditioning/{vin}/active-ventilation/start', 'Lüftung starten')">
                <span class="method-tag post">POST</span>
                <span class="endpoint-name">Lüftung starten</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('POST', '/v2/air-conditioning/{vin}/active-ventilation/stop', 'Lüftung stoppen')">
                <span class="method-tag post">POST</span>
                <span class="endpoint-name">Lüftung stoppen</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('POST', '/v2/air-conditioning/{vin}/start-window-heating', 'Scheiben heizen')">
                <span class="method-tag post">POST</span>
                <span class="endpoint-name">Scheibenheizung an</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('POST', '/v2/air-conditioning/{vin}/stop-window-heating', 'Scheiben aus')">
                <span class="method-tag post">POST</span>
                <span class="endpoint-name">Scheibenheizung aus</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('POST', '/v2/air-conditioning/{vin}/settings/target-temperature', 'Temperatur', JSON.stringify({temperatureValue: 22.0, unitInCar: 'CELSIUS'}, null, 2))">
                <span class="method-tag post">POST</span>
                <span class="endpoint-name">Zieltemperatur</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('POST', '/v2/air-conditioning/{vin}/settings/ac-at-unlock', 'Klima Unlock', JSON.stringify({airConditioningAtUnlockEnabled: true}, null, 2))">
                <span class="method-tag post">POST</span>
                <span class="endpoint-name">Klima bei Unlock</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('POST', '/v2/air-conditioning/{vin}/settings/ac-without-external-power', 'Klima ohne Strom', JSON.stringify({airConditioningWithoutExternalPowerEnabled: true}, null, 2))">
                <span class="method-tag post">POST</span>
                <span class="endpoint-name">Klima ohne ext. Strom</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('POST', '/v2/air-conditioning/{vin}/settings/windows-heating', 'Scheibenheizung', JSON.stringify({windowHeatingEnabled: true}, null, 2))">
                <span class="method-tag post">POST</span>
                <span class="endpoint-name">Scheibenheizung Einst.</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('POST', '/v2/air-conditioning/{vin}/settings/seats-heating', 'Sitzheizung', JSON.stringify({frontLeft: true, frontRight: true}, null, 2))">
                <span class="method-tag post">POST</span>
                <span class="endpoint-name">Sitzheizung Einst.</span>
            </button>

            <h3>Standheizung</h3>
            <button class="endpoint-btn" onclick="loadEndpoint('GET', '/v2/air-conditioning/{vin}/auxiliary-heating', 'Standheizung')">
                <span class="method-tag get">GET</span>
                <span class="endpoint-name">Standheizung-Status</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('POST', '/v2/air-conditioning/{vin}/auxiliary-heating/start', 'Standheizung an', JSON.stringify({spin: '0000'}, null, 2))">
                <span class="method-tag post">POST</span>
                <span class="endpoint-name">Standheizung starten</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('POST', '/v2/air-conditioning/{vin}/auxiliary-heating/stop', 'Standheizung aus')">
                <span class="method-tag post">POST</span>
                <span class="endpoint-name">Standheizung stoppen</span>
            </button>

            <h3>Position</h3>
            <button class="endpoint-btn" onclick="loadEndpoint('GET', '/v1/maps/positions?vin={vin}', 'Position')">
                <span class="method-tag get">GET</span>
                <span class="endpoint-name">Aktuelle Position</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('GET', '/v3/maps/positions/vehicles/{vin}/parking', 'Parkposition')">
                <span class="method-tag get">GET</span>
                <span class="endpoint-name">Parkposition</span>
            </button>

            <h3>Fahrten</h3>
            <button class="endpoint-btn" onclick="loadEndpoint('GET', '/v1/trip-statistics/{vin}?offsetType=week&offset=0&timezone=Europe%2FBerlin', 'Fahrstatistik')">
                <span class="method-tag get">GET</span>
                <span class="endpoint-name">Fahrstatistiken</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('GET', '/v1/trip-statistics/{vin}/single-trips?timezone=Europe%2FBerlin', 'Einzelfahrten')">
                <span class="method-tag get">GET</span>
                <span class="endpoint-name">Einzelfahrten</span>
            </button>

            <h3>Wartung & Gesundheit</h3>
            <button class="endpoint-btn" onclick="loadEndpoint('GET', '/v3/vehicle-maintenance/vehicles/{vin}', 'Wartung')">
                <span class="method-tag get">GET</span>
                <span class="endpoint-name">Wartungsinfo</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('GET', '/v3/vehicle-maintenance/vehicles/{vin}/report', 'Wartungsbericht')">
                <span class="method-tag get">GET</span>
                <span class="endpoint-name">Wartungsbericht</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('GET', '/v1/vehicle-health-report/warning-lights/{vin}', 'Warnleuchten')">
                <span class="method-tag get">GET</span>
                <span class="endpoint-name">Warnleuchten</span>
            </button>

            <h3>Timer</h3>
            <button class="endpoint-btn" onclick="loadEndpoint('GET', '/v1/vehicle-automatization/{vin}/departure/timers?deviceDateTime=' + encodeURIComponent(new Date().toISOString()), 'Abfahrtstimer')">
                <span class="method-tag get">GET</span>
                <span class="endpoint-name">Abfahrtstimer</span>
            </button>

            <h3>Fahrzeugzugriff</h3>
            <button class="endpoint-btn" onclick="loadEndpoint('POST', '/v1/vehicle-access/{vin}/lock', 'Verriegeln', JSON.stringify({currentSpin: '0000'}, null, 2))">
                <span class="method-tag post">POST</span>
                <span class="endpoint-name">Verriegeln</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('POST', '/v1/vehicle-access/{vin}/unlock', 'Entriegeln', JSON.stringify({currentSpin: '0000'}, null, 2))">
                <span class="method-tag post">POST</span>
                <span class="endpoint-name">Entriegeln</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('POST', '/v1/vehicle-access/{vin}/honk-and-flash', 'Hupen', JSON.stringify({mode: 'HONK_AND_FLASH', vehiclePosition: {latitude: 0, longitude: 0}}, null, 2))">
                <span class="method-tag post">POST</span>
                <span class="endpoint-name">Hupen & Blinken</span>
            </button>

            <h3>Sonstige</h3>
            <button class="endpoint-btn" onclick="loadEndpoint('POST', '/v1/vehicle-wakeup/{vin}?applyRequestLimiter=true', 'Wakeup')">
                <span class="method-tag post">POST</span>
                <span class="endpoint-name">Fahrzeug aufwecken</span>
            </button>
            <button class="endpoint-btn" onclick="loadEndpoint('POST', '/v1/spin/verify', 'SPIN prüfen', JSON.stringify({currentSpin: '0000'}, null, 2))">
                <span class="method-tag post">POST</span>
                <span class="endpoint-name">S-PIN verifizieren</span>
            </button>
        </aside>

        <main class="request-panel">
            <h2 id="endpointTitle">Request</h2>

            <p class="info-text" id="endpointHint">Wähle einen Endpoint aus der linken Sidebar oder gib einen eigenen ein.</p>

            <div class="request-bar">
                <select id="reqMethod">
                    <option value="GET">GET</option>
                    <option value="POST">POST</option>
                    <option value="PUT">PUT</option>
                </select>
                <input type="text" id="reqPath" placeholder="/v2/vehicle-status/{vin}">
                <button class="btn-green" onclick="sendRequest()" id="sendBtn">Senden</button>
            </div>

            <div id="bodySection" style="display:none;">
                <div class="section-label">Request Body (JSON)</div>
                <textarea id="reqBody" rows="6" placeholder='{"key": "value"}'></textarea>
            </div>

            <div class="response-section" id="responseSection" style="display:none;">
                <div class="response-header">
                    <div class="section-label" style="margin:0;">Response</div>
                    <div class="response-meta">
                        <span>Status: <strong id="respStatus" class="status-ok">200</strong></span>
                        <span>Zeit: <strong id="respTime">0</strong> ms</span>
                        <span>URL: <code id="respUrl" style="font-size:0.75rem;"></code></span>
                    </div>
                </div>
                <div class="response-body" id="respBody"></div>
            </div>
        </main>
    </div>

    <?php endif; ?>
</div>

<script>
// ── Login ──────────────────────────────────────────────────────────────────

async function doLogin(e) {
    e.preventDefault();
    const btn = document.getElementById('loginBtn');
    const errEl = document.getElementById('loginError');
    btn.disabled = true;
    btn.innerHTML = '<span class="loading"></span> Anmeldung läuft...';
    errEl.style.display = 'none';

    const form = new FormData();
    form.append('action', 'login');
    form.append('email', document.getElementById('loginEmail').value);
    form.append('password', document.getElementById('loginPassword').value);

    try {
        const resp = await fetch('', { method: 'POST', body: form });
        const data = await resp.json();
        if (data.error) {
            errEl.textContent = data.error;
            errEl.style.display = 'block';
            if (data.debug) {
                const debugEl = document.getElementById('loginDebug');
                const debugContent = document.getElementById('loginDebugContent');
                debugContent.textContent = JSON.stringify(data.debug, null, 2);
                debugEl.style.display = 'block';
            }
            btn.disabled = false;
            btn.innerHTML = 'Anmelden';
        } else {
            location.reload();
        }
    } catch (err) {
        errEl.textContent = 'Netzwerkfehler: ' + err.message;
        errEl.style.display = 'block';
        btn.disabled = false;
        btn.innerHTML = 'Anmelden';
    }
}

// ── Logout & Refresh ───────────────────────────────────────────────────────

async function doLogout() {
    const form = new FormData();
    form.append('action', 'logout');
    await fetch('', { method: 'POST', body: form });
    location.reload();
}

async function doRefresh() {
    const form = new FormData();
    form.append('action', 'refresh');
    const resp = await fetch('', { method: 'POST', body: form });
    const data = await resp.json();
    if (data.error) {
        showToast(data.error, true);
    } else {
        showToast('Token erfolgreich erneuert');
    }
}

// ── Endpoint loading ───────────────────────────────────────────────────────

function loadEndpoint(method, path, title, body) {
    const vin = document.getElementById('vinInput').value.trim();
    if (path.includes('{vin}') && !vin) {
        showToast('Bitte zuerst eine VIN eingeben', true);
        document.getElementById('vinInput').focus();
        return;
    }

    path = path.replace(/\{vin\}/g, vin);

    document.getElementById('reqMethod').value = method;
    document.getElementById('reqPath').value = path;
    document.getElementById('endpointTitle').textContent = title || 'Request';

    const bodySection = document.getElementById('bodySection');
    const bodyInput = document.getElementById('reqBody');

    if (body) {
        bodySection.style.display = 'block';
        bodyInput.value = body;
    } else {
        bodySection.style.display = (method !== 'GET') ? 'block' : 'none';
        bodyInput.value = '';
    }

    // Mark active
    document.querySelectorAll('.endpoint-btn').forEach(b => b.classList.remove('active'));
    if (event && event.currentTarget) event.currentTarget.classList.add('active');
}

// Show/hide body section on method change
document.getElementById('reqMethod')?.addEventListener('change', function() {
    document.getElementById('bodySection').style.display = this.value === 'GET' ? 'none' : 'block';
});

// ── Send request ───────────────────────────────────────────────────────────

async function sendRequest() {
    const method = document.getElementById('reqMethod').value;
    const path = document.getElementById('reqPath').value.trim();
    const body = document.getElementById('reqBody').value.trim();
    const btn = document.getElementById('sendBtn');

    if (!path) {
        showToast('Bitte einen Pfad eingeben', true);
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<span class="loading"></span>';

    const form = new FormData();
    form.append('action', 'api_call');
    form.append('method', method);
    form.append('path', path);
    if (body && method !== 'GET') {
        form.append('body', body);
    }

    try {
        const resp = await fetch('', { method: 'POST', body: form });
        const data = await resp.json();

        if (data.error && !data.status) {
            showToast(data.error, true);
            btn.disabled = false;
            btn.innerHTML = 'Senden';
            return;
        }

        document.getElementById('responseSection').style.display = 'block';

        const statusEl = document.getElementById('respStatus');
        statusEl.textContent = data.status;
        statusEl.className = (data.status >= 200 && data.status < 300) ? 'status-ok' : 'status-err';

        document.getElementById('respTime').textContent = data.duration_ms || '?';
        document.getElementById('respUrl').textContent = data.url || '';

        const bodyContent = data.body_formatted || data.body || '';
        document.getElementById('respBody').innerHTML = syntaxHighlight(bodyContent);
    } catch (err) {
        showToast('Fehler: ' + err.message, true);
    }

    btn.disabled = false;
    btn.innerHTML = 'Senden';
}

// ── JSON syntax highlighting ───────────────────────────────────────────────

function syntaxHighlight(json) {
    if (!json) return '<span class="null">(leer)</span>';

    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

    return json.replace(
        /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
        function(match) {
            let cls = 'number';
            if (/^"/.test(match)) {
                if (/:$/.test(match)) {
                    cls = 'key';
                } else {
                    cls = 'string';
                }
            } else if (/true|false/.test(match)) {
                cls = 'bool';
            } else if (/null/.test(match)) {
                cls = 'null';
            }
            return '<span class="' + cls + '">' + match + '</span>';
        }
    );
}

// ── Toast ──────────────────────────────────────────────────────────────────

function showToast(msg, isError) {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const el = document.createElement('div');
    el.className = 'toast' + (isError ? ' error' : '');
    el.textContent = msg;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 4000);
}
</script>

</body>
</html>
