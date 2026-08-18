# Packages the backend into backend/lambda.zip for deployment.
#
# The tricky part: bcrypt and pymongo have compiled C components, and
# building them on a Mac produces binaries that won't run on Lambda's Linux
# runtime. Rather than using Docker to build in a real Linux environment,
# this uses pip's cross-platform wheel download: --platform + --only-binary
# tells pip "only fetch pre-built Linux wheels, never compile from source
# locally" - which works here because both bcrypt and pymongo publish
# proper manylinux wheels to PyPI. If a future dependency doesn't publish
# platform wheels, this approach would fail and Docker would become
# necessary - worth knowing as a real limitation, not a guarantee for any
# dependency.
import os
import shutil
import subprocess
import sys
import zipfile

BUILD_DIR = "_build"
ZIP_PATH = "lambda.zip"
LAMBDA_PYTHON_VERSION = "3.12"


def main() -> None:
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR)

    subprocess.run(
        [
            sys.executable, "-m", "pip", "install",
            "-r", "requirements.txt",
            "--platform", "manylinux2014_x86_64",
            "--implementation", "cp",
            "--python-version", LAMBDA_PYTHON_VERSION,
            "--only-binary=:all:",
            "--target", BUILD_DIR,
        ],
        check=True,
    )

    # ignore any stray venv/__pycache__ dirs sitting inside app/ - only the
    # actual application source should end up in the deployment package
    shutil.copytree(
        "app",
        os.path.join(BUILD_DIR, "app"),
        ignore=shutil.ignore_patterns("venv", "__pycache__"),
    )

    if os.path.exists(ZIP_PATH):
        os.remove(ZIP_PATH)

    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(BUILD_DIR):
            for file in files:
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, BUILD_DIR)
                zf.write(filepath, arcname)

    print(f"Built {ZIP_PATH}")


if __name__ == "__main__":
    main()
