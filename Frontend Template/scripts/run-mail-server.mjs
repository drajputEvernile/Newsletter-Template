// Starts the email server (port 1002) with the venv Python, installing deps first if needed.
import { spawn, spawnSync } from "node:child_process";
import { existsSync } from "node:fs";

const venvPy = process.platform === "win32" ? "server/.venv/Scripts/python.exe" : "server/.venv/bin/python";
if (!existsSync(venvPy)) {
  const r = spawnSync("node", ["scripts/setup-mail-server.mjs"], { stdio: "inherit" });
  if (r.status !== 0) process.exit(r.status ?? 1);
}
const child = spawn(venvPy, ["server/main.py"], { stdio: "inherit" });
child.on("exit", (code) => process.exit(code ?? 0));
