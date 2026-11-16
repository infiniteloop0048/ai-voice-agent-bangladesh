import { readFile } from 'node:fs/promises';
import { Sworborno } from './sworborno.mjs';

try {
  const client = new Sworborno();
  const payload = JSON.parse(await readFile(process.argv[2] || new URL('../payloads/call-request.json', import.meta.url), 'utf8'));
  console.log(JSON.stringify(await client.send_call(payload), null, 2));
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
