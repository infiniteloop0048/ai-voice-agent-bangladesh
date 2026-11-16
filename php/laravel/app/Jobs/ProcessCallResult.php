<?php

namespace App\Jobs;

use App\Models\Order;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;

class ProcessCallResult implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public function __construct(public Order $order, public array $result) {}

    public function handle(): void
    {
        // A late hourly check must not replace a result already applied by a webhook.
        $this->order->getConnection()->transaction(function () {
            $order = Order::whereKey($this->order->id)->lockForUpdate()->firstOrFail();
            if ($order->status !== 'awaiting_confirmation') {
                return;
            }
            $details = $this->result['outcome_details'] ?? [];
            if (($this->result['outcome'] ?? null) === 'confirmed' && ($this->result['status'] ?? '') !== 'failed') {
                $order->update([
                    'status' => 'confirmed',
                    'shipping_thana' => $details['thana'] ?? null,
                    'shipping_zilla' => $details['zilla'] ?? null,
                ]);
            } else {
                $order->update([
                    'status' => 'needs_review',
                    'hold_reason' => $details['reason'] ?? null,
                    'call_note' => $details['summary'] ?? null,
                ]);
            }
        });
    }
}
