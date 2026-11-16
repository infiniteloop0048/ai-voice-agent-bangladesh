export function environment() {
  const names = ['VOICE_API_URL', 'VOICE_API_KEY', 'VOICE_WEBHOOK_SECRET'];
  const missing = names.filter(name => !process.env[name]);
  if (missing.length) throw new Error(`Missing environment variable(s): ${missing.join(', ')}`);
  return Object.fromEntries(names.map(name => [name, process.env[name]]));
}

export class Sworborno {
  constructor() {
    const env = environment();
    this.url = env.VOICE_API_URL.replace(/\/+$/, '');
    this.key = env.VOICE_API_KEY;
  }

  async request(method, path, payload, timeout = 10_000) {
    const headers = { Authorization: `Bearer ${this.key}` };
    if (payload !== undefined) headers['Content-Type'] = 'application/json';
    let response;
    let body;
    try {
      response = await fetch(this.url + path, {
        method, headers, redirect: 'manual',
        body: payload === undefined ? undefined : JSON.stringify(payload),
        signal: AbortSignal.timeout(timeout),
      });
      body = Buffer.from(await response.arrayBuffer());
    } catch {
      throw new Error('HTTP request failed or timed out');
    }
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${body.toString('utf8').split(this.key).join('[redacted]')}`);
    }
    return { status: response.status, headers: response.headers, body };
  }

  async send_call(payload) {
    return JSON.parse((await this.request('POST', '/integrations/call-requests', payload)).body.toString('utf8'));
  }

  async get_call(externalId) {
    return JSON.parse((await this.request('GET', `/integrations/call-requests/${encodeURIComponent(externalId)}`)).body.toString('utf8'));
  }

  cancel_call(externalId) {
    return this.request('DELETE', `/integrations/call-requests/${encodeURIComponent(externalId)}`);
  }

  async balance() {
    return JSON.parse((await this.request('GET', '/integrations/balance')).body.toString('utf8'));
  }

  async list_voices() {
    return JSON.parse((await this.request('GET', '/integrations/tts/voices')).body.toString('utf8'));
  }

  voiceover(voiceId, text, format = 'mp3') {
    // Preserve audio bytes and the JSON body returned with a queued job.
    return this.request('POST', '/integrations/tts', { voice_id: voiceId, text, format }, 120_000);
  }

  async get_voiceover(id) {
    return JSON.parse((await this.request('GET', `/integrations/tts/${encodeURIComponent(id)}`)).body.toString('utf8'));
  }

  voiceover_audio(id, format = 'mp3') {
    return this.request('GET', `/integrations/tts/${encodeURIComponent(id)}/audio?format=${encodeURIComponent(format)}`, undefined, 120_000);
  }
}
