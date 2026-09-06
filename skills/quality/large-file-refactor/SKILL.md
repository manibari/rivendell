---
name: large-file-refactor
loop: dev
pdca: act
description: >
  Systematically split large single-file components (500+ lines) into modular
  architecture while preserving interface compatibility.
  TRIGGER when: file exceeds 500 lines, user mentions "monolith", "模組化重構",
  or asks to split a large component/module.
  DO NOT TRIGGER when: file is under 300 lines, or change is purely cosmetic.
when_to_use: when a file exceeds 500 lines or user asks to modularize/split a large component
version: 1.0.0
tags: [quality, refactoring]
languages: all
source: harvest-auto
---

# Large File Refactor

## Overview

Files over 500 lines are hard to navigate, test, and maintain. This skill provides
a repeatable workflow to split them into focused modules while keeping existing
import paths working.

Applies to: React/Next.js components, Vue SFCs, Python modules, FastAPI routers.

## Workflow

### Step 1: Read and map the file

Read the entire file first. Identify logical boundaries:

```bash
wc -l <file>   # confirm it's worth splitting
```

Look for natural split points:
- **By feature / domain** — each section handles a distinct concept
- **By route segment** — in Next.js, each page section or sub-route
- **By abstraction level** — data fetching vs. UI vs. utilities
- **By size** — aim for sub-files under 150 lines each

List the boundaries before touching any code.

### Step 2: Extract sub-modules one at a time

For each section:
1. Create the target file
2. Move the code (types, functions, component)
3. Add necessary imports in the new file
4. Export everything the parent needs

**Key rule**: Extract one section at a time and verify before moving to the next.

### Step 3: Create an index re-export (preserves old import paths)

```typescript
// components/deals/index.ts
export { DealHeader } from "./DealHeader";
export { DealTimeline } from "./DealTimeline";
export { DealActions } from "./DealActions";
export type { DealPageProps } from "./types";
```

```python
# services/__init__.py
from .embeddings import EmbeddingService
from .search import VectorSearchService
```

### Step 4: Validate

```bash
# TypeScript / Next.js
npx tsc --noEmit
npm run build

# Python
python -m py_compile <files>
python -m pytest -x --tb=short
```

Fix any import errors before continuing.

### Step 5: Clean up original file

The original file should now be either:
- Deleted (fully replaced by the index)
- Reduced to a thin orchestrator importing from the new modules

## Example: 1343-line React Component → 4 files

```
Before:
  app/deals/[id]/page.tsx   (1343 lines)

After:
  app/deals/[id]/
  ├── page.tsx              (80 lines — orchestrator)
  ├── DealHeader.tsx        (120 lines)
  ├── DealTimeline.tsx      (200 lines)
  ├── DealActions.tsx       (150 lines)
  └── types.ts              (40 lines)
```

## Common Pitfalls

- **Circular imports**: if A imports B and B imports A, extract shared types to `types.ts`
- **Missing exports**: TypeScript catches these at compile time via `tsc --noEmit`
- **Prop drilling**: if splitting creates 5+ prop layers, consider context or a state hook
- **Test file location**: co-locate tests with the new files

## Integration

| Skill | When |
|-------|------|
| **code-reviewer** | After refactor — review the new structure |
| **qa-testing** | Write unit tests for each new module |
| **systematic-debugging** | If TypeScript/import errors appear after splitting |
