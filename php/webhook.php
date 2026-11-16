<?php
declare(strict_types=1);
require_once __DIR__.'/signature.php';

try {
    $env = voice_environment();
} catch (RuntimeException $error) {
    http_response_code(500);
    echo $error->getMessage();
    exit(1);
}

$raw = file_get_contents('php://input');
$timestamp = $_SERVER['HTTP_X_WEBHOOK_TIMESTAMP'] ?? null;
$signature = $_SERVER['HTTP_X_SIGNATURE'] ?? null;
$webhookId = $_SERVER['HTTP_X_WEBHOOK_ID'] ?? '';
if ($raw === false || $webhookId === '' || !verify_signature($raw, $timestamp, $signature, $env['VOICE_WEBHOOK_SECRET'])) {
    http_response_code(401);
    exit('Invalid or missing webhook headers');
}

// Production needs a database table and a transaction for the receipt and order update.
// This file keeps the sample's receipts and order changes across requests.
$store = @fopen(__DIR__.'/webhook-receipts.json', 'c+');
if ($store === false || !flock($store, LOCK_EX)) {
    http_response_code(500);
    exit('Cannot lock webhook receipt store');
}

try {
    $saved = stream_get_contents($store);
    $receipts = $saved === '' ? [] : json_decode($saved, true, 512, JSON_THROW_ON_ERROR);
    if (array_key_exists($webhookId, $receipts)) {
        http_response_code(204);
        exit;
    }
    try {
        $data = json_decode($raw, true, 512, JSON_THROW_ON_ERROR);
        if (!is_array($data) || !str_starts_with(ltrim($raw), '{')) {
            throw new RuntimeException('Expected a JSON object');
        }
    } catch (Throwable $error) {
        http_response_code(400);
        exit('Expected a JSON object');
    }
    // Keep slow work in a queue so delivery can be acknowledged quickly.
    if (($data['event'] ?? '') === 'balance.low') {
        $result = $data;
    } elseif (($data['status'] ?? '') === 'confirmed') {
        $result = [
            'order_id' => $data['order_id'] ?? null,
            'status' => 'confirmed',
            'shipping_thana' => $data['address']['thana'] ?? null,
            'shipping_zilla' => $data['address']['zilla'] ?? null,
        ];
    } else {
        $result = [
            'order_id' => $data['order_id'] ?? null,
            'status' => 'needs_review',
            'hold_reason' => $data['reason'] ?? null,
            'call_note' => $data['summary'] ?? null,
        ];
    }
    $receipts[$webhookId] = $result;
    $encoded = json_encode($receipts, JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE);
    rewind($store);
    if (!ftruncate($store, 0) || fwrite($store, $encoded) !== strlen($encoded) || !fflush($store)) {
        throw new RuntimeException('Cannot save webhook receipt');
    }
    http_response_code(204);
} catch (Throwable $error) {
    http_response_code(500);
    echo 'Cannot process webhook receipt';
} finally {
    flock($store, LOCK_UN);
    fclose($store);
}
