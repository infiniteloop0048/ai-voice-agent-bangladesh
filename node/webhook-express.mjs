import { verify_signature } from './signature.mjs';
import { environment } from './sworborno.mjs';

let env;
try {
  env = environment();
} catch (error) {
  console.error(error.message);
  process.exit(1);
}

let express;
try {
  ({ default: express } = await import('express'));
} catch {
  console.error('Express is required to run this receiver.');
  process.exit(1);
}

const app = express();
const receipts = new Set();
const orders = new Map();

// Mount before any JSON middleware so verification sees the exact bytes.
app.post('/webhooks/voice', express.raw({ type: () => true }), (req, res) => {
  const timestamp = req.get('X-Webhook-Timestamp');
  const signature = req.get('X-Signature');
  const webhookId = req.get('X-Webhook-Id');
  if (!webhookId || !Buffer.isBuffer(req.body) ||
      !verify_signature(req.body, timestamp, signature, env.VOICE_WEBHOOK_SECRET)) {
    return res.status(401).send('Invalid or missing webhook headers');
  }
  if (receipts.has(webhookId)) return res.status(204).end();
  let data;
  try {
    data = JSON.parse(req.body.toString('utf8'));
    if (!data || typeof data !== 'object' || Array.isArray(data)) throw new Error();
  } catch {
    return res.status(400).send('Expected a JSON object');
  }
  // Production needs a database table and a transaction for the receipt and order update.
  // Queue slow work so delivery can be acknowledged quickly.
  if (data.event === 'balance.low') {
    console.warn('Voice agent balance low:', data.balance_minutes);
  } else if (data.status === 'confirmed') {
    orders.set(data.order_id, {
      status: 'confirmed',
      shipping_thana: data.address?.thana,
      shipping_zilla: data.address?.zilla,
    });
  } else {
    orders.set(data.order_id, {
      status: 'needs_review', hold_reason: data.reason, call_note: data.summary,
    });
  }
  receipts.add(webhookId);
  return res.status(204).end();
});

app.listen(3000);
