
# Import needed libraries
import sys                      # Standard python interpreter funcionality
import re                       # Support for regular expressions

# Function that validates user inputted fields (in the .env file) to ensure propper characters/formatting

# Each variable has a list of whitelisted characters that can be accepted for that field
# This list is checked against the entry in the .env file to ensure no illagal characters were entered
# The dictionary FIELD_WL (Field White List) has an entry for each .env variable
FIELD_WL = {
    # Disk and ethernet .env entries
    "INSTALL_DISK":   r'^/dev/[a-zA-Z0-9/_-]+$',
    "NET_IFACE":      r'^[a-zA-Z0-9]+$',
    #
    # User settings and timezone
    "HOSTNAME":       r'^[a-zA-Z0-9-]+$',
    "TIMEZONE":       r'^[A-Za-z0-9_-]+(/[A-Za-z0-9_-]+)*$',
    "USER_NAME":      r'^[a-z_][a-z0-9_-]{0,31}$',
    "USER_FULLNAME":  r"^[a-zA-Z0-9 .'-]+$",
    #
    # SSH settings
    # Limit SSH ports to a 1-5 digit number, valid range (1-65535) enforced in function below
    "SSH_PORT":       r'^\d{1,5}$',
    #"PUBLIC_KEY":     r'^(ssh-(ed25519|rsa)|ecdsa-[\w-]+) [A-Za-z0-9+/=]+( \S+)?$',
    #
    # Network configuration settings
    # Strictly matches 0.0.0.0 through 255.255.255.255
    "STATIC_IP":      r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',
    "NETMASK":        r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',
    "GATEWAY":        r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',
    "DNS_SERVERS":    r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',
    #
    # Debian Version for install
    "DEBIAN_VERSION": r'^\d+(\.\d+)*$',
}

# Helper Function that prints error and exits program when syntax/character error is detected
def fail(key: str, value: str):
    print(f"[!] Validation Failed: '{key}' = '{value}' doesn't match the expected format.")
    sys.exit(1)

# Function that validates all entries in the config dictionary (from .env)
def validate_config(config: dict) -> None:

    # For all key, pattern pairs in the whitelist (above)
    for key, pattern in FIELD_WL.items():

        # Find the associated value in the .env file (user input for that field)
        # Results in an empty string if no value is found, removes leading and trailing spaces
        value = config.get(key, "").strip()

        # Fail if the required key is completely missing or empty
        if not value:
            fail(key, "<EMPTY>")

        # Enforce SSH port range (1-65535)
        if key == "SSH_PORT":
            if not re.fullmatch(pattern, value) or not (1 <= int(value) <= 65535):
                fail(key, value)
            continue

        # Special handling for DNS_SERVERS (space separated list)
        if key == "DNS_SERVERS":

            # Find all space separated entries in the list
            entries = value.split()

            # If the list is empty (no DNS servers were listed)
            # -> Tell the user the list is empty and fail
            if not entries:
                fail(key, "<EMPTY>")

            # If any entry does not match the pattern in the white list, fail
            for entry in entries:
                if not re.fullmatch(pattern, entry):
                    fail(key, value)
        
        # Standard validation for all other items
        # If they do not match their patter, fail
        else:
            if not re.fullmatch(pattern, value):
                fail(key, value)

    # If no failures occur, all values are correct and the program can proceed
    print("[+] Entries in .env Validated")