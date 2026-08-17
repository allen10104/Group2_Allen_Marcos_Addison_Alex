"""
build.py — Package the FastAPI backend for AWS Lambda.

Works on Windows, Mac, and Linux. On Windows, dependencies are installed as
manylinux wheels so the zip runs on Amazon Linux.

Usage (from this project folder):
    python build.py
"""

import os
import platform
import shutil
import subprocess
import sys
import zipfile

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
BUILD_DIR = os.path.join(BACKEND_DIR, "_build")
ZIP_PATH = os.path.join(BACKEND_DIR, "lambda.zip")
REQUIREMENTS = os.path.join(BACKEND_DIR, "requirements.txt")
LAMBDA_PYTHON = "3.12"


def run(cmd):
    print(f"  > {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)


def ignore_backend(_dir, names):
    skip = {"tests", "__pycache__", "_build", "lambda.zip"}
    return [name for name in names if name in skip or name.endswith(".pyc")]


def build():
    print("\n=== Step 1: Clean build folder ===")
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR)

    print("\n=== Step 2: Install Python dependencies (Linux wheels) ===")
    pip_cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "-r",
        REQUIREMENTS,
        "-t",
        BUILD_DIR,
        "-q",
        "--upgrade",
    ]
    # Windows/macOS host wheels will not import on Lambda. Force manylinux.
    if platform.system() != "Linux":
        pip_cmd.extend(
            [
                "--platform",
                "manylinux2014_x86_64",
                "--implementation",
                "cp",
                "--python-version",
                LAMBDA_PYTHON,
                "--only-binary=:all:",
            ]
        )
    run(pip_cmd)

    print("\n=== Step 3: Copy backend package and Lambda handler ===")
    shutil.copytree(
        BACKEND_DIR,
        os.path.join(BUILD_DIR, "backend"),
        ignore=ignore_backend,
        dirs_exist_ok=True,
    )
    shutil.copy(os.path.join(BACKEND_DIR, "lambda_function.py"), BUILD_DIR)

    print("\n=== Step 4: Create lambda.zip ===")
    if os.path.exists(ZIP_PATH):
        os.remove(ZIP_PATH)

    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(BUILD_DIR):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for file in files:
                if file.endswith(".pyc"):
                    continue
                full_path = os.path.join(root, file)
                archive_name = os.path.relpath(full_path, BUILD_DIR)
                zf.write(full_path, archive_name)

    size_kb = os.path.getsize(ZIP_PATH) // 1024
    print(f"\nDone! lambda.zip created ({size_kb} KB)")
    print(f"Location: {ZIP_PATH}")
    print("\nYou can now run: terraform apply")


if __name__ == "__main__":
    build()
