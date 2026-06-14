#!/usr/bin/env python3
"""Pre-flight platform compatibility checker."""
import sys
import platform
import shutil

def check(label: str, ok: bool, fix: str = ""):
    status = "✅" if ok else "❌"
    print(f"{status} {label}")
    if not ok and fix:
        print(f"   Fix: {fix}")
    return ok

passed = True
passed &= check(f"Python 3.12+ ({sys.version_info.major}.{sys.version_info.minor})",
                sys.version_info >= (3, 12),
                "Install Python 3.12: pyenv install 3.12")
passed &= check("Not native Windows",
                sys.platform != "win32",
                "Run in WSL2: scripts/setup-wsl2.ps1")
passed &= check("Podman or Docker available",
                bool(shutil.which("podman") or shutil.which("docker")),
                "Install Podman: https://podman.io/getting-started/installation")
passed &= check("cloudflared available (optional)",
                bool(shutil.which("cloudflared")),
                "Install: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/")

print()
if passed:
    print("✅ Platform verification passed — ready to build.")
else:
    print("❌ Some checks failed. Fix the above before running `make dev-up`.")
    sys.exit(1)
