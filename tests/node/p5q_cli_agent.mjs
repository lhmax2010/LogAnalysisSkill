// Integration entry only: real Agent, local certificate/DNS and simulated human.
import { readFile, writeFile } from 'node:fs/promises';
import { createInterface } from 'node:readline';
import { Agent, createRuntime } from '../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';
const [playwright, chromium] = process.argv.slice(2);
const runtime = await createRuntime(playwright, chromium, JSON.parse(await readFile(process.env.P5Q_TEST_SERVER, 'utf8')));
const agent = new Agent(runtime);
const transcript = [];
try {
  for await (const line of createInterface({ input: process.stdin })) {
    const input = JSON.parse(line);
    const result = agent.command(input);
    if (input.command === 'login') {
      // Test simulates the person; production Agent.login remains passive.
      await runtime.page.locator('input[name=user]').fill('synthetic');
      await runtime.page.locator('input[type=password]').fill('synthetic-password');
      await runtime.page.getByRole('button', { name: 'Login', exact: true }).click();
    }
    const output = await result;
    if (input.command === 'login' && output.ok) {
      if (process.env.P5Q_TEST_C6_FAILURE === 'NEW_PAGE') {
        try { await runtime.context.newPage(); } catch { /* Expected fail-closed. */ }
        await runtime.close();
      } else if (process.env.P5Q_TEST_C6_FAILURE === 'BROWSER_DISCONNECTED') {
        await runtime.browser.close();
      } else if (process.env.P5Q_TEST_C6_FAILURE === 'PAGE_CLOSED') {
        await runtime.page.close();
      }
    }
    transcript.push({ input, output });
    process.stdout.write(JSON.stringify(output) + '\n');
    if (input.command === 'close') break;
  }
} finally {
  await runtime.close();
  await writeFile(process.env.P5Q_TEST_AGENT_LOG, JSON.stringify({ transcript, trace: runtime.trace }, null, 2));
  process.stdin.destroy();
}
