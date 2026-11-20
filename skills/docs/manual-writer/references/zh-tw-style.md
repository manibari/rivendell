# zh-TW writing rules for manuals

Read this file before you write the first line of an article.
The Source column tells where each rule comes from:

- **MS**: Microsoft Writing Style Guide or Microsoft Learn contributor guide.
- **MS-TW**: Microsoft Chinese (Traditional) Style Guide, `zho-twn-StyleGuide.pdf` (2024-09-05).
- **MS-obs**: seen on zh-TW Microsoft Support pages, no written rule found.
- **R**: rivendell choice. Microsoft publishes no rule for it (checked 2026-11-20).

When a project rule and a rule in this file disagree, tell the user. Do not pick one in silence.

## Sources

- Step-by-step instructions: https://learn.microsoft.com/en-us/style-guide/procedures-instructions/writing-step-by-step-instructions
- Interactions with UI: https://learn.microsoft.com/en-us/style-guide/procedures-instructions/describing-interactions-with-ui
- Formatting text in instructions: https://learn.microsoft.com/en-us/style-guide/procedures-instructions/formatting-text-in-instructions
- Lists, headings, tables: https://learn.microsoft.com/en-us/style-guide/scannable-content/
- Alt text: https://learn.microsoft.com/en-us/style-guide/accessibility/alternative-text
- Alerts and images: https://learn.microsoft.com/en-us/contribute/content/markdown-reference
- Style quickstart: https://learn.microsoft.com/en-us/contribute/content/style-quick-start
- zh-TW guide: https://aka.ms/chinese-traditional-styleguide

## Steps

| Rule | Source |
|---|---|
| Use a numbered list for a procedure. A procedure with one step uses a bullet. | MS |
| Write one instruction in each step. You can combine short steps at the same place on the screen. | MS |
| Tell the location before the action: `在 [報價] 頁面，選取 [新增報價]。` | MS |
| Each step is a full sentence. It starts with the location or the verb, and ends with `。`. | MS |
| Include the last action, for example `選取 [儲存]。` | MS |
| Keep a list to seven steps if possible. Split a procedure of more than 12 steps into tasks. | MS |
| Do not put comments between steps. Put them after the procedure, or in an alert. | MS |
| Write an intro sentence before the procedure. It must not repeat the heading. | MS |
| When the result of a step is not clear, add the result as a second line of the step: `畫面會顯示 [報價詳情]。` | R |
| Write a menu path as `[帳戶] > [簽名]`, with one space on each side of `>`. | MS |

Correct:

```markdown
若要建立報價，請使用下列步驟。

1. 在 [報價] 頁面，選取 [新增報價]。
2. 在 [商機] 清單中，選取要報價的商機。
3. 輸入數量和單價，然後選取 [儲存]。

   畫面會顯示 [報價詳情]，狀態為 [草稿]。
```

Incorrect, with the reason:

```markdown
1. 從商機詳情按「新增報價」，或在「報價」清單按「新增報價」。
```

- Two start points in one step. Pick one path, and put the other path in one sentence after the procedure.
- `按` is a device verb. Use `選取`.
- `「」` marks a quote, not a screen name. Use `[ ]`.

## Verbs

Use verbs that work with each input method: mouse, touch, keyboard, and screen reader.

| Action | Use | Do not use | Source |
|---|---|---|---|
| Select a button, check box, list value, link, or tab | 選取 | 按一下、點擊、點選、單擊、按 | MS-TW |
| Type a value | 輸入 | 打、鍵入 | MS-TW |
| Go to a page, tab, or menu | 移至 | 跳到、切到 | MS-obs |
| Choose a preference | 選擇 | | MS-obs |
| Right-click (desktop only) | 以滑鼠右鍵按一下 | 右鍵點擊 | MS-TW |
| Clear a check box | 清除 | 取消勾選 | R |
| Turn a toggle on or off | 開啟、關閉 | 打開、關掉 | R |
| Open or close an app, pane, or file | 開啟、關閉 | 打開、關掉 | R |
| Move an item with the pointer | 拖曳 | 拉 | R |

## Screen names

| Rule | Source |
|---|---|
| Put the screen name in half-width brackets, exactly as the screen shows it: `[新增報價]`. Do not make it bold. | MS-TW |
| Remove the ellipsis or the colon of a label: `[另存新檔]`, not `[另存新檔...]`. | MS-TW, MS |
| Do not use brackets for icons, program names, files, paths, and URLs: `選取齒輪圖示`. | MS-TW |
| Add the element type only when it helps: `[大小寫須相符] 核取方塊`. | MS, MS-TW |
| Element types: 按鈕、核取方塊、索引標籤、功能表、清單方塊、檢視、對話方塊. | MS-TW |
| Put an error message in `「」`: `畫面會顯示「單價不可低於底價」。` | MS |
| Copy each label from the live screen. Do not copy it from code constants or old documents. | R |

Live zh-TW Support pages use bold and brackets together (`**[簽名]**`). Their markup is often broken. This skill follows the written rule of the zh-TW guide: brackets only.

## Voice and words

| Rule | Source |
|---|---|
| Address the reader as `您`. Use `你們` for the plural. | MS-TW |
| Start a step with the verb. You can use `請` in the intro sentence: `請使用下列步驟。` | MS-obs |
| Use a semi-formal, friendly tone. Do not talk down to the reader. | MS-TW |
| Use active voice: `系統會儲存報價。` | MS-TW |
| Use `如果`, not `倘若`. Use `其` or the noun, not `它`. Remove extra `的`. | MS-TW |
| Do not use `正在` in a heading. | MS-TW |
| Use one word for one concept in the whole manual. If the project has a 統一語言表, use its screen column. | MS |
| Use `登入`, not `登錄`. | MS |
| Use `停止回應`, not `當機` or `死當`. Use `封鎖清單` and `允許清單`, not `黑名單` and `白名單`. | MS-TW |
| Do not use developer words: API、endpoint、port、localhost、資料表、JSON. Tell what the reader sees. | R |

## Punctuation and spacing

| Rule | Source |
|---|---|
| In documents, use full-width `，。、：；！？「」《》＜＞`. Use half-width only for `( )` and `[ ]`. | MS-TW |
| Put one half-width space between Chinese and English letters or digits: `2026 年 11 月 20 日`、`在 Outlook 中`. | MS-TW |
| Put one half-width space between Chinese and half-width `( )` or `[ ]`: `選取 [儲存]`. | MS-TW |
| Put no space next to full-width punctuation. | MS-TW |
| Put no space inside parentheses: `(選用)`. | MS-TW |
| Do not use the em dash `——`. It looks like `一`. Use `( )` or `：`. | MS-TW |
| List items in a sentence with `、`, and the last item with `，以及`: `客戶、商機，以及報價`. | MS-TW |
| `「」` marks a quote, a new term, or emphasis. `《》` marks a book title. `＜＞` marks a chapter. | MS-TW |

## Bold, input, keys, numbers

| Rule | Source |
|---|---|
| Do not use bold or italic on Chinese text. Exceptions: headings, a word of strong emphasis, and text the reader types. | MS-TW |
| Make text that the reader types bold: `輸入 **Q-DEMO-001**`. | MS-TW |
| Make a placeholder bold, not italic: `輸入 **客戶名稱**`. | MS-TW |
| Write a key combination with no spaces: `Ctrl+S`. | MS |
| Key names: `空格鍵`、`退格鍵`、`向上鍵`. | MS-TW |
| Dates: `2026 年 11 月 20 日`. Time: `上午`、`下午`. Version: `4.2 版`. | MS-TW |
| Put a measure word after a number: `3 位使用者`、`5 筆報價`. | MS-TW |

## Headings

| Rule | Source |
|---|---|
| A task heading is a verb and an object: `建立報價`、`把報價轉成合約`. | MS, MS-obs |
| Use the same structure for each heading at one level. | MS |
| Put no punctuation at the end of a heading. | MS |
| Do not put two headings in a row with no text between them. | MS |
| Do not use `&` or `+` in a heading. Do not use bold or code style in a heading or in link text. | MS |
| Use a level-2 heading only when there are two or more topics. | MS |

## Tables

| Rule | Source |
|---|---|
| Do not use a table for a simple list. | MS |
| The left column names each row. Make each column header specific. | MS |
| Do not leave a cell empty, and do not use a dash. Write `不適用` or `無`. | MS |
| End the intro sentence of a table with `。`, not `：`. | MS |
| A header and a cell must not form one sentence together. | MS |

## Alerts

Readers skip alerts. Use one or two in an article, and never put two next to each other. (MS)

| Type | Label | Use for | Source |
|---|---|---|---|
| NOTE | 注意 | Information that a reader who skims must still see | MS, label MS-obs |
| TIP | 秘訣 | Optional help to do the task better | MS, label MS-obs |
| IMPORTANT | 重要 | Information without which the task fails | MS, label R |
| WARNING | 警告 | An action that can lose data or cannot be undone | MS, label R |

Write an alert as a blockquote: `> **注意：** 送出後的報價無法刪除，只能作廢。`

## Images

| Rule | Source |
|---|---|
| Add a screenshot when it saves words or adds clarity. | MS |
| The steps must work without the image, and the image must work without the steps. | MS |
| Alt text: 150 characters or fewer. Start with `螢幕擷取畫面`. Do not use the file name. Do not list each field. | MS, MS-obs |
| An image that only decorates gets empty alt text. | MS |
| Put only numbers in the image. Put labels in the text, where an editor can change them. | MS |

How to capture and mark a screenshot: [screenshots.md](screenshots.md).

## Links

| Rule | Source |
|---|---|
| The link text is the title of the target article. | R |
| Add `(英文)` after a link to a page in English only. | MS-TW |
