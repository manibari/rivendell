import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdtemp, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { clipRect, parseSpec, placeBadges } from '../annotate-shot.mjs';

const cli = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../annotate-shot.mjs');

test('parseSpec applies defaults and resolves target-project paths', () => {
  const spec = parseSpec({ url: 'https://example.com/page', out: 'shots/page.png' }, 'spec.json');
  assert.deepEqual(spec, {
    url: 'https://example.com/page',
    out: path.resolve('shots/page.png'),
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 2,
    fullPage: false,
    mask: [],
    callouts: [],
  });
});

test('parseSpec reports all validation problems together', async () => {
  const directory = await mkdtemp(path.join(os.tmpdir(), 'manual-shot-unit-'));
  try {
    assert.throws(() => parseSpec({
      out: 'bad.jpg',
      storageState: path.join(directory, 'missing.json'),
      clip: '#panel',
      fullPage: true,
      typo: true,
      callouts: [
        { n: 0, selector: '#one' },
        { n: 2, selector: '#two' },
        { n: 2, selector: '#three' },
      ],
    }, 'bad.json'), (error) => {
      for (const expected of ['url', 'out', 'storageState', 'clip', 'fullPage', 'typo', 'callouts[0].n', '重複']) {
        assert.match(error.message, new RegExp(expected.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
      }
      return true;
    });
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test('parseSpec rejects invalid viewport, scale, mask and callout selectors', () => {
  assert.throws(() => parseSpec({
    url: 'file:///page.html', out: 'shot.png', viewport: { width: 0, height: 1.5 },
    deviceScaleFactor: 4, mask: [''], callouts: [{ n: 1, selector: '' }],
  }, 'bad.json'), /url.*viewport.width.*viewport.height.*deviceScaleFactor.*mask\[0\].*callouts\[0\].selector/);
});

test('placeBadges keeps ten crowded badges inside bounds without overlap', () => {
  const bounds = { x: 12, y: 20, width: 300, height: 180 };
  const badges = placeBadges(Array.from({ length: 10 }, (_, index) => ({
    n: index + 1, x: 24, y: 30, width: 80, height: 30,
  })), bounds, 24);
  assert.equal(badges.length, 10);
  for (const [index, badge] of badges.entries()) {
    assert.ok(badge.x >= bounds.x && badge.x + 24 <= bounds.x + bounds.width);
    assert.ok(badge.y >= bounds.y && badge.y + 24 <= bounds.y + bounds.height);
    for (const earlier of badges.slice(0, index)) {
      assert.ok(badge.x + 24 <= earlier.x || earlier.x + 24 <= badge.x
        || badge.y + 24 <= earlier.y || earlier.y + 24 <= badge.y);
    }
  }
});

test('clipRect clamps at all page edges', () => {
  const page = { width: 100, height: 80 };
  assert.deepEqual(clipRect({ x: 2, y: 3, width: 20, height: 10 }, 16, page),
    { x: 0, y: 0, width: 38, height: 29 });
  assert.deepEqual(clipRect({ x: 85, y: 65, width: 15, height: 15 }, 16, page),
    { x: 69, y: 49, width: 31, height: 31 });
});

test('CLI reports every invalid spec in filename order', async () => {
  const directory = await mkdtemp(path.join(os.tmpdir(), 'manual-shot-cli-'));
  try {
    await writeFile(path.join(directory, 'b.json'), JSON.stringify({ out: 'b.png' }));
    await writeFile(path.join(directory, 'a.json'), JSON.stringify({ url: 'https://example.com' }));
    const result = await new Promise((resolve, reject) => {
      const child = spawn(process.execPath, [cli, '--spec-dir', directory]);
      let stdout = '';
      let stderr = '';
      child.stdout.setEncoding('utf8').on('data', (chunk) => { stdout += chunk; });
      child.stderr.setEncoding('utf8').on('data', (chunk) => { stderr += chunk; });
      child.on('error', reject);
      child.on('close', (code) => resolve({ code, stdout, stderr }));
    });
    assert.equal(result.code, 1);
    assert.equal(result.stdout, '');
    const lines = result.stderr.trim().split('\n');
    assert.equal(lines.length, 2);
    assert.match(lines[0], /錯誤 .*a\.json:.*out/);
    assert.match(lines[1], /錯誤 .*b\.json:.*url/);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});
