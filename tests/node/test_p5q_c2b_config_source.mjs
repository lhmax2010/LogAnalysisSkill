import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { createRuntime } from '../../tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs';
import {
  BUILD_PREFIX, CONFIGURATION_PATH, configurationDOM, configurationPageChecks,
  parentConfigurationChecks, parentRegistration,
} from '../../docs/clang-fix-campaign/spikes/p5q_c2b_config_source.mjs';

const [playwright, chromium] = process.argv.slice(2);
const sourcePath = '/build/123/overview';
function fixture({ id = '7654', path = CONFIGURATION_PATH, current = true,
  copy = CONFIGURATION_PATH, name = BUILD_PREFIX + 'FIXTURE', prefix = '../../',
  overview = `${prefix}overview/${id}`, pipeline = `${prefix}pipeline/${id}`,
  children = `${prefix}children/${id}` } = {}) {
  const segments = path.split('/').map((text, index, parts) => {
    const label = index === parts.length - 1 && current
      ? `<span><em><span>${text}</span></em></span>` : `<a href="${index}.latest"><span>${text}</span></a>`;
    return `<span>${label}<a class="children-chooser"> </a></span>`;
  }).join('');
  return `<div id="breadcrumb">${segments}<a id="copy">copy</a></div>
    <li class="tab-ConfigurationOverview"><a class="nav-link" href="${overview}">Configuration Overview</a></li>
    <li class="tab-PipelinePage"><a class="nav-link" href="${pipeline}">Pipelines</a></li>
    <li class="tab-ChildrenPage"><a class="nav-link" href="${children}">Children</a></li>
    <div class="build-header"><div class="text-2xl">${name}</div></div>
    <script>onCopyClipboardLinkDomReady('copy', '${copy}');</script>`;
}

test('C2B-04/07 configuration evidence: URL resolution, five parent checks, two page checks, fresh provenance', async t => {
  const runtime = await createRuntime(playwright, chromium, {
    launchArgs: ['--no-proxy-server', '--host-resolver-rules=MAP * ~NOTFOUND'],
  });
  runtime.policy.allow = () => false;
  const parse = html => runtime.page.evaluate(configurationDOM, html);
  const source = facts => ({ path: sourcePath, id_verified: true,
    file: '01.response.html', sha256: 'a'.repeat(64), status: 200, facts });
  try {
    await t.test('all five, independent fixture id and exact archived source', async () => {
      const facts = await parse(fixture());
      const result = parentConfigurationChecks(facts, sourcePath);
      assert.equal(Object.keys(result.checks).length, 5);
      assert.ok(result.passed);
      assert.equal(result.overview_id, '7654');
      const project = parentRegistration(source(facts));
      assert.equal(project.overview_id, 7654);
      assert.equal(project.source.sha256, 'a'.repeat(64));
      assert.equal(project.configuration_path, CONFIGURATION_PATH);
    });
    for (const [name, prefix, path] of [
      ['one traversal from bare build address', '../', '/build/123'],
      ['two traversals from overview address', '../../', sourcePath],
      ['same-origin absolute URLs', 'https://quickbuild.tizen.org/', sourcePath],
      ['root-relative paths', '/', sourcePath],
    ]) await t.test(name, async () => {
      const result = parentConfigurationChecks(await parse(fixture({ prefix })), path);
      assert.ok(result.passed);
      assert.equal(result.overview_id, '7654');
    });
    await t.test('resolution uses archived address, not a guessed depth or HTML base', async () => {
      const facts = await parse(`<base href="https://elsewhere.invalid/">${fixture({ prefix: '../' })}`);
      assert.ok(parentConfigurationChecks(facts, '/build/123').passed);
      assert.equal(parentConfigurationChecks(facts, sourcePath).passed, false);
      assert.equal(parentConfigurationChecks(facts).passed, false);
    });
    await t.test('live-08 archived overview passes all five revised checks without navigation', async () => {
      const html = readFileSync(new URL('../../docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C2b/live-08/01.response.html', import.meta.url), 'utf8');
      const facts = await parse(html);
      const result = parentConfigurationChecks(facts, '/build/1193467/overview');
      assert.deepEqual(result.checks, { overview_link: true, sibling_tabs: true,
        breadcrumb: true, copy_path: true, build_name: true });
      assert.equal(parentRegistration({ ...source(facts), path: '/build/1193467/overview' }).overview_id, 1917);
    });
    for (const key of ['overview', 'pipeline', 'children']) {
      const kind = key;
      for (const [name, href] of [
        ['query', `../../${kind}/7654?1`],
        ['empty-query', `../../${kind}/7654?`],
        ['fragment', `../../${kind}/7654#section`],
        ['empty-fragment', `../../${kind}/7654#`],
        ['external-url', `https://elsewhere.invalid/${kind}/7654`],
        ['http-downgrade', `http://quickbuild.tizen.org/${kind}/7654`],
        ['trailing-segment', `../../${kind}/7654/x`],
        ['zero', `../../${kind}/0`],
        ['negative', `../../${kind}/-1`],
        ['non-integer', `../../${kind}/1.5`],
        ['unsafe-integer', `../../${kind}/9007199254740992`],
        ['malformed-url', 'https://['],
      ]) await t.test(`${key} rejects ${name}`, async () => {
        const facts = await parse(fixture({ [key]: href }));
        assert.equal(parentConfigurationChecks(facts, sourcePath).passed, false);
        assert.throws(() => parentRegistration(source(facts)), /CONFIGURATION_SOURCE_MISMATCH/);
      });
    }
    const mutations = [
      ['missing-overview', html => html.replace('tab-ConfigurationOverview', 'other')],
      ['duplicate-overview', html => html + '<li class="tab-ConfigurationOverview"><a class="nav-link" href="../../overview/7654">copy</a></li>'],
      ['overview-id', html => html.replace('../../overview/7654', '../../overview/7655')],
      ['pipeline-id', html => html.replace('../../pipeline/7654', '../../pipeline/7655')],
      ['children-id', html => html.replace('../../children/7654', '../../children/7655')],
      ['missing-pipeline', html => html.replace('tab-PipelinePage', 'other')],
      ['duplicate-pipeline', html => html + '<li class="tab-PipelinePage"><a class="nav-link" href="../../pipeline/7654">Pipelines</a></li>'],
      ['missing-children', html => html.replace('tab-ChildrenPage', 'other')],
      ['duplicate-children', html => html + '<li class="tab-ChildrenPage"><a class="nav-link" href="../../children/7654">Children</a></li>'],
      ['wrong-breadcrumb', () => fixture({ path: CONFIGURATION_PATH.replace('/RBS/', '/SBS/') })],
      ['last-not-current', () => fixture({ current: false })],
      ['duplicate-breadcrumb', html => html + html.match(/<div id="breadcrumb">.*?<\/div>/)[0]],
      ['wrong-copy', () => fixture({ copy: CONFIGURATION_PATH.replace('/RBS/', '/SBS/') })],
      ['missing-copy', html => html.replace('onCopyClipboardLinkDomReady', 'other')],
      ['wrong-copy-anchor', html => html.replace("('copy',", "('missing',")],
      ['duplicate-copy', html => html + `<script>onCopyClipboardLinkDomReady('copy', '${CONFIGURATION_PATH}');</script>`],
      ['wrong-build-prefix', () => fixture({ name: 'TIZEN_SBS_TRIGGER_FIXTURE' })],
      ['missing-build-name', html => html.replace('build-header', 'other')],
      ['duplicate-build-name', html => html + `<div class="build-header"><div class="text-2xl">${BUILD_PREFIX}COPY</div></div>`],
    ];
    for (const [name, mutate] of mutations) await t.test(`parent rejects ${name}`, async () => {
      const facts = await parse(mutate(fixture()));
      assert.equal(parentConfigurationChecks(facts, sourcePath).passed, false);
      assert.throws(() => parentRegistration(source(facts)), /CONFIGURATION_SOURCE_MISMATCH/);
    });
    await t.test('configuration page requires same breadcrumb and copy path, no build name', async () => {
      const facts = await parse(fixture().replace('build-header', 'other'));
      assert.ok(configurationPageChecks(facts).passed);
      assert.equal(Object.keys(configurationPageChecks(facts).checks).length, 2);
    });
    for (const [name, options] of [
      ['wrong-path', { path: CONFIGURATION_PATH.replace('/RBS/', '/SBS/') }],
      ['wrong-copy', { copy: CONFIGURATION_PATH + '/other' }],
    ]) await t.test(`configuration page rejects ${name}`, async () => {
      assert.equal(configurationPageChecks(await parse(fixture(options))).passed, false);
    });
    await t.test('registration cannot use absent, subpage or unarchived source', async () => {
      const row = source(await parse(fixture()));
      for (const value of [undefined, { ...row, path: '/build/123' }, { ...row, path: '/build/123/variables' },
        { ...row, id_verified: false }, { ...row, id_verified: undefined },
        { ...row, sha256: null }, { ...row, status: 403 }]) {
        assert.throws(() => parentRegistration(value), /CONFIGURATION_SOURCE_MISMATCH/);
      }
    });
    assert.equal(runtime.page.url(), 'about:blank');
    console.log('C2B-04/07 selectors: synthetic DOMParser inputs and archived live-08 only, no network or navigation');
  } finally { await runtime.close(); }
});
