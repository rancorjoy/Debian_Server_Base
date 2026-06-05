# Import needed libraries
import os                       # Standard operating system functionality
import sys                      # Standard python interpreter funcionality
from pathlib import Path        # Manages file locations, import function 'Path'
import shutil                   # Shell utilities (high level operations)
import hashlib                  # Produces secure cryptographic hashes
import urllib.request           # Allows pulling data from URLs
import subprocess               # Allows the use of mutliple processes (in parellel)

# Function that gets the checksum for a given ISO
def get_checksum(iso_filename, sums_url):
    print(f"[*] Fetching SHA256SUMS from Debian CDN...")

    # Fetch the relevant checksum from the Debian website
    with urllib.request.urlopen(sums_url) as r:
        for line in r.read().decode().splitlines():
            checksum, name = line.split()

            # If the checksum's filename matches the given ISO filename, return the checksum
            if name.strip("*") == iso_filename:
                print(f"[+] Found checksum for {iso_filename}")
                return checksum
    
    # If a matching checksum is not found, exit with an error
    print(f"[!] Could not find {iso_filename} in SHA256SUMS")
    sys.exit(1)

# Function that checks is xorriso is available on host system
# If it is not found, the user is prompted to download it and the program exits with an error
def check_xorriso():
    if shutil.which("xorriso") is None:
        print("[!] xorriso not found in PATH.")
        print("    Linux:   sudo apt install xorriso")
        print("    Windows: rerun using WSL")
        sys.exit(1)

# Function that produces a SHA-256 hash of a file (path -> str)
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        # Read in 1 MiB chunks; iter's two-arg form calls the lambda repeatedly
        # until it returns the sentinel value b"" (i.e. EOF).
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

# Function that downloads the Debian ISO defined in env and checks its checksum
def download_iso(DIST_DIR, DEBIAN_URL, DEBIAN_SHA256, ISO_CACHE):

    # If the ISO already exists...
    if ISO_CACHE.exists():
        print(f"[*] Found cached ISO at {ISO_CACHE}, verifying checksum...")

        # If the checksum matches the required checksum, this ISO can be used
        # Return before the ISO is downloaded
        if sha256_file(ISO_CACHE) == DEBIAN_SHA256:
            print("[+] Checksum OK — skipping download.")
            return
        
        # If the checksum does not match, the ISO must be deleted and redownloaded
        else:
            print("[!] Checksum mismatch on cached ISO - re-downloading.")
            ISO_CACHE.unlink()

    # If this point is reached the Debian ISO must be downloaded...
    # Ensure the directory for the downloaded ISO exists
    print(f"[*] Downloading Debian ISO from:\n    {DEBIAN_URL}")
    DIST_DIR.mkdir(exist_ok=True)

    # Function that calculates and displays download progress
    def progress(block_count, block_size, total):
        downloaded = block_count * block_size
        pct = min(downloaded / total * 100, 100) if total > 0 else 0
        mb = downloaded / (1 << 20)
        print(f"\r    {pct:5.1f}%  {mb:6.1f} MB", end="", flush=True)

    # Display a progress indicator for the download (it can take a while on slow internet)
    urllib.request.urlretrieve(DEBIAN_URL, ISO_CACHE, progress)
    print()

    # If the downloaded ISO cache DOES NOT have the expected checksum, exit with an error
    digest = sha256_file(ISO_CACHE)
    if digest != DEBIAN_SHA256:
        print(f"[!] Checksum FAILED!\n    got:      {digest}\n    expected: {DEBIAN_SHA256}")
        ISO_CACHE.unlink()
        sys.exit(1)

    # If the downloaded ISO cache does have the expected checksum, continue to next step
    print("[+] Checksum verified.")

# Function that extracts downloaded ISO into working directory
def extract_iso(ISO_WORK, ISO_CACHE):

    # Ensure a clean working directory, equivelent to rm -rf
    if ISO_WORK.exists():
        shutil.rmtree(ISO_WORK)

    # Recreate the directory (which should now be empty)
    ISO_WORK.mkdir(parents=True)

    # Use Xorriso to extract the ISO into the working directory
    # osirrox on            - allows Xorriso to run backwards and read ISO
    # -indev <ISO_CACHE>    - specifies an input file path
    # -extract / <ISO_WORK> - specifies an output file path
    print(f"[*] Extracting ISO to {ISO_WORK} ...")
    subprocess.run(
        ["xorriso", "-osirrox", "on",
         "-indev", str(ISO_CACHE),
         "-extract", "/", str(ISO_WORK)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
    )

    # xorriso extracts as read-only, use chmod to get write access
    for root, dirs, files in os.walk(ISO_WORK):
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o755)
        for f in files:
            os.chmod(os.path.join(root, f), 0o644)
    print("[+] Extracted.")

# Function that copies the preseed file into the working ISO directory
def inject_preseed(ISO_WORK, PRESEED):
    dest = ISO_WORK / "preseed.cfg"
    shutil.copy(PRESEED, dest)
    print(f"[+] Injected preseed.cfg into ISO root.")

# Function that passes preseed function through boot menu
    # Patch isolinux/txt.cfg (BIOS boot) and grub/grub.cfg (UEFI boot)
    # to auto-select the install option and pass the preseed kernel parameter.
def patch_boot_menu(ISO_WORK):

    #Inject preseed kernel parameters into the ISO's boot menu configs so
    #the installer runs fully unattended, without any manual menu interaction.

    #Handles both boot firmware types:
    #  - BIOS  -> isolinux/txt.cfg
    #  - UEFI  -> boot/grub/grub.cfg (or grub/grub.cfg on older Debian)

    # Kernel parameters that tell the Debian installer to:
    #   - load answers from the preseed file on the CD
    #   - skip confirmation prompts (auto=true, priority=critical)
    preseed_param = "file=/cdrom/preseed.cfg auto=true priority=critical"

    # BIOS: isolinux 
    txt_cfg = ISO_WORK / "isolinux" / "txt.cfg"
    if txt_cfg.exists():
        original = txt_cfg.read_text()

        # Primary pattern: append preseed params just before the quiet flag
        patched = original.replace(
            "--- quiet",
            f"preseed/file=/cdrom/preseed.cfg auto=true priority=critical --- quiet"
        )

        # Fallback: some ISOs use a bare "append" line without "--- quiet"
        if patched == original:
            patched = original.replace(
                "append ",
                f"append preseed/file=/cdrom/preseed.cfg auto=true priority=critical "
            )
        txt_cfg.write_text(patched)
        print("[+] Patched isolinux/txt.cfg (BIOS boot).")
    else:
        print("[!] isolinux/txt.cfg not found — BIOS boot won't be auto-preseed.")

    # UEFI: grub
    # Debian moved grub.cfg location between versions, so this check both paths.
    grub_cfg = ISO_WORK / "boot" / "grub" / "grub.cfg"
    if not grub_cfg.exists():
        grub_cfg = ISO_WORK / "grub" / "grub.cfg"      # some Debian versions

    if grub_cfg.exists():
        original = grub_cfg.read_text()

        # Primary pattern: same as isolinux, insert before "--- quiet"
        patched = original.replace(
            "--- quiet",
            f"file=/cdrom/preseed.cfg auto=true priority=critical --- quiet"
        )
        if patched == original:

            # Fallback: target the kernel line directly if "--- quiet" isn't present
            patched = original.replace(
                "linux   /install",
                f"linux   /install preseed/file=/cdrom/preseed.cfg auto=true priority=critical"
            )
        grub_cfg.write_text(patched)
        print("[+] Patched boot/grub/grub.cfg (UEFI boot).")
    else:
        print("[!] grub.cfg not found — UEFI boot won't be auto-preseed.")

# Function that repackages working ISO into output ISO
def repack_iso(ISO_WORK, ISO_OUT, ISO_CACHE):
    
    # If the output ISO exists, delete it
    if ISO_OUT.exists():
        ISO_OUT.unlink()

    print(f"[*] Repacking ISO to {ISO_OUT} ...")

    # Grab MBR and EFI partition from original ISO for bootability
    # Run Xorriso to create ISO using the following settings:

    # ISO Structure Settings
    # -as mkisofs                   - Run in mkisofs compatability mode
    # -r                            - Preserves Unix file system features
    # -J                            - Adds Windows readable file names (alongside -r)
    # -joliet-long                  - Allows Windows filenames to be longer (64 -> 103)
    # -iso-level 3                  - Allows files larger than 4 GB on the disk
    # -full-iso9660-filenames       - Allows much longer names in base ISO layer

    # USB/ BIOS Boot Settings
    # -isohybrid-mbr <ISO_CACHE>    - Copies mbr code from original ISO, preserves USB hybrid boot
    # -partition_offset 16          - Offset boot partition by 16 sectors (compatability increase)
    # -b isolinux/isolinux.bin      - Entry point of boot loader (El Torito)
    # -c isolinux/boot.cat          - Boot catalog (El Torito)
    # -no-emul-boot                 - Non-emulation boot (not a floppy disk)
    # -boot-load-size 4             - Load 4 x 512 byte sectors of boot image into memory
    # -boot-info-table              - Creates and locates isolinux.bin

    # UEFI Boot Settings
    # -eltorito-alt-boot            - Start second El Torito entry for UEFI Boot
    # -e boot/grub/efi.img          - Location of EFI boot image
    # -no-emul-boot                 - Non-emulation boot (not a floppy disk)
    # -isohybrid-gpt-basdat         - Add GUID Partition Table to Partition Image

    # Output Settings
    # -o <ISO_OUT>                  - Output path
    # <ISO_WORK>                    - Source directory

    subprocess.run([
        "xorriso", "-as", "mkisofs",
        "-r", "-J", "-joliet-long",
        "-iso-level", "3",
        "-full-iso9660-filenames",
        "-isohybrid-mbr", str(ISO_CACHE), 
        "-partition_offset", "16",
        "-b", "isolinux/isolinux.bin",
        "-c", "isolinux/boot.cat",
        "-no-emul-boot",
        "-boot-load-size", "4",
        "-boot-info-table",
        "-eltorito-alt-boot",
        "-e", "boot/grub/efi.img",
        "-no-emul-boot",
        "-isohybrid-gpt-basdat",
        "-o", str(ISO_OUT),
        str(ISO_WORK)
    ], check=True)

    print(f"[+] ISO written: {ISO_OUT}")
    print(f"    Size: {ISO_OUT.stat().st_size / (1 << 20):.1f} MB")

# Function that deletes working directory once the ISO is written
def cleanup_workdir(ISO_WORK):
    if ISO_WORK.exists():
        shutil.rmtree(ISO_WORK)
    print("[+] Cleaned up work directory.")