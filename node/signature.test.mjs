import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { verify_signature } from './signature.mjs';

const vector = JSON.parse(readFileSync(new URL('../payloads/signature-vector.json', import.meta.url), 'utf8'));
const raw = Buffer.from(vector.body);
const now = Number(vector.timestamp);
const verify = (body = raw, timestamp = vector.timestamp, signature = vector.signature, at = now) =>
  verify_signature(body, timestamp, signature, vector.secret, at);

test('accepts the shared vector', () => assert.equal(verify(), true));
test('rejects a changed body', () => assert.equal(verify(Buffer.concat([raw, Buffer.from(' ')])), false));
test('rejects a changed timestamp', () => assert.equal(verify(raw, String(now + 1)), false));
test('rejects an old timestamp', () => assert.equal(verify(raw, vector.timestamp, vector.signature, now + 301), false));
test('rejects a future timestamp', () => assert.equal(verify(raw, vector.timestamp, vector.signature, now - 301), false));
test('rejects a missing signature', () => assert.equal(verify(raw, vector.timestamp, ''), false));
test('rejects a missing timestamp', () => assert.equal(verify(raw, ''), false));
test('rejects an invalid timestamp', () => assert.equal(verify(raw, 'invalid'), false));
test('accepts the window boundary', () => assert.equal(verify(raw, vector.timestamp, vector.signature, now + 300), true));
