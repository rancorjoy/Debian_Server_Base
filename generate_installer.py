import os
import sys
from pathlib import Path
from string import Template

# Import verification function
from utils import hash
from utils import load_env
from utils import verify

class CustomPreseedTemplate(Template):
    # This forces generator to only look for keys completely wrapped in $: $VARIABLE$ non $VARIABLE
    # This forces generator to only look for keys that start with A-Z, not a-z or 0-9
    delimiter = '$'
    pattern = r'\$(?P<named>[A-Z_][A-Z0-9_]*)\$'

def main():
    # Resolve absolute path locations relative to script directory execution context
    base_dir = Path(__file__).parent.resolve()
    env_file = base_dir / ".env"
    template_file = base_dir / "preseed.template.cfg"
    output_dir = base_dir / "dist"
    output_file = output_dir / "preseed.cfg"

    print("=====================================================================")
    print("[*] Launching Debian Base System Preseed Generator")
    print("=====================================================================")

    # 1. Load Local Machine Node Settings Environment
    config = load_env.load_env_variables(env_file)

    # 2. Extract Plaintext Targets and Convert to Shadow Password Hashes
    if "ROOT_PASSWORD_PLAIN" not in config or "USER_PASSWORD_PLAIN" not in config:
        print("[!] Compilation Aborted: Missing required root or user plaintext passwords in '.env'.")
        sys.exit(1)

    print("[*] Processing raw string configurations into secure shadow hashes...")
    config["ROOT_HASH"] = hash.generate_sha512_hash(config["ROOT_PASSWORD_PLAIN"])
    config["USER_HASH"] = hash.generate_sha512_hash(config["USER_PASSWORD_PLAIN"])

    # 3. Read and Map Blueprint Template Values
    if not template_file.exists():
        print(f"[!] Error: Missing source asset architecture template '{template_file}'.")
        sys.exit(1)

    template_content = template_file.read_text()
    template_pattern = CustomPreseedTemplate(template_content)
    
    try:
        # substitute throws a KeyError explicitly if a template asset item lacks a mapped .env value
        compiled_output = template_pattern.substitute(config)
    except KeyError as e:
        print(f"\n[!] Compilation Error: The template requires a variable named {e}")
        print("    but it wasn't found in your active '.env' file setup variables list.")
        sys.exit(1)

    # 4. Safely Write and Export Localized Compiled Preseed Config File
    output_dir.mkdir(exist_ok=True)
    output_file.write_text(compiled_output)
    print(f"[+] Compiled preseed configuration successfully saved to local workspace: {output_file}")

    # 5. Hand Execution Context off to Validation Audit Checks Script
    is_valid = verify.verify_compiled_preseed(output_file)
    if not is_valid:
        print("\n[!] RUNTIME HALT: Validation verification checks dropped a flag.")
        print("    Cleaning up unverified configuration artifacts...")
        if output_file.exists():
            output_file.unlink()
        sys.exit(1)

    print("\n=====================================================================")
    print("[=] PRESEED GENERATION SUCCESSFUL [=]")
    print("=====================================================================")
    print("The Debian server preseed file is prepared inside 'dist/preseed.cfg'.")

if __name__ == "__main__":
    main()