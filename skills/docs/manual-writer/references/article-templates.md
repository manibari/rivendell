# Article templates

Each article has one topic type. Pick the type, then copy its template.
Microsoft publishes no definitions of these types. The shapes follow the Microsoft Learn
community templates for how-to and tutorial articles:
https://learn.microsoft.com/en-us/community/templates/how-to-template and
https://learn.microsoft.com/en-us/community/templates/tutorial-template.
The section names (必要條件、後續步驟、相關文章) are rivendell choices; `相關文章` is seen on zh-TW Support pages.

The project frontmatter and heading level come from the project (step 1 of `SKILL.md`).
The templates below start at `##`, as a page that shows the title by itself.

| Type | The reader asks | One article holds |
|---|---|---|
| 快速入門 | 第一次用，從哪裡開始？ | The shortest path to one useful result, in less than 10 minutes |
| 操作說明 | 我要怎麼做到 X？ | One user goal, as one or more procedures |
| 概念 | X 是什麼、為什麼這樣運作？ | One idea: terms, states, rules, no procedure |
| 參考 | X 有哪些欄位、狀態或選項？ | Tables to look up, no procedure |
| 疑難排解 | 畫面出現 Y，怎麼辦？ | Symptom, cause, solution, one block for each symptom |

Do not mix types in one article. A concept that a procedure needs goes in a concept article, and the procedure links to it.

## 快速入門

```markdown
本文說明如何在 10 分鐘內完成第一筆報價。完成後，您會有一筆可以送出的報價。

## 必要條件

- 您的帳號有 [業務] 角色。
- 系統中至少有一筆商機。

## 建立第一筆報價

若要從商機建立報價，請使用下列步驟。

1. ...

## 後續步驟

- [送出報價並追蹤狀態](/manual/quotes-contracts)
```

## 操作說明

```markdown
<One or two sentences: the goal, and who does it.>

## 必要條件

<Role or permission, data that must exist, a module that must be on. Leave the section out when there is none.>

## <Task 1: verb + object>

<Intro sentence that does not repeat the heading.>

1. 在 [<page>] 頁面，選取 [<control>]。
2. ...

   <Result, when it is not clear.>

<A different start point for the same task, in one sentence.>

## <Task 2: verb + object>

...

## 相關文章

- [<article title>](/manual/<slug>)
```

## 概念

```markdown
<One paragraph: what it is and why it matters to the reader.>

## <Sub-idea 1>

<Short paragraphs. A table for states or rules.>

| 狀態 | 意義 | 下一個可用動作 |
| --- | --- | --- |
| 草稿 | 尚未送出，可以修改 | 送出、刪除 |

## 相關文章
```

## 參考

```markdown
<One sentence: what the tables list.>

## <Screen or object name>

下表列出 [<page>] 頁面的欄位。

| 欄位 | 說明 | 必填 |
| --- | --- | --- |
| 單號 | 系統自動產生，格式為 Q-年份-序號 | 不適用 |
```

## 疑難排解

```markdown
<One sentence: which screen or task this article covers.>

## 畫面顯示「<exact message>」

**原因：** <one or two sentences>

**解決方法：**

1. ...

## <Next symptom>
```

Write each symptom as the reader sees it: the exact message in `「」`, or what the screen does.
