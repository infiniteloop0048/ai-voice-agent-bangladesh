<?php

use App\Jobs\ProcessCallResult;
use App\Models\Order;
use Illuminate\Http\Client\RequestException;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Schedule;

Schedule::call(function () {
    foreach (['url' => 'VOICE_API_URL', 'key' => 'VOICE_API_KEY', 'secret' => 'VOICE_WEBHOOK_SECRET'] as $field => $name) {
        if (!config('services.voice.'.$field)) {
            throw new RuntimeException('Missing environment variable: '.$name);
        }
    }
    Order::where('status', 'awaiting_confirmation')
        ->where('created_at', '<', now()->subHours(2))
        ->each(function ($order) {
            try {
                $r = Http::withToken(config('services.voice.key'))
                    ->withoutRedirecting()
                    ->timeout(10)
                    ->get(rtrim(config('services.voice.url'), '/').'/integrations/call-requests/'.rawurlencode((string) $order->id))
                    ->throw();
                if (!$r->successful()) {
                    throw new RuntimeException('HTTP '.$r->status().': '.str_replace(
                        config('services.voice.key'), '[redacted]', $r->body()
                    ));
                }
            } catch (RequestException $error) {
                throw new RuntimeException('HTTP '.$error->response->status().': '.str_replace(
                    config('services.voice.key'), '[redacted]', $error->response->body()
                ));
            }
            if ($r->json('outcome') !== null || $r->json('status') === 'failed') {
                ProcessCallResult::dispatch($order, $r->json());
            }
        });
})->hourly();
