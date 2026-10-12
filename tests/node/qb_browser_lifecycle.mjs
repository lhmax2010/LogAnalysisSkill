import { existsSync } from 'node:fs';
import { createRuntime, installFailureHandlers } from '../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';

const [mode, playwright, chromium] = process.argv.slice(2);
const runtime = await createRuntime(playwright, chromium, {
  launchArgs: ['--no-proxy-server', '--host-resolver-rules=MAP * ~NOTFOUND'],
});
console.log(JSON.stringify({ ready: true, profile: runtime.profile }));
if (mode === 'signal') {
  await new Promise(() => {});
} else if (mode === 'exception') {
  installFailureHandlers(() => runtime.close());
  setTimeout(() => { throw new Error('synthetic exception must not appear in output'); }, 0);
  await new Promise(() => {});
} else {
  await runtime.close();
  console.log(JSON.stringify({ removed: !existsSync(runtime.profile) }));
}
