<?php
declare(strict_types=1);
require_once __DIR__.'/signature.php';

$vector = json_decode(file_get_contents(__DIR__.'/../payloads/signature-vector.json'), true, 512, JSON_THROW_ON_ERROR);
$body = $vector['body'];
$timestamp = $vector['timestamp'];
$signature = $vector['signature'];
$secret = $vector['secret'];
$now = (int) $timestamp;
$checks = [
    'shared vector' => verify_signature($body, $timestamp, $signature, $secret, $now),
    'changed body' => !verify_signature($body.' ', $timestamp, $signature, $secret, $now),
    'changed timestamp' => !verify_signature($body, (string) ($now + 1), $signature, $secret, $now),
    'old timestamp' => !verify_signature($body, $timestamp, $signature, $secret, $now + 301),
    'future timestamp' => !verify_signature($body, $timestamp, $signature, $secret, $now - 301),
    'missing signature' => !verify_signature($body, $timestamp, null, $secret, $now),
    'missing timestamp' => !verify_signature($body, null, $signature, $secret, $now),
    'invalid timestamp' => !verify_signature($body, 'invalid', $signature, $secret, $now),
    'window boundary' => verify_signature($body, $timestamp, $signature, $secret, $now + 300),
];
foreach ($checks as $name => $passed) {
    if (!$passed) {
        fwrite(STDERR, 'FAIL: '.$name.PHP_EOL);
        exit(1);
    }
    echo 'PASS: '.$name.PHP_EOL;
}
