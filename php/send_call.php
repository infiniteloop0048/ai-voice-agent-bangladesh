<?php
declare(strict_types=1);
require_once __DIR__.'/signature.php';

try {
    $env = voice_environment();
    $payload = @file_get_contents($argv[1] ?? __DIR__.'/../payloads/call-request.json');
    if ($payload === false) {
        throw new RuntimeException('Cannot read call request JSON file.');
    }
    json_decode($payload, true, 512, JSON_THROW_ON_ERROR);
    $context = stream_context_create(['http' => [
        'method' => 'POST',
        'header' => "Authorization: Bearer ".$env['VOICE_API_KEY']."\r\nContent-Type: application/json\r\n",
        'content' => $payload,
        'timeout' => 10,
        'ignore_errors' => true,
        'follow_location' => 0,
    ]]);
    $body = @file_get_contents(rtrim($env['VOICE_API_URL'], '/').'/integrations/call-requests', false, $context);
    $status = 0;
    foreach ($http_response_header ?? [] as $header) {
        if (preg_match('/^HTTP\/\S+\s+(\d{3})/', $header, $match)) {
            $status = (int) $match[1];
        }
    }
    if ($body === false || $status < 200 || $status >= 300) {
        throw new RuntimeException('HTTP '.$status.': '.($body === false ? 'request failed or timed out' : str_replace($env['VOICE_API_KEY'], '[redacted]', $body)));
    }
    echo $body.PHP_EOL;
} catch (Throwable $error) {
    fwrite(STDERR, $error->getMessage().PHP_EOL);
    exit(1);
}
