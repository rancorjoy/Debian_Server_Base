# Import needed libraries
import os                       # Standard operating system functionality
import sys                      # Standard python interpreter funcionality
from pathlib import Path        # Manages file locations, import function 'Path'

# Import utility functions
from . import load_env                 # Allows env to be loaded into config
from . import build_utils              # Helper functions to build ISO file

# Downloads a Debian netinstall ISO, injects dist/preseed.cfg into it,
# patches the boot menu to load it automatically, and writes a
# flashable ISO to dist/debian-custom.iso.

# Requires: xorriso
#  Linux:   sudo apt install xorriso
#  Windows: https://www.gnu.org/software/xorriso/ (add to PATH)

# Function that builds ISO file from Preseed file
def build_iso():
    print("[*] Building Debian ISO using Generated Preseed")

    # Get relevant file paths
    BASE_DIR = Path(__file__).parent.parent.resolve()
    DIST_DIR    = BASE_DIR / "dist"
    PRESEED     = DIST_DIR / "preseed.cfg"
    ISO_CACHE   = DIST_DIR / "debian-original.iso"
    ISO_WORK    = DIST_DIR / "iso-work"
    ISO_OUT     = DIST_DIR / "debian-custom.iso"

    # Load the env file into config
    env_file = BASE_DIR / ".env"
    config = load_env.load_env_variables(env_file)

    # Get URLs to download Debian and its checksum for the version defined in env
    version = config.get("DEBIAN_VERSION", "12.10.0")
    iso_filename = f"debian-{version}-amd64-netinst.iso"
    base_url = f"https://cdimage.debian.org/cdimage/archive/{version}/amd64/iso-cd"
    ISO_URL = f"{base_url}/{iso_filename}"
    SUMS_URL = f"{base_url}/SHA256SUMS"
    DEBIAN_SHA256 = build_utils.get_checksum(iso_filename, SUMS_URL)

    # If the preseed file does not exist, something did not work previously
    # The program should abort with an error
    if not PRESEED.exists():
        print("[!] dist/preseed.cfg not found.")
        print("    Run generate_installer.py first.")
        sys.exit(1)

    # Run all compilation steps in order (from build_utils)
    build_utils.check_xorriso()                                             # Check if xorriso is installed
    build_utils.download_iso(DIST_DIR, ISO_URL, DEBIAN_SHA256, ISO_CACHE)   # Download the Debian ISO if it does not exist
    build_utils.extract_iso(ISO_WORK, ISO_CACHE)                            # Extract the Debian ISO into the working directory
    build_utils.inject_preseed(ISO_WORK, PRESEED)                           # Inject the preseed file into the working ISO
    build_utils.patch_boot_menu(ISO_WORK)                                   # Ensure preseed is run when ISO is booted
    build_utils.repack_iso(ISO_WORK, ISO_OUT, ISO_CACHE)                    # Repack the ISO into a new file
    build_utils.cleanup_workdir(ISO_WORK)                                   # Remove the working directory

    print("[=] SUCCESS: Flash dist/debian-custom.iso to your USB drive")
    print("    Linux:   sudo dd if=dist/debian-custom.iso of=/dev/sdX bs=4M status=progress")
    print("    Windows: Use a tool such as Rufus")