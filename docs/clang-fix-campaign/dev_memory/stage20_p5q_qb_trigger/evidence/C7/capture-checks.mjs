// Reproduce the offline contract probe and read-only checks; archive generated outputs.
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const output = fileURLToPath(new URL('.', import.meta.url));
const inputs = [
  'docs/clang-fix-campaign/p5q-qb-trigger-design-v1.8-FROZEN.md',
  'docs/clang-fix-campaign/p5q-qb-trigger-design-v1.5-FROZEN.md',
  '/home/linhao/Toolchain/p5q-live-validation/p5q-c6/state.db',
];
const hash = raw => createHash('sha256').update(raw).digest('hex');
const hashes = () => Object.fromEntries(inputs.map(path => [path, hash(readFileSync(path))]));
const before = hashes();
const commands = [
  ['budget-probe', [process.execPath, output + 'probe-read-budget.mjs']],
  ['source-guards', [process.execPath, '--test', 'tests/node/test_qb_agent_source_guards.mjs']],
  ['design-check', ['.venv/bin/python', 'docs/clang-fix-campaign/tools/check_design_doc.py',
    'docs/clang-fix-campaign/design.md']],
];
const results = [];
for (const [name, argv] of commands) {
  const started = new Date().toISOString();
  const start = performance.now();
  const result = spawnSync(argv[0], argv.slice(1), { encoding: 'utf8', maxBuffer: 8 * 1024 * 1024 });
  const ended = new Date().toISOString();
  const stdout = `${name}.stdout.${name === 'budget-probe' ? 'json' : 'txt'}`;
  const stderr = `${name}.stderr.txt`;
  writeFileSync(output + stdout, result.stdout ?? '');
  writeFileSync(output + stderr, result.stderr ?? '');
  results.push({ name, argv, started, ended, duration_ms: Math.round(performance.now() - start),
    exit: result.status, signal: result.signal, stdout, stderr });
}
const agentPath = 'tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';
const baseline = spawnSync('git', ['show', `48b0aa9:${agentPath}`], { encoding: 'utf8' });
if (baseline.status !== 0) throw new Error('BASELINE_UNAVAILABLE');
const current = readFileSync(agentPath, 'utf8');
const prefix = source => source.slice(0, source.indexOf('export class Agent {'));
const after = hashes();
const checks = { before, after, unchanged: JSON.stringify(before) === JSON.stringify(after),
  agent: { baseline_sha256: hash(baseline.stdout), current_sha256: hash(current),
    full_equal: current === baseline.stdout, prefix_end: 'export class Agent {',
    prefix_baseline_sha256: hash(prefix(baseline.stdout)), prefix_current_sha256: hash(prefix(current)),
    prefix_equal: prefix(current) === prefix(baseline.stdout) } };
writeFileSync(output + 'checks.json', JSON.stringify({ cwd: process.cwd(), results, checks }, null, 2) + '\n');
console.log(JSON.stringify({ results, checks }, null, 2));
process.exitCode = results.every(row => row.exit === (row.name === 'budget-probe' ? 1 : 0))
  && checks.unchanged && checks.agent.full_equal ? 0 : 1;
