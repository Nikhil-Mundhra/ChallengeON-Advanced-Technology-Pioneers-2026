#!/usr/bin/env python3
"""Build DATA_ISSUES.pdf from DATA_ISSUES.md using the document-manipulation toolchain."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MD_PATH = ROOT / "DATA_ISSUES.md"
PDF_PATH = ROOT / "DATA_ISSUES.pdf"
TOOL_SCRIPT = Path.home() / ".gemini" / "config" / "skills" / "document-manipulation" / "scripts" / "md_to_pdf.py"


def main():
    if not MD_PATH.exists():
        print(f"Error: {MD_PATH} not found.")
        sys.exit(1)

    if TOOL_SCRIPT.exists():
        # Prefer system python3 which has markdown and playwright installed
        py_cmd = "python3"
        cmd = [py_cmd, str(TOOL_SCRIPT), "--input", str(MD_PATH), "--output", str(PDF_PATH)]
        print(f"Compiling {MD_PATH.name} -> {PDF_PATH.name} via md_to_pdf...")
        res = subprocess.run(cmd)
        if res.returncode == 0:
            print(f"Successfully generated {PDF_PATH} ({PDF_PATH.stat().st_size:,} bytes).")
            return
        print("Fallback to direct execution...")

    print("Error: Could not find or execute md_to_pdf compiler.")
    sys.exit(1)


if __name__ == "__main__":
    main()
