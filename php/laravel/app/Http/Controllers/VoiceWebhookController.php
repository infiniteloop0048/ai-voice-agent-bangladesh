<?php

namespace App\Http\Controllers;

use App\Models\Order;
use App\Models\WebhookReceipt;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;
use RuntimeException;

class VoiceWebhookController extends Controller
{
    public function handle(Request $request)
    {
        foreach (['url' => 'VOICE_API_URL', 'key' => 'VOICE_API_KEY', 'secret' => 'VOICE_WEBHOOK_SECRET'] as $field => $name) {
            if (!config('services.voice.'.$field)) {
                throw new RuntimeException('Missing environment variable: '.$name);
            }
        }
        $raw = $request->getContent();
        $ts = $request->header('X-Webhook-Timestamp', '');
        $signature = $request->header('X-Signature', '');
        $webhookId = $request->header('X-Webhook-Id', '');
        abort_if($ts === '' || $signature === '' || $webhookId === '' || !ctype_digit($ts), 401);
        $expected = hash_hmac('sha256', $ts.'.'.$raw, config('services.voice.secret'));
        abort_unless(hash_equals($expected, $signature), 401);
        abort_if(abs(time() - (float) $ts) > 300, 401);

        DB::transaction(function () use ($request, $webhookId) {
            // The unique index handles concurrent retries; rollback leaves a failed delivery retryable.
            $inserted = WebhookReceipt::query()->insertOrIgnore([
                'webhook_id' => $webhookId,
                'created_at' => now(),
                'updated_at' => now(),
            ]);
            if (!$inserted) {
                return;
            }
            if ($request->input('event') === 'balance.low') {
                Log::warning('Voice agent balance low', $request->only('balance_minutes'));
                return;
            }
            $order = Order::findOrFail($request->input('order_id'));
            match ($request->input('status')) {
                'confirmed' => $order->update([
                    'status' => 'confirmed',
                    'shipping_thana' => $request->input('address.thana'),
                    'shipping_zilla' => $request->input('address.zilla'),
                ]),
                default => $order->update([
                    'status' => 'needs_review',
                    'hold_reason' => $request->input('reason'),
                    'call_note' => $request->input('summary'),
                ]),
            };
        });
        return response()->noContent();
    }
}
