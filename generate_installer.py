# Import needed libraries
import os                       # Standard operating system functionality
import sys                      # Standard python interpreter funcionality
from pathlib import Path        # Manages file locations, import function 'Path'
from string import Template     # Manages string functions, import 'Template' function
import shutil                   # High level file operations

# Import utility files
from utils import sanitize      # Checks that all .env entries are valid for their field type
from utils import prompt_pw     # Allows the user to enter their passwords into the terminal instead of storing them in .env
from utils import hash          # Generates hashed passwords
from utils import load_env      # Loads env file to configure generated ISO/Preseed
from utils import verify        # Verifies that produced preseed is valid
from utils import build_iso     # Builds packaged ISO file from generated preseed file and Debian version (from env)

# Class that manages env -> preseed variable passing
class CustomPreseedTemplate(Template):
    # This forces generator to only look for keys completely wrapped in $: $VARIABLE$ non $VARIABLE
    # This forces generator to only look for keys that start with A-Z, not a-z or 0-9
    delimiter = '$'
    pattern = r'\$(?P<named>[A-Z_][A-Z0-9_]*)\$'

# Main method, entry point for preseed/ISO generator
def main():
    
    # Check for Xorriso before slower operations are run
    # If Xorriso is not installed this will fail immediately
    if shutil.which("xorriso") is None:
       print("[!] xorriso not found. Install it with: sudo apt install xorriso (use WSL on Windows)")
       sys.exit(1)
    
    # Resolve absolute path locations relative to script directory execution context
    base_dir = Path(__file__).parent.resolve()
    env_file = base_dir / ".env"
    template_file = base_dir / "preseed.template.cfg"
    output_dir = base_dir / "dist"
    output_file = output_dir / "preseed.cfg"

    print("[*] Starting Debian Preseed Generation...")

    # 1. Load Target Debian settings from env file and ensure inputs are sanitized
    config = load_env.load_env_variables(env_file)
    sanitize.validate_config(config)

    # 2. Obtain and hash user and root passwords, either in .env file or entered into the terminal
    # 2a. Extract plaintext passwords (if entered) and convert passwords to hashes
    root_plain = config.get("ROOT_PASSWORD_PLAIN", "").strip()
    user_plain = config.get("USER_PASSWORD_PLAIN", "").strip()

    # 2b. Handle ROOT_PASSWORD
    # If the password is NOT in .env, prompt user for it
    if not root_plain:

        # Get and hash password
        raw_pwd = prompt_pw.prompt_password("ROOT_PASSWORD_PLAIN")
        print("[*] Hashing Root Password from terminal...")
        config["ROOT_HASH"] = hash.generate_sha512_hash(raw_pwd)

        # Clear temporary plaintext variable from memory
        del raw_pwd

    # If the password is in .env, use directly
    else:
        print("[*] Hashing Root Password from .env...")
        config["ROOT_HASH"] = hash.generate_sha512_hash(root_plain)

    # 2c. Handle USER_PASSWORD
    # If the password is NOT in .env, prompt user for it
    if not user_plain:

        # Get and hash password
        raw_pwd = prompt_pw.prompt_password("USER_PASSWORD_PLAIN")
        print("[*] Hashing User Password from terminal...")
        config["USER_HASH"] = hash.generate_sha512_hash(raw_pwd)

        # Clear temporary plaintext variable from memory
        del raw_pwd

    # If the password is in .env, use directly
    else:
        print("[*] Hashing User Password from .env...")
        config["USER_HASH"] = hash.generate_sha512_hash(user_plain)

    # 2d. Security Cleanup: Remove plain text keys from the config dictionary
    config.pop("ROOT_PASSWORD_PLAIN", None)
    config.pop("USER_PASSWORD_PLAIN", None)


    # 3. Read and map env values
    if not template_file.exists():
        print(f"[!] Error: Missing env file, cannot generate system image '{template_file}'.")
        sys.exit(1)

    template_content = template_file.read_text()
    template_pattern = CustomPreseedTemplate(template_content)
    
    try:
        # substitute throws a KeyError explicitly if a template asset item lacks a mapped .env value
        compiled_output = template_pattern.substitute(config)
    except KeyError as e:
        print(f"\n[!] Compilation Error: The template requires a variable named {e}")
        print("    but it wasn't found in the active '.env' file setup variables list.")
        sys.exit(1)

    # 4. Safely write and export localized compiled preseed config file
    output_dir.mkdir(exist_ok=True)
    output_file.write_text(compiled_output)
    print(f"[+] Compiled preseed configuration successfully saved to local workspace: {output_file}")

    # 5. Verify that the script or user did not miss any variable substitutions
    is_valid = verify.verify_compiled_preseed(output_file)
    if not is_valid:
        print("\n[!] Validation failed, check all current env variables and try again.")
        print("    Cleaning up unverified configuration artifacts...")
        if output_file.exists():
            output_file.unlink()
        sys.exit(1)
    print("[=] Preseed Generation Successful!")
    print("The Debian preseed file is prepared inside 'dist/preseed.cfg'.")

    # 6. Build a packaged ISO file that contains the preseed file
    print("\n[*] Building ISO file from preseed and .env settings")
    build_iso.build_iso()

if __name__ == "__main__":
    main()