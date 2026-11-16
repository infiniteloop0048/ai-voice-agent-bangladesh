import { createHmac, timingSafeEqual } from 'node:crypto';

export function verify_signature(rawBody, timestamp, signature, secret, now = Date.now() / 1000) {
  if (!timestamp || !signature || !secret || !/^[0-9]+$/.test(timestamp)) return false;
  const seconds = Number(timestamp);
  if (!Number.isSafeInteger(seconds) || Math.abs(now - seconds) > 300) return false;
  const expected = Buffer.from(createHmac('sha256', secret).update(timestamp + '.').update(rawBody).digest('hex'));
  const supplied = Buffer.from(signature);
  return expected.length === supplied.length && timingSafeEqual(expected, supplied);
}
