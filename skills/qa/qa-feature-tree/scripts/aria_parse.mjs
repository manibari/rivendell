export const INTERACTIVE_ROLES = Object.freeze([
  'button', 'link', 'textbox', 'searchbox', 'combobox', 'checkbox',
  'radio', 'switch', 'tab', 'menuitem', 'slider',
]);

const rolePattern = new RegExp(`^\\s*- (${INTERACTIVE_ROLES.join('|')})(?=\\s|:|$)(.*)$`);

// Playwright wraps the whole node key in YAML single quotes when the name holds
// ": " (seen 2026-11-19: - 'button "時間: 10:00"'). Inside, '' is one quote.
function unwrapSingleQuotedKey(line) {
  const match = /^(\s*- )'(.*)$/.exec(line);
  if (!match) return line;
  const body = match[2];
  let key = '';
  for (let index = 0; index < body.length; index += 1) {
    if (body[index] !== "'") {
      key += body[index];
    } else if (body[index + 1] === "'") {
      key += "'";
      index += 1;
    } else {
      return `${match[1]}${key}${body.slice(index + 1)}`;
    }
  }
  return line;
}

export function parseAriaSnapshot(text) {
  const controls = [];
  for (const line of text.split(/\r?\n/)) {
    const match = rolePattern.exec(unwrapSingleQuotedKey(line));
    if (!match) continue;

    const rest = match[2].trimStart();
    let name = '';
    if (rest.startsWith('"')) {
      let escaped = false;
      for (let index = 1; index < rest.length; index += 1) {
        const char = rest[index];
        if (escaped) {
          name += char;
          escaped = false;
        } else if (char === '\\') {
          escaped = true;
        } else if (char === '"') {
          break;
        } else {
          name += char;
        }
      }
    } else if (rest.startsWith('/')) {
      const end = rest.lastIndexOf('/');
      if (end > 0) name = rest.slice(0, end + 1);
    }
    controls.push({ role: match[1], name });
  }
  return controls;
}
