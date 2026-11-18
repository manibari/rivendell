import fs from "node:fs";
import { currentRun } from "./support/store";

export default function globalSetup(): void {
  const run = currentRun();
  if (!fs.existsSync(run.home) || !fs.existsSync(run.database)) {
    throw new Error("E2E fixture 尚未建立。");
  }
}
