<?php
declare(strict_types=1);

function voice_environment(): array
{
    $env = [];
    foreach (['VOICE_API_URL', 'VOICE_API_KEY', 'VOICE_WEBHOOK_SECRET'] as $name) {
        $value = getenv($name);
        if ($value === false || $value === '') {
            throw new RuntimeException('Missing environment variable: '.$name);
        }
        $env[$name] = $value;
    }
    return $env;
}

function verify_signature(string $rawBody, ?string $timestamp, ?string $signature, string $secret, ?int $now = null): bool
{
    if ($timestamp === null || $timestamp === '' || $signature === null || $signature === '' || $secret === '') {
        return false;
    }
    if (!ctype_digit($timestamp) || abs(($now ?? time()) - (float) $timestamp) > 300) {
        return false;
    }
    $expected = hash_hmac('sha256', $timestamp.'.'.$rawBody, $secret);
    return hash_equals($expected, $signature);
}
