import fs from "node:fs";
import { currentRun } from "./store";

export interface RecordedCall {
  cmd: string;
  argv: string[];
  cwd: string;
  ts: string;
}

export function recordedCalls(): RecordedCall[] {
  const text = fs.readFileSync(currentRun().recorderLog, "utf8");
  return text.split("\n").filter(Boolean).map((line) => JSON.parse(line) as RecordedCall);
}
