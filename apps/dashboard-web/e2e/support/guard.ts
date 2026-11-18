import path from "node:path";

export function assertSafeServers(webPort: number, apiPort: number, apiHome: string, realHome: string): void {
  if (webPort === 3000 || apiPort === 8000) {
    throw new Error("E2E 不可使用正式服務的 3000 或 8000 埠。");
  }
  if (path.resolve(apiHome) === path.resolve(realHome)) {
    throw new Error("E2E API 的 HOME 不可指向真實家目錄。");
  }
}
