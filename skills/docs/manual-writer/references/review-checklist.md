# Review checklist

`scripts/check-manual.py` checks the form. This list holds what only a reader can judge.
For each item, write 通過 or the reason it does not pass. An item with no answer is not checked.

## For each article

1. The article has one topic type, and its sections follow the template of that type.
2. The first paragraph tells the goal. A reader can decide in 10 seconds if this is the right article.
3. Each label in brackets matches the live screen today. Write the date you looked.
4. Each procedure starts at a place that the reader can reach from the home screen or the menu.
5. A new user can do each step with only the text, without the screenshot.
6. Each step that changes the screen in a way that is not clear tells the result.
7. 必要條件 lists each role, permission, module, or data the task needs, or the article has no such need.
8. The article uses demo data only: no customer name, real person, credential, or internal address.
9. Each term is the same word as in the other articles and on the screen.
10. Each screenshot has badge numbers that match the step numbers, and its spec file still captures.

## For the whole manual

1. Each task from the task list (step 2 of `SKILL.md`) is in exactly one 操作說明 article.
2. Each 操作說明 article links to the 概念 article for each idea it uses.
3. Each error message that a reader can see in the tasks has a 疑難排解 entry, or a reason why not.
4. The index or menu order follows the order of the work: first-time setup first, then daily work.
