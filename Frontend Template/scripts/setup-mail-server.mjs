// Creates server/.venv and installs the email server's Python dependencies.
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";

const py = process.platform === "win32" ? "python" : "python3";
const venvPy = process.platform === "win32" ? "server/.venv/Scripts/python.exe" : "server/.venv/bin/python";
const run = (cmd, args) => {
  const r = spawnSync(cmd, args, { stdio: "inherit" });
  if (r.status !== 0) process.exit(r.status ?? 1);
};
if (!existsSync(venvPy)) run(py, ["-m", "venv", "server/.venv"]);
run(venvPy, ["-m", "pip", "install", "-q", "-r", "server/requirements.txt"]);
console.log("Email server dependencies installed.");
