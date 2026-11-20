import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const here = path.dirname(fileURLToPath(import.meta.url));
const cli = path.resolve(here, '../annotate-shot.mjs');
const fixture = path.join(here, 'fixtures/page.html');

function runCli(project, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [cli, ...args], { cwd: project });
    let stdout = '';
    let stderr = '';
    child.stdout.setEncoding('utf8').on('data', (chunk) => { stdout += chunk; });
    child.stderr.setEncoding('utf8').on('data', (chunk) => { stderr += chunk; });
    child.on('error', reject);
    child.on('close', (code) => resolve({ code, stdout, stderr }));
  });
}

test('captures annotated controls and continues after a duplicate selector', {
  skip: !process.env.MW_PLAYWRIGHT_PROJECT && 'Set MW_PLAYWRIGHT_PROJECT to a project with @playwright/test installed',
}, async () => {
  const project = path.resolve(process.env.MW_PLAYWRIGHT_PROJECT);
  const html = await readFile(fixture);
  const server = createServer((_request, response) => {
    response.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
    response.end(html);
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const temporary = await mkdtemp(path.join(os.tmpdir(), 'manual-shot-browser-'));
  try {
    const url = `http://127.0.0.1:${server.address().port}/`;
    const goodOut = path.join(temporary, 'good.png');
    const badOut = path.join(temporary, 'bad.png');
    const goodSpec = path.join(temporary, 'good.json');
    const badSpec = path.join(temporary, 'bad.json');
    await writeFile(goodSpec, JSON.stringify({
      url, out: goodOut, viewport: { width: 640, height: 480 }, deviceScaleFactor: 2,
      callouts: [
        { n: 1, selector: 'role=button[name="新增報價"]' },
        { n: 2, selector: 'role=combobox[name="狀態"]' },
      ],
    }));
    await writeFile(badSpec, JSON.stringify({
      url, out: badOut, callouts: [{ n: 3, selector: 'role=button[name="刪除"]' }],
    }));

    const good = await runCli(project, ['--spec', goodSpec]);
    assert.equal(good.code, 0, good.stderr);
    assert.match(good.stdout, /\(2 個標註\)/);
    const png = await readFile(goodOut);
    assert.equal(png.toString('ascii', 1, 4), 'PNG');
    assert.equal(png.readUInt32BE(16), 1280);
    assert.equal(png.readUInt32BE(20), 960);

    const bad = await runCli(project, ['--spec', badSpec]);
    assert.equal(bad.code, 1);
    assert.match(bad.stderr, /標號 3.*刪除.*找到 2 個可見元素/);
    await assert.rejects(readFile(badOut), { code: 'ENOENT' });

    const both = await runCli(project, ['--spec', goodSpec, '--spec', badSpec]);
    assert.equal(both.code, 1);
    assert.match(both.stdout, /good\.png \(2 個標註\)/);
    assert.match(both.stderr, /找到 2 個可見元素/);
    assert.equal((await readFile(goodOut)).toString('ascii', 1, 4), 'PNG');
    await assert.rejects(readFile(badOut), { code: 'ENOENT' });
  } finally {
    await rm(temporary, { recursive: true, force: true });
    await new Promise((resolve) => server.close(resolve));
  }
});
