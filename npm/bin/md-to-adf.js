#!/usr/bin/env node

const { execFileSync, spawnSync } = require("child_process");

function findPython() {
  const candidates =
    process.platform === "win32"
      ? ["py", "python3", "python"]
      : ["python3", "python"];

  for (const cmd of candidates) {
    try {
      const args = cmd === "py" ? ["-3", "--version"] : ["--version"];
      const version = execFileSync(cmd, args, { encoding: "utf-8" }).trim();
      const match = version.match(/Python (\d+)\.(\d+)/);
      if (match && (parseInt(match[1]) > 3 || (parseInt(match[1]) === 3 && parseInt(match[2]) >= 9))) {
        return { cmd, args: cmd === "py" ? ["-3"] : [] };
      }
    } catch {}
  }
  return null;
}

function checkInstalled(python) {
  try {
    execFileSync(python.cmd, [...python.args, "-m", "md_to_adf.cli.main", "--version"], { encoding: "utf-8" });
    return true;
  } catch {
    return false;
  }
}

const python = findPython();
if (!python) {
  console.error("Error: Python 3.9+ is required but not found.");
  console.error("Install Python from https://python.org");
  process.exit(1);
}

if (!checkInstalled(python)) {
  console.log("Installing md-to-adf Python package...");
  const install = spawnSync(python.cmd, [...python.args, "-m", "pip", "install", "--user", "md-to-adf"], {
    stdio: "inherit",
  });
  if (install.status !== 0) {
    console.error("Failed to install md-to-adf. Try: pip install md-to-adf");
    process.exit(1);
  }
}

const args = process.argv.slice(2);
const result = spawnSync(python.cmd, [...python.args, "-m", "md_to_adf.cli.main", ...args], {
  stdio: "inherit",
});
process.exit(result.status || 0);
