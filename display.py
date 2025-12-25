import os
import requests
from dotenv import load_dotenv

# ================= LOAD ENV =================

load_dotenv()

ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
ZOHO_REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN")
ZOHO_ACCOUNT_ID = os.getenv("ZOHO_ACCOUNT_ID")

ZOHO_ACCOUNTS_URL = "https://accounts.zoho.in"
ZOHO_MAIL_URL = "https://mail.zoho.in"

# ================= ZOHO =================

def refresh_access_token() -> str:
    url = f"{ZOHO_ACCOUNTS_URL}/oauth/v2/token"
    data = {
        "refresh_token": ZOHO_REFRESH_TOKEN,
        "client_id": ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "grant_type": "refresh_token"
    }

    r = requests.post(url, data=data, timeout=10)
    r.raise_for_status()
    return r.json()["access_token"]


def get_unread_emails(access_token: str):
    url = f"{ZOHO_MAIL_URL}/api/accounts/{ZOHO_ACCOUNT_ID}/messages/view"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"
    }
    params = {
        "status": "unread",
        "limit": 10
    }

    r = requests.get(url, headers=headers, params=params, timeout=10)
    r.raise_for_status()
    return r.json().get("data", [])


def main():
    print("Refreshing Zoho access token...")
    access_token = refresh_access_token()

    print("Fetching unread emails...")
    emails = get_unread_emails(access_token)

    if not emails:
        print("No unread emails.")
        return

    print("\nSubjects of unread emails:")
    for email in emails:
        subject = email.get("subject", "(No Subject)")
        print("-", subject)


if __name__ == "__main__":
    main()