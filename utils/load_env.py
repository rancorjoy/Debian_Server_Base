# Import needed libraries
import os                       # Standard operating system functionality
import sys                      # Standard python interpreter funcionality
from pathlib import Path        # Manages file locations, import function 'Path'

# Function that loads variables from env file as a dictionary
def load_env_variables(env_path: Path) -> dict:
    """Parses environment keys directly out of raw .env files while avoiding shell contamination."""

    # Define env_dict as an empty dictionary
    env_dict = {}

    # If env file is not found, tell user to create env file and exit with an error
    if not env_path.exists():
        print(f"[!] Error: Path '{env_path}' is missing.")
        print("    Please copy '.env.example' to '.env' and populate it with user secrets.")
        sys.exit(1)
    
    # Get the variables out of env (confirmed to exist)
    for line in env_path.read_text().splitlines():  # For each line in the env file...
        line = line.strip()                         # Remove all white space from ends of line and spacing (/t or /n)
        if not line or line.startswith("#"):        # If this line is a commented line...
            continue                                # Skip this line
        if "=" in line:                             # If the current line has "=", it must contain a variable...
            key, val = line.split("=", 1)           # key, val <= {a = b} split at "="
            val = val.strip().strip('"').strip("'") # Remove " and ' from val (variable)
            env_dict[key.strip()] = val             # Add variable to dictionary
    return env_dict                                 # Return the dictionary populated with user settings