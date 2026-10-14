// Read-only evidence: production guards, one navigation, isolated snapshots.
import { parseArgs } from 'node:util';
import { pathToFileURL } from 'node:url';
import { Agent, Policy, createRuntime } from '../../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';
import { PROJECT, DEFAULTS, newOutput, writeJSON, comparePage, validatePaths } from './p5q_c5_tools.mjs';

export async function comparePages(agent, paths, output) {
  validatePaths(agent.policy, paths);
  const pages = [];
  for (const path of paths) {
    const result = await comparePage(agent, path, output, String(pages.length + 1).padStart(2, '0'));
    pages.push(result);
    // Preserve evidence but do not continue collecting after a premise violation.
    if (result.comparison.some(row => row.result !== '一致')) break;
  }
  await writeJSON(`${output}/run.json`, { pages, trace: agent.runtime.trace });
  return pages;
}

async function main() {
  const { values } = parseArgs({ options: { path: { type: 'string', multiple: true }, output: { type: 'string' } } });
  validatePaths(new Policy([PROJECT.overview_id]), values.path ?? []);
  if (!values.output) throw new Error('OUTPUT_REQUIRED');
  await newOutput(values.output);
  const runtime = await createRuntime(DEFAULTS.playwright, DEFAULTS.chromium);
  const agent = new Agent(runtime);
  try {
    const login = await agent.command({ command: 'login', projects: [PROJECT], login_timeout_seconds: 600 });
    if (!login.ok) throw new Error(login.error);
    const pages = await comparePages(agent, values.path, values.output);
    if (pages.some(page => page.comparison.some(row => row.result !== '一致'))) {
      process.stderr.write('EVIDENCE_PREMISE_MISMATCH\n'); process.exitCode = 1;
    }
  } finally { await agent.command({ command: 'close' }); }
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch(() => { process.stderr.write('EVIDENCE_STOPPED\n'); process.exitCode = 1; });
}
