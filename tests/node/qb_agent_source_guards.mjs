import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { runInNewContext } from 'node:vm';

// Offline, with no npm dependency: Node ships Acorn for its own JS parsing.
// This private Node interface is deliberately fail-closed if a runtime omits it.
const acornSource = process.binding('natives')['internal/deps/acorn/acorn/dist/acorn'];
assert.equal(typeof acornSource, 'string', 'Source guards require Node bundled Acorn');
const parser = { exports: {} };
runInNewContext(acornSource, { exports: parser.exports, module: parser });
const parse = (source) => parser.exports.parse(source, {
  ecmaVersion: 'latest', sourceType: 'module', locations: true,
});

const MAIN_WORLD = new Set(['evaluate', 'evaluateAll', 'evaluateHandle', '$eval', '$$eval',
  'waitForFunction', 'addScriptTag', 'exposeFunction', 'exposeBinding']);
const INTERACTIONS = new Set(['click', 'dblclick', 'fill', 'press', 'type', 'tap', 'check',
  'uncheck', 'setChecked', 'selectOption', 'pressSequentially', 'insertText', 'dispatchEvent',
  'focus', 'blur', 'hover', 'dragTo', 'dragAndDrop', 'setInputFiles', 'clear', 'selectText',
  'down', 'up', 'move', 'wheel', 'submit', 'requestSubmit']);
const SENSITIVE = new Set(['headers', 'postData', 'postDataEntries']);
const TEST_OPTIONS = /^(?:testOptions|test_options|launchArgs|launch_args|useBrowserFetch|use_browser_fetch|syntheticCount|synthetic_count)$/;
const HTTP_MODULE = /^(?:node:)?(?:https?|http2)$|^(?:undici|axios|got|node-fetch|superagent)(?:\/|$)/;
const FUNCTION = /^(?:FunctionDeclaration|FunctionExpression|ArrowFunctionExpression)$/;

function walk(node, visit, ancestors = []) {
  if (!node || typeof node.type !== 'string') return;
  visit(node, ancestors);
  for (const [key, value] of Object.entries(node)) {
    if (key === 'loc') continue;
    for (const child of Array.isArray(value) ? value : [value]) {
      if (child && typeof child.type === 'string') walk(child, visit, [...ancestors, node]);
    }
  }
}

function literal(node) {
  if (node?.type === 'Literal') return node.value;
  if (node?.type === 'TemplateLiteral' && !node.expressions.length) return node.quasis[0].value.cooked;
  if (node?.type === 'BinaryExpression' && node.operator === '+') {
    const left = literal(node.left), right = literal(node.right);
    if (typeof left === 'string' && typeof right === 'string') return left + right;
  }
}

function key(node) {
  const property = node?.property ?? node?.key;
  return node?.computed ? literal(property) : property?.name ?? literal(property);
}

function member(node, object, property) {
  return node?.type === 'MemberExpression' && key(node) === property
    && node.object.type === 'Identifier' && node.object.name === object;
}

function callable(node) {
  if (node?.type === 'ChainExpression') return callable(node.expression);
  return node?.type === 'MemberExpression' ? key(node) : node?.name;
}

function nearestFunction(ancestors) {
  return ancestors.findLast((node) => FUNCTION.test(node.type));
}

function codeName(node, ancestors) {
  if (node.type === 'MemberExpression' || node.type === 'Property' || node.type === 'MethodDefinition') return key(node);
  if (node.type !== 'Identifier') return null;
  const parent = ancestors.at(-1);
  if ((parent?.type === 'MemberExpression' && parent.property === node && !parent.computed)
    || ((parent?.type === 'Property' || parent?.type === 'MethodDefinition') && parent.key === node)) return null;
  return node.name;
}

function nullFunction(node) {
  if (!FUNCTION.test(node?.type) || node.params.length || node.async || node.generator) return false;
  const body = node.body.type === 'BlockStatement' && node.body.body.length === 1
    && node.body.body[0].type === 'ReturnStatement' ? node.body.body[0].argument : node.body;
  return body?.type === 'Literal' && body.value === null;
}

function windowOpenGuard(callback) {
  if (!FUNCTION.test(callback?.type) || callback.params.length || callback.async || callback.generator) return false;
  let body = callback.body;
  if (body.type === 'BlockStatement' && body.body.length === 1) {
    body = body.body[0].expression ?? body.body[0].argument;
  }
  if (body?.type !== 'CallExpression' || !member(body.callee, 'Object', 'defineProperty')) return false;
  const [target, name, descriptor] = body.arguments;
  if (body.arguments.length !== 3 || target.type !== 'Identifier' || target.name !== 'window'
    || literal(name) !== 'open' || descriptor.type !== 'ObjectExpression') return false;
  const props = descriptor.properties;
  return props.length === 3 && props.every((p) => p.type === 'Property' && p.kind === 'init' && !p.method)
    && props.some((p) => key(p) === 'value' && nullFunction(p.value))
    && ['configurable', 'writable'].every((name) => props.some((p) => key(p) === name && literal(p.value) === false));
}

/** Inspect JS text only; return {rule, line, column, message}[] (one-based positions).
 * The named exceptions are top-level adaptProtocol/startupSelfTest and the
 * awaited, pre-page window.open installation in createRuntime/launchRuntime.
 * This is a regression guard for this source, not a general JS sandbox.
 */
export function inspectAgentSource(source) {
  assert.equal(typeof source, 'string');
  let tree;
  try { tree = parse(source); }
  catch (error) {
    return [{ rule: 'parse', line: error.loc?.line ?? 1, column: (error.loc?.column ?? 0) + 1,
      message: 'Agent source must parse as an ES module' }];
  }
  const violations = [], entries = [], topFunctions = new Map(), methods = new Map();
  const report = (rule, node, message) => violations.push({ rule,
    line: node.loc.start.line, column: node.loc.start.column + 1, message });
  walk(tree, (node, ancestors) => {
    entries.push({ node, ancestors });
    if (node.type === 'FunctionDeclaration' && ancestors.every((a) => ['Program', 'ExportNamedDeclaration'].includes(a.type))) {
      topFunctions.set(node.id.name, node);
    }
    if (node.type === 'MethodDefinition' && ancestors.findLast((a) => a.type === 'ClassDeclaration')?.id.name === 'Agent') {
      methods.set(key(node), node.value);
    }
  });
  const inFunction = (ancestors, name) => {
    const fn = topFunctions.get(name);
    return Boolean(fn && ancestors.includes(fn));
  };
  const requestAliases = new Set(['request', 'apiRequest', 'requestContext']);
  let changed;
  do {
    changed = false;
    for (const { node } of entries) {
      const target = node.type === 'VariableDeclarator' ? node.id : node.type === 'AssignmentExpression' ? node.left : null;
      const value = node.type === 'VariableDeclarator' ? node.init : node.right;
      if (target?.type === 'Identifier' && value?.type === 'Identifier'
        && requestAliases.has(value.name) && !requestAliases.has(target.name)) {
        requestAliases.add(target.name); changed = true;
      }
    }
  } while (changed);

  // Follow direct helper calls from login as well as the login dispatch branch.
  const loginRoots = new Set(methods.has('login') ? [methods.get('login')] : []);
  for (const { node, ancestors } of entries) {
    if (node.type !== 'IfStatement' || !ancestors.includes(methods.get('command'))) continue;
    const t = node.test;
    if (t.type === 'BinaryExpression' && ['===', '=='].includes(t.operator)
      && (literal(t.left) === 'login' || literal(t.right) === 'login')) loginRoots.add(node.consequent);
  }
  for (const root of loginRoots) {
    walk(root, (node) => {
      if (node.type !== 'CallExpression') return;
      const callee = node.callee;
      const target = callee.type === 'Identifier' ? topFunctions.get(callee.name)
        : callee.type === 'MemberExpression' && callee.object.type === 'ThisExpression' ? methods.get(key(callee)) : null;
      if (target) loginRoots.add(target);
    });
  }

  const initReferences = [];
  for (const { node, ancestors } of entries) {
    const name = codeName(node, ancestors), parent = ancestors.at(-1);
    const call = node.type === 'CallExpression' ? node : null;
    const callName = call && callable(call.callee);
    if (MAIN_WORLD.has(name)) report('main-world', node, `${name} is a main-world execution interface`);
    if (['cookies', 'storageState', 'cloneNode'].includes(name)) report(name, node, `${name} is forbidden`);
    if (SENSITIVE.has(name) && !inFunction(ancestors, 'adaptProtocol')) {
      report('protocol-fields', node, `${name} is only permitted inside adaptProtocol`);
    }
    if (name === 'ignoreHTTPSErrors') {
      const value = node.type === 'Property' ? node.value
        : parent?.type === 'AssignmentExpression' && parent.left === node ? parent.right : null;
      if (literal(value) !== false) report('tls', node, 'ignoreHTTPSErrors must not enable a certificate bypass');
    }
    if (['DEBUG', 'PWDEBUG'].includes(name)) {
      const value = node.type === 'Property' ? node.value
        : parent?.type === 'AssignmentExpression' && parent.left === node ? parent.right : null;
      if (value && !['', '0', false, null].includes(literal(value))) report('protocol-debug', node, 'Protocol debug logging must not be enabled');
    }
    if (node.type === 'Literal' && typeof node.value === 'string' && /(?:DEBUG|PWDEBUG)=(?:pw|1|\*)/.test(node.value)) {
      report('protocol-debug', node, 'Protocol debug logging must not be enabled');
    }
    if (name === 'request' && node.type === 'MemberExpression') {
      // Playwright Response.request() is metadata, not an APIRequestContext.
      const responseMetadata = node.object.type === 'Identifier' && node.object.name === 'response'
        && parent?.type === 'CallExpression' && parent.callee === node && !parent.arguments.length;
      const protocolMetadata = member(node, 'event', 'request') && inFunction(ancestors, 'adaptProtocol');
      if (!responseMetadata && !protocolMetadata) report('http-client', node, 'Page/context HTTP request clients are forbidden');
    }
    if (name === 'newContext' && node.type === 'MemberExpression') {
      const objectName = callable(node.object);
      if (requestAliases.has(objectName)) {
        report('http-client', node, 'Request newContext is forbidden; browser.newContext is allowed');
      }
    }
    if (node.type === 'Property' && key(node) === 'request' && parent?.type === 'ObjectPattern') {
      const initializer = ancestors.at(-2)?.init;
      if (!(inFunction(ancestors, 'adaptProtocol') && initializer?.type === 'Identifier' && initializer.name === 'event')) {
        report('http-client', node, 'Request client destructuring is forbidden');
      }
    }
    if (name === 'fetch' || node.type === 'NewExpression' && callable(node.callee) === 'XMLHttpRequest') {
      report('http-client', node, 'Direct HTTP clients bypass the page interceptor');
    }
    const moduleName = node.type === 'ImportDeclaration' ? literal(node.source)
      : node.type === 'ImportExpression' ? literal(node.source)
        : callName === 'require' ? literal(call.arguments[0]) : null;
    if (typeof moduleName === 'string' && HTTP_MODULE.test(moduleName)) report('http-client', node, 'HTTP client imports are forbidden');
    if (INTERACTIONS.has(callName) && ancestors.some((a) => loginRoots.has(a))) {
      report('login-interaction', node, `${callName} must not interact with the login page`);
    }
    if (name === 'setContent' && (!topFunctions.has('startupSelfTest')
      || nearestFunction(ancestors) !== topFunctions.get('startupSelfTest')
      || !parent || parent.type !== 'CallExpression' || parent.callee !== node)) {
      report('set-content', node, 'setContent is only permitted as a direct call inside startupSelfTest');
    }
    if (name === 'addInitScript') {
      initReferences.push(node);
      const fn = nearestFunction(ancestors);
      const factory = fn && ['createRuntime', 'launchRuntime'].some((n) => topFunctions.get(n) === fn);
      const installer = parent?.type === 'CallExpression' && parent.callee === node ? parent : null;
      const receiver = node.type === 'MemberExpression' && (node.object.name === 'context'
        || member(node.object, 'runtime', 'context'));
      const beforeNavigation = fn && !entries.some(({ node: n, ancestors: a }) => n.type === 'CallExpression'
        && a.includes(fn) && n.start < node.start && ['goto', 'newPage', 'reload'].includes(callable(n.callee)));
      if (!factory || !receiver || !installer || installer.arguments.length !== 1
        || ancestors.at(-2)?.type !== 'AwaitExpression' || !beforeNavigation
        || !windowOpenGuard(installer.arguments[0])) {
        report('init-location', node, 'addInitScript must only install the awaited pre-navigation window.open guard');
      }
    }
    if (typeof name === 'string' && /^(?:refresh(?:es|Urls?|Set|Allowset|Allowlist)?|(?:register|extract|allow|allowed|registered).*refresh.*|.*refresh.*(?:set|urls?|allowlist|allowset))$/i.test(name)) {
      report('refresh', node, 'Refresh extraction, registration and allowsets are forbidden');
    }
    if (call && /^(?:querySelector(?:All)?|getAttribute|match(?:All)?|exec|add|set)$/.test(callName ?? '')) {
      let refresh = false;
      for (const arg of call.arguments) walk(arg, (n) => {
        if (/ajaxRefresh/i.test(String(literal(n) ?? n.regex?.pattern ?? ''))) refresh = true;
      });
      if (refresh) report('refresh', call, 'ajaxRefresh must not be extracted or registered');
    }
    if (inFunction(ancestors, 'main') && (TEST_OPTIONS.test(name ?? '')
      || node.type === 'Literal' && TEST_OPTIONS.test(String(node.value)))) {
      report('production-options', node, 'main must not pass test-only options');
    }
    if (call && inFunction(ancestors, 'main') && ['createRuntime', 'launchRuntime', 'startupSelfTest'].includes(callName)
      && (call.arguments.length !== 2 || call.arguments.some((n) => n.type === 'SpreadElement'))) {
      report('production-options', call, 'Production runtime calls must have exactly two ordinary arguments');
    }
  }
  if (initReferences.length !== 1) {
    for (const node of initReferences.length ? initReferences : [tree]) {
      report('init-count', node, `Expected exactly one addInitScript reference, found ${initReferences.length}`);
    }
  }
  return violations;
}

// Python's stdlib AST checks the real driver without importing or executing it.
const DRIVER_CHECK = String.raw`
import ast, json, re, sys
source = sys.stdin.read()
errors = []
def report(rule, node, message):
    errors.append(dict(rule=rule, line=getattr(node, 'lineno', 1),
                       column=getattr(node, 'col_offset', 0) + 1, message=message))
try:
    tree = ast.parse(source)
except SyntaxError as error:
    print(json.dumps([dict(rule='parse', line=error.lineno or 1,
                          column=error.offset or 1, message='Driver source must parse')]))
    sys.exit(0)
options = re.compile(r'^(?:test_?options|launch_?args|use_?browser_?fetch|synthetic_?count)$', re.I)
flags = ('--test', '--diagnostic', '--launch-args', '--host-resolver-rules',
         '--ignore-certificate-errors', '--use-browser-fetch', '--synthetic-count')
launches = []
for node in ast.walk(tree):
    name = node.id if isinstance(node, ast.Name) else node.attr if isinstance(node, ast.Attribute) else node.arg if isinstance(node, (ast.keyword, ast.arg)) else None
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        name = node.value
    if isinstance(name, str) and (options.fullmatch(name) or name.startswith(flags)):
        report('driver-options', node, 'Driver must not reference or pass test-only options')
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'Popen':
        launches.append(node)
        for keyword in node.keywords:
            if keyword.arg == 'diagnostic':
                report('driver-options', keyword, 'diagnostic is a response field, not a launch switch')
        argv = node.args[0] if node.args else next((k.value for k in node.keywords if k.arg == 'args'), None)
        # Freeze only the launch contract, not unrelated Python formatting.
        expected = ast.parse('[browser["node"], str(Path(__file__).with_name("qb_browser_agent.mjs")), browser["playwright_module"], browser["chromium"]]', mode='eval').body
        if argv is None or ast.dump(argv) != ast.dump(expected):
            report('driver-argv', argv or node, 'Driver argv must be exactly node, agent, Playwright module, Chromium')
            if isinstance(argv, (ast.List, ast.Tuple)):
                for index, item in enumerate(argv.elts):
                    if index >= len(expected.elts) or ast.dump(item) != ast.dump(expected.elts[index]):
                        report('driver-argv', item, 'Unexpected production launch argument')
if len(launches) != 1:
    report('driver-argv', tree, 'Expected exactly one explicit Popen launch')
print(json.dumps(errors))
`;

/** Inspect Python driver text using offline python3 -I and stdlib ast. */
export function inspectDriverSource(source) {
  assert.equal(typeof source, 'string');
  const result = spawnSync('python3', ['-I', '-c', DRIVER_CHECK], {
    input: source, encoding: 'utf8', timeout: 10000, maxBuffer: 4 * 1024 * 1024,
  });
  assert.ifError(result.error);
  assert.equal(result.status, 0, 'Driver source guards require working Python 3 stdlib ast');
  return JSON.parse(result.stdout);
}

function assertClean(violations, label) {
  assert.equal(violations.length, 0, `${label} source guard violations:\n${violations.map(
    ({ rule, line, column, message }) => `${line}:${column} [${rule}] ${message}`).join('\n')}`);
}

/** Throw AssertionError on any agent violation; otherwise return undefined. */
export function assertAgentSourceGuards(source) { assertClean(inspectAgentSource(source), 'Agent'); }

/** Throw AssertionError on any driver violation; otherwise return undefined. */
export function assertDriverSourceGuards(source) { assertClean(inspectDriverSource(source), 'Driver'); }
