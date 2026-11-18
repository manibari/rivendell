import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import { INTERACTIVE_ROLES, parseAriaSnapshot } from '../aria_parse.mjs';

const fixtures = path.join(path.dirname(fileURLToPath(import.meta.url)), 'fixtures/web');

test('the role list follows the screen scan contract', () => {
  assert.deepEqual(INTERACTIVE_ROLES, [
    'button', 'link', 'textbox', 'searchbox', 'combobox', 'checkbox',
    'radio', 'switch', 'tab', 'menuitem', 'slider',
  ]);
});

test('parses keys that Playwright wraps in single quotes', () => {
  const snapshot = [
    `- 'button "時間: 10:00"'`,
    `- 'textbox "key: value"': 目前的值`,
    `- 'link "a: b"':`,
    '  - /url: /a',
    `- 'button "It''s: ok" [disabled]'`,
    `- 'heading "標題: 一" [level=1]'`,
  ].join('\n');
  assert.deepEqual(parseAriaSnapshot(snapshot), [
    { role: 'button', name: '時間: 10:00' },
    { role: 'textbox', name: 'key: value' },
    { role: 'link', name: 'a: b' },
    { role: 'button', name: "It's: ok" },
  ]);
});

test('parses every documented node form', () => {
  const snapshot = [
    '- button "儲存"',
    '- button "儲存" [disabled]',
    '- link "首頁":',
    '  - /url: /',
    '- textbox "搜尋": 目前的值',
    '- checkbox "同意" [checked]',
    '- button',
    '- button "說 \\"好\\""',
    '- tab "浪費報告" [selected]',
    '- link /詳細資料 .*/:',
  ].join('\n');
  assert.deepEqual(parseAriaSnapshot(snapshot), [
    { role: 'button', name: '儲存' },
    { role: 'button', name: '儲存' },
    { role: 'link', name: '首頁' },
    { role: 'textbox', name: '搜尋' },
    { role: 'checkbox', name: '同意' },
    { role: 'button', name: '' },
    { role: 'button', name: '說 "好"' },
    { role: 'tab', name: '浪費報告' },
    { role: 'link', name: '/詳細資料 .*/' },
  ]);
});

test('ignores containers and noninteractive roles across three nesting levels', () => {
  assert.deepEqual(parseAriaSnapshot([
    '- navigation:',
    '  - list:',
    '    - listitem:',
    '      - link "首頁":',
    '        - /url: /',
    '  - heading "標題" [level=1]',
    '  - paragraph: 文字',
    '    - text: 更多文字',
    '  - img "圖示"',
    '  - button "開啟"',
  ].join('\n')), [
    { role: 'link', name: '首頁' },
    { role: 'button', name: '開啟' },
  ]);
});

test('handles an empty snapshot and Windows line endings', () => {
  assert.deepEqual(parseAriaSnapshot(''), []);
  assert.deepEqual(parseAriaSnapshot('- button "一"\r\n  - button "二"\r\n'), [
    { role: 'button', name: '一' },
    { role: 'button', name: '二' },
  ]);
});

test('parses a page snapshot with navigation, a form, and tabs', async () => {
  const snapshot = await readFile(path.join(fixtures, 'page.snapshot.txt'), 'utf8');
  assert.deepEqual(parseAriaSnapshot(snapshot), [
    { role: 'link', name: '首頁' },
    { role: 'link', name: '報告' },
    { role: 'textbox', name: '搜尋' },
    { role: 'button', name: '送出' },
    { role: 'tab', name: '總覽' },
    { role: 'tab', name: '浪費報告' },
  ]);
});
