import os
import sys
from pathlib import Path

def load_env_variables(env_path: Path) -> dict:
    """Parses environment keys directly out of raw .env files while avoiding shell contamination."""
    env_dict = {}
    if not env_path.exists():
        print(f"[!] Error: Active runtime config target '{env_path}' missing.")
        print("    Please copy '.env.example' to '.env' and populate your local host configurations.")
        sys.exit(1)
        
    for line in env_path.read_text().splitlines():
        line = line.strip()
        # Bypass comments and empty padding lines
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, val = line.split("=", 1)
            # Safe strip potential variable padding symbols or outer quoting wrappers
            val = val.strip().strip('"').strip("'")
            env_dict[key.strip()] = val
    return env_dict