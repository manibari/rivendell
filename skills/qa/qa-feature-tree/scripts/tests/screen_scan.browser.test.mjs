import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { readFile, mkdtemp, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = path.join(here, 'fixtures/web');
const scanner = path.resolve(here, '../screen_scan.mjs');

function runScanner(project, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [scanner, ...args], { cwd: project });
    let stderr = '';
    child.stderr.setEncoding('utf8').on('data', (chunk) => { stderr += chunk; });
    child.on('error', reject);
    child.on('close', (code) => resolve({ code, stderr }));
  });
}

test('scans pages, states, missing samples, failed steps, and HTTP errors', {
  skip: !process.env.FT_PLAYWRIGHT_PROJECT && 'Set FT_PLAYWRIGHT_PROJECT to a project with @playwright/test installed',
}, async () => {
  const project = path.resolve(process.env.FT_PLAYWRIGHT_PROJECT);
  const server = createServer(async (request, response) => {
    const pathname = new URL(request.url, 'http://localhost').pathname;
    if (pathname === '/http-redirect') {
      response.writeHead(302, { location: '/plain' }).end();
      return;
    }
    if (pathname === '/client-redirect') {
      response.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
      response.end('<!doctype html><script>location.replace("/plain")</script>');
      return;
    }
    const file = pathname === '/plain' ? 'plain.html'
      : pathname === '/items/a%20b' ? 'dynamic.html' : null;
    if (!file) {
      response.writeHead(404).end('Not found');
      return;
    }
    response.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
    response.end(await readFile(path.join(fixtures, file)));
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const temporary = await mkdtemp(path.join(os.tmpdir(), 'screen-scan-test-'));
  try {
    const baseUrl = `http://127.0.0.1:${server.address().port}`;
    const out = path.join(temporary, 'scan.json');
    const result = await runScanner(project, [
      '--tree', path.join(fixtures, 'tree.json'), '--out', out,
      '--base-url', baseUrl, '--timeout-ms', '500',
    ]);
    assert.equal(result.code, 0, result.stderr);
    const scan = JSON.parse(await readFile(out, 'utf8'));
    assert.deepEqual(Object.keys(scan), ['schema', 'base_url', 'scanned_at', 'screens']);
    assert.equal(scan.schema, 1);
    assert.equal(scan.base_url, baseUrl);
    assert.match(scan.scanned_at, /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}[+-]\d\d:\d\d$/);
    assert.deepEqual(scan.screens.map(({ module, screen, state }) => [module, screen, state]), [
      ['demo', 'plain', 'default'], ['demo', 'plain', 'dialog'],
      ['demo', 'plain', 'failed'], ['demo', 'dynamic', 'default'],
      ['demo', 'http-redirect', 'default'], ['demo', 'client-redirect', 'default'],
      ['demo', 'no-sample', 'default'], ['demo', 'not-found', 'default'],
    ]);
    for (const entry of scan.screens) {
      assert.deepEqual(Object.keys(entry), ['module', 'screen', 'state', 'url', 'reached', 'error', 'controls', 'final_url']);
    }
    const [plain, dialog, failed, dynamic, httpRedirect, clientRedirect, noSample, notFound] = scan.screens;
    assert.equal(plain.reached, true);
    assert.equal(plain.error, null);
    assert.equal(plain.final_url, `${baseUrl}/plain`);
    assert.deepEqual(plain.controls, [
      { role: 'link', name: '首頁' }, { role: 'button', name: '開啟對話框' },
    ]);
    assert.equal(dialog.reached, true);
    assert.deepEqual(dialog.controls, [
      { role: 'link', name: '首頁' }, { role: 'button', name: '開啟對話框' },
      { role: 'button', name: '確認' }, { role: 'button', name: '取消' },
    ]);
    assert.equal(failed.reached, false);
    assert.equal(failed.final_url, `${baseUrl}/plain`);
    assert.match(failed.error, /步驟 1 失敗：.*不存在/s);
    assert.deepEqual(failed.controls, []);
    assert.equal(dynamic.reached, true);
    assert.equal(dynamic.url, `${baseUrl}/items/a%20b`);
    assert.equal(dynamic.final_url, dynamic.url);
    assert.deepEqual(dynamic.controls, [
      { role: 'link', name: '返回首頁' }, { role: 'button', name: '編輯項目' },
    ]);
    assert.equal(httpRedirect.reached, true);
    assert.equal(httpRedirect.final_url, `${baseUrl}/plain`);
    assert.equal(clientRedirect.reached, true);
    assert.equal(clientRedirect.final_url, `${baseUrl}/plain`);
    assert.equal(noSample.reached, false);
    assert.equal(noSample.final_url, null);
    assert.equal(noSample.error, '缺少 sample：label');
    assert.deepEqual(noSample.controls, []);
    assert.equal(notFound.reached, false);
    assert.equal(notFound.final_url, null);
    assert.match(notFound.error, /步驟 0（載入頁面）失敗：HTTP 404/);
    assert.deepEqual(notFound.controls, []);
  } finally {
    await rm(temporary, { recursive: true, force: true });
    await new Promise((resolve) => server.close(resolve));
  }
});
