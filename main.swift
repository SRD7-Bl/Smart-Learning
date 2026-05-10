import Foundation

let pythonPath = "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3"

// 让工作目录 = main.swift 所在目录（通常也就是你放 .py 的目录）
let scriptDir = URL(fileURLWithPath: #file).deletingLastPathComponent()

// 默认跑 pytest + 你的文件（你也可以在 Scheme 里传参覆盖）
let cliArgs = Array(CommandLine.arguments.dropFirst())
let defaultArgs = ["-m", "pytest", "test_example.py", "--headed", "-q"]

let process = Process()
process.executableURL = URL(fileURLWithPath: pythonPath)
process.arguments = cliArgs.isEmpty ? defaultArgs : cliArgs
process.currentDirectoryURL = scriptDir

let pipe = Pipe()
process.standardOutput = pipe
process.standardError = pipe

do {
    try process.run()
    process.waitUntilExit()

    // 把 pytest 输出吐到 Xcode Console
    let data = pipe.fileHandleForReading.readDataToEndOfFile()
    if let text = String(data: data, encoding: .utf8), !text.isEmpty {
        print(text)
    }

    print("Python exit code:", process.terminationStatus)
} catch {
    print("Failed to run python:", error)
}

