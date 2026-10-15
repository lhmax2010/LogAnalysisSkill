// Read-only evidence: production guards, one navigation, isolated snapshots.
import { parseArgs } from 'node:util';
import { pathToFileURL } from 'node:url';
import { Agent, Policy, createRuntime } from '../../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';
import { PROJECT, DEFAULTS, newOutput, comparePage, validatePaths,
  EvidenceError, withEvidence, evidenceSession, reportFailure } from './p5q_c5_tools.mjs';

export async function comparePages(agent, paths, output, record = null) {
  if (!record) return withEvidence(output, inner => comparePages(agent, paths, output, inner));
  record.agent = agent;
  validatePaths(agent.policy, paths);
  const pages = [];
  record.data.pages = pages;
  for (const path of paths) {
    const result = await comparePage(agent, path, output, String(pages.length + 1).padStart(2, '0'), record);
    pages.push(result);
    // Preserve evidence but do not continue collecting after a premise violation.
    if (result.comparison.some(row => row.result !== '一致')) {
      record.stage = 'compare'; record.fail(new EvidenceError('EVIDENCE_PREMISE_MISMATCH')); break;
    }
  }
  return pages;
}

async function main() {
  const { values } = parseArgs({ options: { path: { type: 'string', multiple: true }, output: { type: 'string' } } });
  validatePaths(new Policy([PROJECT.overview_id]), values.path ?? []);
  if (!values.output) throw new EvidenceError('OUTPUT_REQUIRED');
  await newOutput(values.output);
  await evidenceSession(values.output, async () => new Agent(await createRuntime(DEFAULTS.playwright, DEFAULTS.chromium)),
    (agent, record) => comparePages(agent, values.path, values.output, record));
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch(error => { reportFailure(error); process.exitCode = 1; });
}
