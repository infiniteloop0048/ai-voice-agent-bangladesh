<?php

namespace App\Jobs;

use App\Models\Order;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Http\Client\RequestException;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use Illuminate\Support\Facades\Http;
use RuntimeException;

class RequestConfirmationCall implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public $tries = 3;
    public $backoff = [30, 120];

    public function __construct(public Order $order) {}

    public function handle(): void
    {
        foreach (['url' => 'VOICE_API_URL', 'key' => 'VOICE_API_KEY', 'secret' => 'VOICE_WEBHOOK_SECRET'] as $field => $name) {
            if (!config('services.voice.'.$field)) {
                throw new RuntimeException('Missing environment variable: '.$name);
            }
        }
        try {
            $response = Http::withToken(config('services.voice.key'))
                ->withoutRedirecting()
                ->timeout(10)
                ->post(rtrim(config('services.voice.url'), '/').'/integrations/call-requests', [
                    'external_id' => (string) $this->order->id,
                    'phone' => $this->order->phone,
                    'context' => [
                        'customer_name' => $this->order->customer_name,
                        'order_id' => (string) $this->order->id,
                        'total' => $this->order->total,
                        'payment_method' => $this->order->payment_method,
                        'address' => $this->order->full_address,
                        'items' => $this->order->items->map(fn ($i) => [
                            'name' => $i->name, 'qty' => $i->quantity, 'price' => $i->price,
                        ])->all(),
                    ],
                ])->throw();
            if (!$response->successful()) {
                throw new RuntimeException('HTTP '.$response->status().': '.str_replace(
                    config('services.voice.key'), '[redacted]', $response->body()
                ));
            }
        } catch (RequestException $error) {
            throw new RuntimeException('HTTP '.$error->response->status().': '.str_replace(
                config('services.voice.key'), '[redacted]', $error->response->body()
            ));
        }
    }
}
