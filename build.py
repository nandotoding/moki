from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def run(*command: str) -> None:
    subprocess.run(command, cwd=ROOT, check=True)

if __name__ == "__main__":
    run("npm", "install", "--prefix", "frontend", "--no-audit", "--no-fund")
    run("npm", "run", "build", "--prefix", "frontend")
