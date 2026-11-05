import { fakeQuickBuild, PROJECT, overview, variables, VALUES } from './p5q_fake_quickbuild.mjs';

// Synthetic response shaped like live-04: four columns, plain anchors and a space directory.
export async function discoveryServer(mode = 'ok') {
  const fixture = await fakeQuickBuild();
  const child = '1193469', prefix = `/download/${child}/html/HTML%20REPORT/`;
  const page = body => `<!doctype html><link rel="icon" href="data:,"><span>Welcome! LocalTester</span>${body}`;
  fixture.discoveryHandler = (url, response, row) => {
    const path = url.pathname;
    if (path === '/build/1193467/overview' || path === `/build/${child}/overview`) {
      const id = path.split('/')[2];
      const config = PROJECT.configuration_path.replace('TRIGGER', id === child ? 'build' : 'TRIGGER');
      response.end(overview(id, 'Failed').replace('<title>QuickBuild</title>', `<title>QuickBuild - ${config}</title>`));
    } else if (path === '/build/1193467/variables') {
      response.end(variables('1193467'));
    } else if (path === `/build/${child}/variables`) {
      response.end(variables(child, { ...VALUES, 'Build Package List': 'platform/upstream/zlib@' + 'a'.repeat(40) })
        .replace('</tbody>', '<tr><td>PROJECT_BRANCH</td><td></td><td>tizen_base</td></tr></tbody>'));
    } else if (path === `/build/${child}/html_report`) {
      response.end(page(`<a class="nav-link">Build (id:${child})</a><iframe src="/download/${child}/html/HTML REPORT/index.html"></iframe>`));
    } else if (path === prefix + 'index.html') {
      const links = '<a href="logfiles/standard/armv7l/zlib.txt">failed</a>';
      response.end(page(`<h3>Details</h3><table><thead><tr><th>name</th><th>standard armv7l</th><th>standard aarch64</th><th>standard x86_64</th></tr></thead>
        <tbody><tr><td>zlib</td><td>${links}${mode === 'ambiguous' ? links : ''}</td><td>succeeded</td><td>succeeded</td></tr></tbody></table>`));
    } else if (path === prefix + 'logfiles/standard/armv7l/zlib.txt') {
      response.setHeader('Content-Type', mode === 'binary' ? 'application/octet-stream' : 'text/plain');
      if (mode === 'attachment') response.setHeader('Content-Disposition', 'attachment; filename="zlib.txt"');
      if (mode === 'redirect') {
        row.status = 302; response.writeHead(302, { Location: '/not-registered' }); response.end();
      } else if (mode === 'status') {
        row.status = 404; response.statusCode = 404; response.end('missing');
      } else if (mode === 'encoding') response.end(Buffer.from([0xff, 0xfe]));
      else if (mode === 'large') response.end(Buffer.alloc(64 * 1024 * 1024 + 1, 65));
      else response.end('LocalTester\nerror: compiler failure\n');
    } else return false;
    return true;
  };
  return fixture;
}
