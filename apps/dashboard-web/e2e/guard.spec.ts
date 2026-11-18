import os from "node:os";
import path from "node:path";
import { test, expect } from "@playwright/test";
import { assertSafeServers } from "./support/guard";

test("正式埠與真實 HOME 會被拒絕", () => {
  const realHome = os.userInfo().homedir;
  const fakeHome = path.join(realHome, "fixture-home");
  expect(() => assertSafeServers(3000, 8005, fakeHome, realHome)).toThrow();
  expect(() => assertSafeServers(3005, 8000, fakeHome, realHome)).toThrow();
  expect(() => assertSafeServers(3005, 8005, realHome, realHome)).toThrow();
  expect(() => assertSafeServers(3005, 8005, fakeHome, realHome)).not.toThrow();
});
