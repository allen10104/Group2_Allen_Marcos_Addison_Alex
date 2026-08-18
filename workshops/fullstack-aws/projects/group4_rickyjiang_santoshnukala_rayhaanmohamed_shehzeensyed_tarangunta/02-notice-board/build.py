"""Package the FastAPI app into a Lambda deployment zip.

THE PROBLEM THIS SOLVES: you are on Windows. `pip install -t` downloads wheels built
for YOUR platform, so pydantic-core, pymongo and bcrypt would arrive as Windows .pyd
binaries. Lambda runs Amazon Linux. The result imports fine on your laptop and dies in
AWS with:

    Runtime.ImportModuleError: No module named 'pydantic_core._pydantic_core'

which points at pydantic and has nothing to do with pydantic. It is the single most
common Python-on-Lambda failure.

THE FIX is the --platform / --only-binary / --python-version flag set below, which
tells pip to fetch LINUX wheels for the LAMBDA Python version regardless of the machine
doing the building. The same script therefore works on Windows, macOS, and the Ubuntu
runner in GitHub Actions.
"""

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent
BACKEND = ROOT / "backend"
BUILD = BACKEND / "_build"
ZIP_PATH = BACKEND / "lambda.zip"

# Must match the Terraform `runtime` and the Lambda you deploy to.
PYTHON_VERSION = "3.13"
PLATFORM = "manylinux2014_x86_64"


def clean():
    if BUILD.exists():
        shutil.rmtree(BUILD)
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    BUILD.mkdir(parents=True)


def install_dependencies():
    print(f"Installing Linux wheels for Python {PYTHON_VERSION}...")
    subprocess.run(
        [
            sys.executable, "-m", "pip", "install",
            "-r", str(BACKEND / "requirements.txt"),
            "-t", str(BUILD),
            # Fetch wheels for the TARGET platform, not this machine.
            "--platform", PLATFORM,
            "--python-version", PYTHON_VERSION,
            "--implementation", "cp",
            # Refuse to fall back to building from source. Without this, pip would
            # silently compile a Windows binary when no matching wheel exists - which
            # is exactly the failure we are preventing. Better to fail the build here
            # with a clear message than to fail at runtime in AWS.
            "--only-binary=:all:",
            "--upgrade",
            "-q",
        ],
        check=True,
    )


def copy_application():
    """Copy the app package and the handler into the build directory.

    Lambda unzips the archive to /var/task and puts that on sys.path, so both
    `lambda_function` and `app` must sit at the ARCHIVE ROOT - not nested under
    backend/. Getting this wrong produces ModuleNotFoundError: No module named 'app'.
    """
    print("Copying application code...")
    shutil.copytree(
        BACKEND / "app",
        BUILD / "app",
        # Never ship compiled caches or tests - dead weight in every cold start.
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "tests"),
    )
    shutil.copy2(BACKEND / "lambda_function.py", BUILD / "lambda_function.py")


def make_zip():
    print("Creating lambda.zip...")
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in BUILD.rglob("*"):
            if path.is_file():
                # arcname makes paths RELATIVE to _build, so the archive has
                # lambda_function.py at its root rather than backend/_build/...
                zf.write(path, path.relative_to(BUILD))


def main():
    clean()
    install_dependencies()
    copy_application()
    make_zip()

    size_mb = ZIP_PATH.stat().st_size / (1024 * 1024)
    print(f"\nBuilt {ZIP_PATH} ({size_mb:.1f} MB)")
    # 50 MB is the hard limit for a direct upload to Lambda. Well under it means
    # Terraform can push the file straight up with no S3 staging bucket.
    if size_mb > 50:
        print("WARNING: over 50 MB - needs S3 staging, see troubleshooting")


if __name__ == "__main__":
    main()
    