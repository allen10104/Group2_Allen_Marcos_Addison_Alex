"""
Builds backend/lambda.zip: installs requirements for the Lambda's
target platform (manylinux x86_64 / Python 3.12) and bundles them
with lambda_function.py.

Run with: python build.py
"""

import os
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = os.path.join(ROOT, "_build")
ZIP_PATH = os.path.join(ROOT, "lambda.zip")


def main():
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR)

    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            os.path.join(ROOT, "requirements.txt"),
            "--target",
            BUILD_DIR,
            "--platform",
            "manylinux2014_x86_64",
            "--implementation",
            "cp",
            "--python-version",
            "3.12",
            "--only-binary=:all:",
            "--upgrade",
        ]
    )

    shutil.copy(os.path.join(ROOT, "app.py"), BUILD_DIR)

    if os.path.exists(ZIP_PATH):
        os.remove(ZIP_PATH)

    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(BUILD_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, BUILD_DIR)
                zf.write(file_path, arcname)

    print(f"Built {ZIP_PATH}")


if __name__ == "__main__":
    main()
