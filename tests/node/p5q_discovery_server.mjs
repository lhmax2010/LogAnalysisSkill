import { writeFile } from 'node:fs/promises';
import { createInterface } from 'node:readline';
import { discoveryServer } from './p5q_discovery_fixture.mjs';
const [config, requests] = process.argv.slice(2);
const server = await discoveryServer();
try {
  await writeFile(config, JSON.stringify(server.overrides));
  process.stdout.write('{"ready":true}\n');
  for await (const line of createInterface({ input: process.stdin })) {
    if (JSON.parse(line).close) break;
  }
} finally {
  await server.close();
  await writeFile(requests, JSON.stringify(server.received.map(({ method, path }) => ({ method, path }))));
  process.stdin.destroy();
}
