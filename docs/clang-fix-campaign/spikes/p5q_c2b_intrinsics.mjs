// Evidence-only native-code flags; never return function source from the page.
export function intrinsicsDOM() {
  const native = f => typeof f === 'function' && !!/\[native code\]/.test(Function.prototype.toString.call(f));
  return {
    'String.prototype.trim': native(String.prototype.trim),
    'String.prototype.replace': native(String.prototype.replace),
    'String.prototype.split': native(String.prototype.split),
    'String.prototype.includes': native(String.prototype.includes),
    'Array.prototype.map': native(Array.prototype.map),
    'Array.prototype.filter': native(Array.prototype.filter),
    'Array.prototype.includes': native(Array.prototype.includes),
    'JSON.stringify': native(JSON.stringify),
    'RegExp.prototype.exec': native(RegExp.prototype.exec),
  };
}

export async function intrinsicsSelfTest(playwright, chromium) {
  const { default: assert } = await import('node:assert/strict');
  const { readFile } = await import('node:fs/promises');
  const { createRuntime } = await import('../../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs');
  const { configurationDOM, normalizeConfigurationDOM, parentConfigurationChecks, configurationPageChecks } =
    await import('./p5q_c2b_config_source.mjs');
  const runtime = await createRuntime(playwright, chromium);
  runtime.policy.allow = () => false;
  let requests = 0;
  runtime.page.on('request', () => { requests++; });
  let count = 0;
  const pass = name => { count++; process.stdout.write(JSON.stringify({ test: name, result: 'PASS' }) + '\n'); };
  try {
    const baseline = await runtime.page.evaluate(intrinsicsDOM);
    assert.equal(Object.keys(baseline).length, 9);
    assert.ok(Object.values(baseline).every(value => value === true));
    pass('nine-native-boolean-flags-no-source');
    for (const key of Object.keys(baseline)) {
      await runtime.page.evaluate(path => {
        const parts = path.split('.');
        let owner = globalThis;
        for (const name of parts.slice(0, -1)) owner = owner[name];
        const name = parts.at(-1), original = owner[name];
        globalThis.restoreIntrinsic = () => { owner[name] = original; };
        owner[name] = function (...args) { return Reflect.apply(original, this, args); };
      }, key);
      const actual = await runtime.page.evaluate(intrinsicsDOM);
      assert.deepEqual(actual, { ...baseline, [key]: false });
      assert.ok(Object.values(actual).every(value => typeof value === 'boolean'));
      assert.doesNotMatch(JSON.stringify(actual), /function|native code|=>/);
      await runtime.page.evaluate(() => globalThis.restoreIntrinsic());
      pass(`wrapped-intrinsic-false:${key}`);
    }
    for (const [file, path, check] of [
      ['01.response.html', '/build/1193467/overview', parentConfigurationChecks],
      ['06.response.html', '/overview/1917', configurationPageChecks],
    ]) {
      const html = await readFile(new URL(`../dev_memory/stage20_p5q_qb_trigger/evidence/C2b/live-10/${file}`, import.meta.url), 'utf8');
      const expected = normalizeConfigurationDOM(await runtime.page.evaluate(configurationDOM, html));
      await runtime.page.evaluate(() => {
        globalThis.savedTrim = String.prototype.trim;
        String.prototype.trim = function () { return this.replace(/^\s+|\s+$/, ''); };
      });
      const actual = normalizeConfigurationDOM(await runtime.page.evaluate(configurationDOM, html));
      assert.deepEqual(actual, expected);
      assert.equal(check(actual, path).passed, true);
      assert.equal(check({ ...actual, copy_paths: [] }, path).passed, false);
      await runtime.page.evaluate(() => { String.prototype.trim = globalThis.savedTrim; });
      pass(`broken-trim-config-check:${file}`);
    }
    assert.doesNotMatch(configurationDOM.toString(), /\.(?:trim|replace|split|matchAll|toLowerCase|toUpperCase)\s*\(/);
    assert.equal(requests, 0);
    assert.equal(runtime.policy.released, false);
    process.stdout.write(JSON.stringify({ self_tests: count, passed: count, network_requests: requests, released: false }) + '\n');
  } finally { await runtime.close(); }
}
