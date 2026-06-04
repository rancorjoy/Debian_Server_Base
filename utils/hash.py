# Import needed libraries
import os                       # Standard operating system functionality
import sys                      # Standard python interpreter funcionality

# Which cryptography library is imported depends on the curret OS...
# On Windows try importing Crypt, on Linux/Unix try importing sha512_crypt

# Try importing crypt...
try:
    import crypt                # Import crypt
    HAS_NATIVE_CRYPT = True     # If this worked, HAS_NATIVE_CRYPT = true, continue...

# If crypt cannot be imported it is either not installed yet or not available
except ImportError:             # In the case of an import error...
    HAS_NATIVE_CRYPT = False    # This did not work, HAS_NATIVE_CRYPT = false... try Linux installation
    
    # Since crypt cannot be installed, try installing sha512_crypt...
    # If this works continue running using Unix/Linux functions
    try:
        from passlib.hash import sha512_crypt

    # If this fails, the machine being used in a Windows machine and crypt needs to be installed
    # Print installation instructions and exit with an error
    except ImportError:
        print("[!] Cross-Platform Warning: You are running this on a non-Linux machine.")
        print("    To compile secure SHA-512 server password hashes here, please run:")
        print("    `pip install passlib` or `python3 -m pip install passlib`")
        print("    `rerun this program after installing passlib`")
        sys.exit(1)

# Function to generate password hash
# Generates an OS-compliant secure SHA-512 password crypt hash string
def generate_sha512_hash(plaintext_password: str) -> str:

    # Windows native solution
    if HAS_NATIVE_CRYPT:
        # Native Linux crypt compilation using a random generated OS salt signature
        return crypt.crypt(plaintext_password, crypt.mksalt(crypt.METHOD_SHA512))
    
    # Linux/Unix native solution
    else:
        # Number of hashing rounds must be defined (5000)
        return sha512_crypt.using(rounds=5000).hash(plaintext_password)