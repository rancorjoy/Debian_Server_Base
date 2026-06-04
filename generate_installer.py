# Import needed libraries
import os                       # Standard operating system functionality
import sys                      # Standard python interpreter funcionality
from pathlib import Path        # Manages file locations, import function 'Path'
from string import Template     # Manages string functions, import 'Template' function

# Import utility files
from utils import hash          # Generates hashed passwords
from utils import load_env      # Loads env file to configure generated ISO/Preseed
from utils import verify        # Verifies that produced preseed is valid
#from utils import build_iso     # Builds packaged ISO file from generated preseed file and Debian version (from env)

# Class that manages env -> preseed variable passing
class CustomPreseedTemplate(Template):
    # This forces generator to only look for keys completely wrapped in $: $VARIABLE$ non $VARIABLE
    # This forces generator to only look for keys that start with A-Z, not a-z or 0-9
    delimiter = '$'
    pattern = r'\$(?P<named>[A-Z_][A-Z0-9_]*)\$'

# Main method, entry point for preseed/ISO generator
def main():
    # Resolve absolute path locations relative to script directory execution context
    base_dir = Path(__file__).parent.resolve()
    env_file = base_dir / ".env"
    template_file = base_dir / "preseed.template.cfg"
    output_dir = base_dir / "dist"
    output_file = output_dir / "preseed.cfg"

    print("[*] Starting Debian Preseed Generation...")

    # 1. Load Target Debian settings from env file
    config = load_env.load_env_variables(env_file)

    # 2. Extract plaintext targets and convert passwords to hashes
    if "ROOT_PASSWORD_PLAIN" not in config or "USER_PASSWORD_PLAIN" not in config:
        print("[!] Compilation Aborted: Missing required root or user plaintext passwords in '.env'.")
        sys.exit(1)

    print("[*] Hashing Passwords...")
    config["ROOT_HASH"] = hash.generate_sha512_hash(config["ROOT_PASSWORD_PLAIN"])
    config["USER_HASH"] = hash.generate_sha512_hash(config["USER_PASSWORD_PLAIN"])

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
    #print("\n[*] Building ISO file from preseed and .env settings")
    #build_iso.main()

if __name__ == "__main__":
    main()