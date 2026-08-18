#!/usr/bin/env python3
"""
Packages backend/lambda_function.py + its dependencies into backend/lambda.zip,
ready to upload to AWS Lambda (or reference from Terraform).

Usage:
    python build.py

Notes:
- Dependencies are installed with --platform/--only-binary flags so the zip
  contains Linux x86_64 wheels that match the Lambda runtime, even if you're
  building on macOS or Windows.
- Keep LAMBDA_PYTHON_VERSION in sync with the `runtime` set on the
  aws_lambda_function resource in terraform/main.tf.
"""

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
BACKEND_DIR = ROOT / "backend"
BUILD_DIR = ROOT / ".lambda-build"
ZIP_PATH = BACKEND_DIR / "lambda.zip"

LAMBDA_PYTHON_VERSION = "3.12"
LAMBDA_PLATFORM = "manylinux2014_x86_64"


def run(cmd):
    print(f"+ {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def main():
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True)

    requirements = BACKEND_DIR / "requirements.txt"
    if requirements.exists():
        run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-r",
                str(requirements),
                "--target",
                str(BUILD_DIR),
                "--platform",
                LAMBDA_PLATFORM,
                "--python-version",
                LAMBDA_PYTHON_VERSION,
                "--implementation",
                "cp",
                "--only-binary=:all:",
                "--upgrade",
            ]
        )
    else:
        print("No requirements.txt found, skipping dependency install")

    shutil.copy2(BACKEND_DIR / "lambda_function.py", BUILD_DIR / "lambda_function.py")

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in BUILD_DIR.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(BUILD_DIR))

    shutil.rmtree(BUILD_DIR)
    size_kb = ZIP_PATH.stat().st_size / 1024
    print(f"\nBuilt {ZIP_PATH.relative_to(ROOT)} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()