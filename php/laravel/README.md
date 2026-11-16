# Laravel integration pieces

Copy these files into an existing Laravel application. Merge the `voice` entry from
[config/services.php](config/services.php) into your services config. Set
`VOICE_API_URL`, `VOICE_API_KEY` and `VOICE_WEBHOOK_SECRET` from the root
[.env.example](../../.env.example) in your application's environment.

Use your own `App\Models\Order`. The send job reads the order fields and items
shown in the guide. The receiver and reconciliation job need `status`,
`shipping_thana`, `shipping_zilla`, `hold_reason` and `call_note` to be writable
order fields. Adapt these local updates to your order system.

Run the receipt migration in your application. Its unique `webhook_id` index and
the controller transaction make retries safe. Keep slow work in queued jobs.
The examples make no outbound HTTP request while receiving a webhook.

Dispatch the send job where an order is created:

```php
App\Jobs\RequestConfirmationCall::dispatch($order);
```

The guide names two pitfalls:

- `QUEUE_CONNECTION` must not be `sync` in production. Use a queue worker so the
  network request does not run inside checkout.
- Keep `->throw()`. Otherwise a failed POST can be silently dropped. The job
  keeps the guide's retry settings: three tries, with backoff of 30 and 120 seconds.

Put the webhook route in `routes/api.php`. In `web.php`, CSRF protection rejects
the POST with a 419. Give Sworborno your public HTTPS webhook URL, for example
`https://example.com/api/webhooks/voice` when your application uses the `/api`
prefix. The prefix depends on your application's route configuration.

Merge [routes/console.php](routes/console.php) into your application's schedule
registration and run your Laravel scheduler. It checks hourly for orders still
`awaiting_confirmation` after two hours. `ProcessCallResult` reads `outcome` and
`outcome_details` from polling; it does not expect the webhook's `address` object.
Old `failed` rows go to review. A `hold` never cancels an order.
