# AI voice agent API examples for Bangladesh (Sworborno)

[Sworborno](https://www.sworborno.com) is a Bangla AI voice agent and AI calling service for businesses in Bangladesh, made in Dhaka. Your system sends an order by API, the agent calls the customer on a Bangladeshi number and confirms the order in Bangla, and the result comes back by signed webhook. This repository has copy-ready examples in curl, Python, Node.js, PHP and Laravel. Read the [docs](https://www.sworborno.com/docs) for the integration guide.

## Quick start

Get a key at [signup](https://www.sworborno.com/signup), plus your webhook signing
secret. From the repository root:

```bash
cp .env.example .env
# Edit .env with your key and webhook secret before loading it.
set -a
. ./.env
set +a
```

The scripts require all three environment variables. They do not load `.env`
automatically. Keep `.env` out of git. The base URL is
`https://www.sworborno.com/api/v1`; requests use
`Authorization: Bearer vk_live_xxxxxxxxxxxxxxxxxxxx` with your own key.

Replace the masked `01798XXXXXX` in [call-request.json](payloads/call-request.json)
with one of your own test phones in a local copy. The test assistant only calls
your own phones. Keep real phone numbers and credentials out of public files.
Send the test request using that local JSON file:

```bash
bash curl/send-call.sh path/to/local-call-request.json
```

You can also copy `curl/send-call.sh` on its own, edit the masked phone in its
embedded guide sample, set the three environment variables and run it without
an argument. A send returns `202`.
Read the result using your `external_id`:

```bash
bash curl/check-call.sh 10432
```

For signed delivery, give Sworborno your public HTTPS receiver URL, such as
`https://example.com/webhooks/voice`. The small receivers below use
`/webhooks/voice`; the PHP file can be served at the URL you configure.
See [Webhook results](#webhook-results) for verification and result handling.

## Examples by language

| Job | curl | Python | Node.js | PHP | Laravel |
|---|---|---|---|---|---|
| Send an order | [send-call.sh](curl/send-call.sh) | [send_call.py](python/send_call.py) | [send-call.mjs](node/send-call.mjs) | [send_call.php](php/send_call.php) | [queued job](php/laravel/app/Jobs/RequestConfirmationCall.php) |
| Check or cancel | [check](curl/check-call.sh), [cancel](curl/cancel-call.sh) | [client](python/sworborno.py) | [client](node/sworborno.mjs) | — | — |
| Balance | [balance.sh](curl/balance.sh) | [client](python/sworborno.py) | [client](node/sworborno.mjs) | — | — |
| Voices and voiceover | [voiceover.sh](curl/voiceover.sh) | [client](python/sworborno.py) | [client](node/sworborno.mjs) | — | — |
| Receive a webhook | — | [Flask](python/webhook_flask.py) | [Express](node/webhook-express.mjs) | [receiver](php/webhook.php) | [controller](php/laravel/app/Http/Controllers/VoiceWebhookController.php) |
| Reconcile hourly | — | [reconcile.py](python/reconcile.py) | [reconcile.mjs](node/reconcile.mjs) | — | [schedule](php/laravel/routes/console.php) |
| Verify a signature | — | [signature.py](python/signature.py) | [signature.mjs](node/signature.mjs) | [signature.php](php/signature.php) | [controller](php/laravel/app/Http/Controllers/VoiceWebhookController.php) |
| Offline signature tests | — | [unittest](python/test_signature.py) | [node:test](node/signature.test.mjs) | [test_signature.php](php/test_signature.php) | — |

Copy the client or signature helper with the script that imports it. The curl
send script stands alone; the other curl scripts share
[_common.sh](curl/_common.sh). Python clients use only the standard library;
the receiver needs Flask. Node.js needs version 18 or later and uses no packages
except Express for the receiver. The plain PHP examples use built-in functions
and need HTTPS stream support for sending. The [Laravel notes](php/laravel/README.md)
explain where to place those application files.

With the environment loaded, these send the same sample request (or pass your
local request JSON path as the last argument):

```bash
python3 python/send_call.py path/to/local-call-request.json
node node/send-call.mjs path/to/local-call-request.json
php php/send_call.php path/to/local-call-request.json
```

Run a receiver with `python3 python/webhook_flask.py` or
`node node/webhook-express.mjs` when its dependency is already available. They
are small local examples: Python and Node keep receipts and order changes in
memory, so a restart loses them. PHP saves them to `php/webhook-receipts.json`.
Production needs a database table, with the receipt and order change in one
transaction. Adapt the order update code to your system and queue slow work.

The Python and Node clients expose `send_call`, `get_call`, `cancel_call`,
`balance`, `list_voices` and `voiceover`. They also expose `get_voiceover` and
`voiceover_audio` for queued voiceovers. All HTTP calls have a timeout. Errors
exit non-zero or raise with the HTTP status and response body; client code does
not retry automatically. The Laravel send job uses the guide's queue retries.

## The API at a glance

All paths below are relative to `VOICE_API_URL`. Each request needs the bearer key.

| Method | Path | What it does |
|---|---|---|
| POST | `/integrations/call-requests` | Send an order; returns `202` |
| GET | `/integrations/call-requests/{external_id}` | Check status and outcome by your order id |
| DELETE | `/integrations/call-requests/{external_id}` | Withdraw a call request |
| GET | `/integrations/balance` | Read account balance and available seconds |
| GET | `/integrations/tts/voices` | List voices and audio previews |
| POST | `/integrations/tts` | Create a voiceover |
| GET | `/integrations/tts/{id}` | Check a voiceover job |
| GET | `/integrations/tts/{id}/audio?format=mp3` | Download audio; `format=wav` also works |

`external_id` is your order id and the idempotency key, scoped to your account.
Send the same id again to get the first request back without another call.
`context` is free-form JSON: send the details a support person would need.
Supply `assistant_id` only when your account has more than one assistant.

| Send status | Meaning |
|---|---|
| `202` | Accepted, including a retry of the same order |
| `401` | Bad, missing or revoked API key |
| `400` / `404` | Required `assistant_id` missing / assistant is not yours |
| `422` | Bad payload; the response names the field, including numbers that cannot be dialled |
| `429` | Rate limited; back off and retry |

## Webhook results

The [confirmed](payloads/call-result-confirmed.json) and
[hold](payloads/call-result-hold.json) samples are copied from the guide.
Branch on `status` only:

| Status | Action |
|---|---|
| `confirmed` | Customer confirmed and the address was collected. Ship the order. |
| `hold` | Put it in front of a person. Never auto-cancel. |

Show `reason` and `summary` to the reviewer. Do not branch on `reason`.

| Reason | What happened |
|---|---|
| `cancelled` | Customer does not want it |
| `modified` | Customer wants a change; see `summary` |
| `wrong_number` | Not the customer |
| `address_incomplete` | Confirmed, but hung up before the address finished |
| `unclear` | No clear answer, including a request to call later |
| `no_answer` | Nobody picked up on any allowed attempt |
| `call_failed` | The call could not be made or could not continue |
| `abusive` | The person was abusive; consider whether to call again |
| `ran_long` | The call passed the platform's length limit without an outcome |

`address.original` stays exactly as you sent it. `thana` and `zilla` come from
what the customer said; the district is checked where possible. `address.full`
is the joined courier label line. `duration_seconds` is the billed call length
in whole seconds; it can be `null` when no attempt connected or the length
could not be measured. The webhook goes out after the call ends and is billed.
Its `balance_seconds` and `available_seconds` are the balance after that call.
Retried deliveries keep the same figures. A rare reconciliation resend hours
later shows the balance at the time of that resend.

Every delivery has these headers:

| Header | Purpose |
|---|---|
| `X-Signature` | HMAC-SHA256 of `"{timestamp}.{raw body}"` with your signing secret |
| `X-Webhook-Timestamp` | Unix seconds, signed with the body |
| `X-Webhook-Id` | Stable id across retries; use it to skip duplicates |

Read the raw request body before parsing JSON. Compute the signature over the
timestamp header, a literal dot and those exact bytes, then compare using a
constant-time function. Reject a missing header, a bad signature, or
`abs(now - timestamp) > 300` seconds. The shared
[signature vector](payloads/signature-vector.json) contains an exact body string,
including its final newline; all language tests use it with a fixed clock.

Delivery is at least once. Save the webhook id with the order update and treat a
repeated id as done. Return a successful response quickly. On a non-2xx response
or timeout, delivery retries immediately, then after 30 seconds, 2 minutes,
10 minutes, 30 minutes, 2 hours and 6 hours, about 9 hours in all. The result is
saved before delivery; if every attempt fails, Sworborno flags it and can resend
it by hand.

`balance.low` is a separate account event. It uses the same signature and
duplicate check, and must not be processed as an order result.

## Check, cancel and reconcile

```bash
bash curl/check-call.sh 10432
bash curl/cancel-call.sh 10432
```

The [call status sample](payloads/call-status.json) shows the polling response.
`status` moves from `queued` to `calling` to `done`, or becomes `cancelled` after
a DELETE. Treat old `failed` rows as a hold. `outcome` is `null` until `done`,
then `confirmed` or `hold`. Polling uses `outcome_details` for `reason`, `thana`,
`zilla` and `summary`; it has no `address.full`. Build the label from your own
address and the returned thana and zilla. Polling also returns `duration_seconds`.

`attempts` counts dials so far. If the request is `queued` and `attempts` is at
least one, nobody answered and another attempt is scheduled. `error` is `null`
or a plain sentence explaining why a call could not be placed or the phone was
not reached; see the docs for those fixed sentences.

Cancel when the customer cancels or staff confirm by hand. If the phone is
already ringing, it stops. A request with an outcome comes back unchanged.

Run reconciliation hourly for orders still `awaiting_confirmation` and created
more than two hours ago. Export your local orders as a JSON array with `id`,
`status` and a timezone-bearing `created_at`, then run one of:

```bash
python3 python/reconcile.py path/to/orders.json
node node/reconcile.mjs path/to/orders.json
```

These scripts print completed polling results and old `failed` rows as JSON
lines. Feed them into your order update code: apply `confirmed` or send the
order to review, and treat `failed` as a hold. They do not update your database.
Use the [Laravel schedule](php/laravel/routes/console.php) and
[result job](php/laravel/app/Jobs/ProcessCallResult.php) for an application example.

## Balance

```bash
bash curl/balance.sh
```

See the [balance response](payloads/balance.json). Use `available_seconds` for
checks: it leaves out what calls in progress may still use. Calls stop when
the account runs out of minutes. Call result webhooks also carry
`balance_seconds` and `available_seconds`, so you can see balance changes
without polling.

The [balance.low sample](payloads/balance-low.json) is sent once each time the
balance drops below the threshold. A top-up above the threshold resets it.

## Bangla text to speech (TTS) API

Voiceover uses the same key. It must be on for your account, and the account
must have been topped up at least once. One minute of audio uses 75 seconds of
balance, ৳5 a minute. The charge uses the exact audio length; a failed voiceover
costs nothing. For call prices, see [Pricing](https://www.sworborno.com/pricing).

List voices and choose an `id`. Each voice has a name, language, gender,
description, preview URL, preview length and `chars_per_minute`:

```bash
bash curl/voiceover.sh voices
```

Save this as a local request JSON file, replacing `VOICE_ID` with an id from
the voice list:

```json
{"voice_id":"VOICE_ID","text":"আপনার অর্ডারটি আজ পাঠানো হয়েছে।","format":"mp3"}
```

```bash
bash curl/voiceover.sh create path/to/voiceover-request.json voiceover.mp3
```

Text can contain up to 20,000 characters. Up to 2,000 characters returns audio
directly, as `audio/mpeg` for `mp3` or `audio/wav` for `wav`. The response headers
`X-Voiceover-Id`, `X-Audio-Seconds` and `X-Charged-Seconds` describe the audio.
The curl example saves an audio response to the chosen file and prints those
headers to standard error. Use a `.wav` filename when requesting `wav`.

Longer text, or a short request that takes more than 90 seconds, returns `202`
and a JSON job instead. The example prints that JSON without saving it as audio.
Check the returned `id` until its `status` is `done`, then download:

```bash
bash curl/voiceover.sh status VOICEOVER_ID
bash curl/voiceover.sh audio VOICEOVER_ID mp3 voiceover.mp3
```

Job status is `queued`, `processing`, `done`, `failed` or `expired`.
`charged_seconds` is the held estimate while the job runs and the exact charge
when done. Audio files are kept for 30 days.

| HTTP status | Meaning |
|---|---|
| `402` | Not enough balance, or the account has never been topped up |
| `403` | Voiceover is not on for this account |
| `404` | No such voice or voiceover |
| `409` | Audio is not ready yet |
| `410` | Voiceover failed or is older than 30 days |
| `502` | Voiceover could not be made; nothing charged, and the body has its `id` |

## Common mistakes

- Parsing JSON before signature verification changes the bytes. Verify the raw body.
- A Laravel route in `web.php` can return CSRF 419. Put it in `routes/api.php`.
- A production Laravel queue set to `sync` puts the request inside checkout.
- Removing `->throw()` can silently drop a failed POST. Keep it.
- Auto-cancelling a `hold` loses orders that need a person. Send it for review.
- Branching on `reason` adds fragile rules. Branch on `status` for webhook results.

## বাংলায় সংক্ষেপে

API দিয়ে অর্ডার পাঠালে এজেন্ট গ্রাহককে ফোন করে বাংলায় অর্ডার নিশ্চিত করে।  
কলের ফলাফল সই করা ওয়েবহুকের মাধ্যমে আপনার সিস্টেমে ফিরে আসে।  
অর্ডার নিশ্চিত না হলে নিজে থেকে বাতিল না করে একজন কর্মীকে দেখতে দিন।  
বিস্তারিত ও কোডের নিয়ম দেখুন [ডকুমেন্টেশনে](https://www.sworborno.com/docs)।

## Links

- [AI voice agent in Bangladesh](https://www.sworborno.com/use-cases/voice-agent)
- [AI call center in Bangladesh](https://www.sworborno.com/use-cases/ai-call-center)
- [AI order confirmation calls](https://www.sworborno.com/use-cases/order-confirmation-call)
- [API documentation](https://www.sworborno.com/docs)
- [Pricing](https://www.sworborno.com/pricing)
- [Contact](https://www.sworborno.com/contact)

## License

[MIT](LICENSE). Copyright (c) 2026 Sworborno.
