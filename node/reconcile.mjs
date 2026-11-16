import { readFile } from 'node:fs/promises';
import { Sworborno } from './sworborno.mjs';

try {
  const client = new Sworborno();
  if (process.argv.length !== 3) throw new Error('Usage: node node/reconcile.mjs path/to/orders.json');
  const orders = JSON.parse(await readFile(process.argv[2], 'utf8'));
  const cutoff = Date.now() - 2 * 60 * 60 * 1000;
  for (const order of orders) {
    if (order.status !== 'awaiting_confirmation') continue;
    const created = Date.parse(order.created_at);
    if (!Number.isFinite(created) || !/(Z|[+-]\d{2}:\d{2})$/.test(order.created_at)) {
      throw new Error('created_at must be an ISO timestamp with a timezone');
    }
    if (created >= cutoff) continue;
    const result = await client.get_call(order.id);
    if (result.outcome != null || result.status === 'failed') {
      // Feed these results to your order update code; old failed rows need review.
      console.log(JSON.stringify(result));
    }
  }
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
