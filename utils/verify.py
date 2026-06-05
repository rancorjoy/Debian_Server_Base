
# Import needed libraries
import sys                      # Standard python interpreter funcionality
import re                       # Support for regular expressions
from pathlib import Path        # Manages file locations, import function 'Path'

# Function that verifies preseed file has been filled in correctly

# Scans the generated preseed file to ensure all placeholders 
# formatted as $VARIABLE$ were correctly substituted and syntax is valid.

def verify_compiled_preseed(file_path: Path) -> bool:
    print(f"[*] Starting compile verification on: {file_path}")
    
    # If the output filepath does not exist, return false (the preseed file was never saved)
    if not file_path.exists():
        print(f"[!] Verification Failed: Output target file '{file_path}' does not exist.")
        return False

    # Load the preseed file into content so it can be verified
    content = file_path.read_text()
    
    # 1. Regex Scan for Leftover Template Tokens ($VARIABLE$)
    # Uses same place_holder pattern used in main script
    placeholder_pattern = re.compile(r'\$[A-Z_][A-Z0-9_]*\$')
    leftover_placeholders = placeholder_pattern.findall(content)
    
    if leftover_placeholders:
        print("\n[!] Verification Failed: Leftover template tokens detected.")
        for token in set(leftover_placeholders):
            print(f"    -> Missing substitution matching: {token}")
        print("    Ensure these variables are fully defined in '.env'.\n")
        return False

    # 2. Structural Content Integrity Verifications
    # Ensuring critical stanzas weren't stripped or broken during file writing
    required_check_keywords = {
        "passwd/root-password-crypted": "Root Cryptographic Shadow Hash Mapping",
        "passwd/user-password-crypted": "User Cryptographic Shadow Hash Mapping",
        "preseed/late_command": "Post-Install Custom Automation Script (late_command)",
        "dns-nameservers": "Network Interfaces Template Block"
    }
    
    failures = 0
    for keyword, description in required_check_keywords.items():
        if keyword not in content:
            print(f"[!] Verification Warning: Expected foundational block missing: '{description}' ({keyword})")
            failures += 1
            
    if failures > 0:
        print("[!] File structural validation integrity checks failed.")
        return False

    print("[+] Validation Successful: Compiled file contains no raw variables.")
    return True

if __name__ == "__main__":
    # Allows validation to be invoked manually or from CLI testing chains
    target_path = Path("dist/preseed.cfg")
    success = verify_compiled_preseed(target_path)
    sys.exit(0 if success else 1)