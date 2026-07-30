
# Import needed libraries
import sys              # Standard python interpreter funcionality
import getpass          # Allows password entry without keystroke echo to screen

# Function that allows the user to set a password and returns the plaintext string (MUST BE DELETED AFTER USE)
# This is used when a password is not found in the .env file (which is prefered for security)
def prompt_password(var_name: str) -> str:

    # Alert the user that the password is blank and needs to be entered
    print(f"\n[*] '{var_name}' is blank in the .env file.")
    print(f"[*] Please enter a value for {var_name} (input will be hidden):")

    # Until the user enters two matching and non-empty passwords...
    while True:

        # Ask for the first password
        pwd1 = getpass.getpass(f"Enter {var_name}: ")

        # If the password is empty or only spaces, repeat the previous step
        if not pwd1.strip():
            print("[!] Password cannot be empty or space-only. Please try again.")
            continue

        # If the user entered a valid password, ask for it to be entered again
        pwd2 = getpass.getpass(f"Confirm {var_name}: ")

        # If the passwords do not match, have the user try again
        if pwd1 != pwd2:
            print("[!] Passwords do not match. Please try again.\n")
            continue

        # If the passwords do match, alert the user and return the password pwd1
        print(f"[+] '{var_name}' set.\n")
        return pwd1