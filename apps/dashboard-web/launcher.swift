// launcher.swift — Minimal process launcher for launchd agents.
// Compile: swiftc -O launcher.swift -o sk-dashboard-launcher
// Grant Full Disk Access to the output binary in System Settings.
import Foundation

// Usage: sk-dashboard-launcher <script-path>
guard CommandLine.arguments.count >= 2 else {
    fputs("Usage: sk-dashboard-launcher <script-path>\n", stderr)
    exit(1)
}

let script = CommandLine.arguments[1]
let process = Process()
process.executableURL = URL(fileURLWithPath: "/bin/bash")
process.arguments = [script]
process.environment = ProcessInfo.processInfo.environment

do {
    try process.run()
    process.waitUntilExit()
    exit(process.terminationStatus)
} catch {
    fputs("Failed to launch: \(error)\n", stderr)
    exit(1)
}
