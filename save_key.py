# save_key.py
from pathlib import Path
import os, stat, getpass

SECRET_DIR = Path("secrets")
SECRET_FILE = SECRET_DIR / ".openai_api_key"

def main():
    SECRET_DIR.mkdir(parents=True, exist_ok=True)
    key = getpass.getpass("Paste your API key (input hidden): ").strip()
    if not key:
        raise SystemExit("Empty key. Aborted.")
    SECRET_FILE.write_text(key, encoding="utf-8")
    # chmod 600
    os.chmod(SECRET_FILE, stat.S_IRUSR | stat.S_IWUSR)
    print(f"[OK] Saved to {SECRET_FILE} with 600 permission. Do NOT commit this file.")

if __name__ == "__main__":
    main()
