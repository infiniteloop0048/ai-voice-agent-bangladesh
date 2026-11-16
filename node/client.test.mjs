import assert from 'node:assert/strict';
import test from 'node:test';
import { Sworborno } from './sworborno.mjs';

const names = ['VOICE_API_URL', 'VOICE_API_KEY', 'VOICE_WEBHOOK_SECRET'];

function offline(t) {
  const saved = Object.fromEntries(names.map(name => [name, process.env[name]]));
  const originalFetch = globalThis.fetch;
  process.env.VOICE_API_URL = 'https://example.com/api/v1';
  process.env.VOICE_API_KEY = 'vk_live_xxxxxxxxxxxxxxxxxxxx';
  process.env.VOICE_WEBHOOK_SECRET = 'change-me';
  t.after(() => {
    globalThis.fetch = originalFetch;
    for (const name of names) {
      if (saved[name] === undefined) delete process.env[name];
      else process.env[name] = saved[name];
    }
  });
}

test('preserves audio bytes and a queued JSON job', async t => {
  offline(t);
  const replies = [
    new Response(new Uint8Array([0, 255]), { status: 200 }),
    new Response('{"id":"VOICEOVER_ID","status":"queued"}', { status: 202 }),
  ];
  globalThis.fetch = async (_url, options) => {
    assert.equal(options.redirect, 'manual');
    assert.ok(options.signal instanceof AbortSignal);
    assert.equal(JSON.parse(options.body).text, 'আপনার অর্ডারটি আজ পাঠানো হয়েছে।');
    return replies.shift();
  };
  const client = new Sworborno();
  const audio = await client.voiceover('VOICE_ID', 'আপনার অর্ডারটি আজ পাঠানো হয়েছে।');
  const queued = await client.voiceover('VOICE_ID', 'আপনার অর্ডারটি আজ পাঠানো হয়েছে।');
  assert.deepEqual(audio.body, Buffer.from([0, 255]));
  assert.equal(queued.status, 202);
  assert.equal(JSON.parse(queued.body.toString()).status, 'queued');
});

test('reports status and body without exposing a key or retrying', async t => {
  offline(t);
  let calls = 0;
  globalThis.fetch = async () => {
    calls++;
    return new Response(`bad ${process.env.VOICE_API_KEY}`, { status: 401 });
  };
  await assert.rejects(new Sworborno().balance(), { message: 'HTTP 401: bad [redacted]' });
  assert.equal(calls, 1);
});

test('surfaces rate limiting to the caller', async t => {
  offline(t);
  globalThis.fetch = async () => new Response('{}', { status: 429 });
  await assert.rejects(new Sworborno().send_call({ external_id: '10432', phone: '01798XXXXXX', context: {} }), { message: 'HTTP 429: {}' });
});

test('reports a transport failure without retrying', async t => {
  offline(t);
  let calls = 0;
  globalThis.fetch = async () => { calls++; throw new Error('offline'); };
  await assert.rejects(new Sworborno().balance(), { message: 'HTTP request failed or timed out' });
  assert.equal(calls, 1);
});

test('requires all three variables before HTTP', t => {
  offline(t);
  let calls = 0;
  globalThis.fetch = async () => { calls++; throw new Error('HTTP must not run'); };
  for (const name of names) {
    const saved = process.env[name];
    delete process.env[name];
    assert.throws(() => new Sworborno(), new RegExp(name));
    process.env[name] = saved;
  }
  assert.equal(calls, 0);
});
