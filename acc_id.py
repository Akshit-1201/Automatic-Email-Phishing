import requests
import os
from dotenv import load_dotenv

load_dotenv()


# ================= CONFIGURATION =================
CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN") 
# =================================================

def get_access_token():
    # 1. Get a fresh Access Token first
    url = "https://accounts.zoho.in/oauth/v2/token"
    params = {
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token"
    }
    resp = requests.post(url, params=params)
    return resp.json().get("access_token")

def find_account_id():
    token = get_access_token()
    if not token:
        print("Error: Could not generate Access Token. Check credentials.")
        return

    # 2. Ask Zoho for Account Details
    api_url = "https://mail.zoho.in/api/accounts"
    
    headers = {
        "Authorization": f"Zoho-oauthtoken {token}"
    }

    response = requests.get(api_url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        # Print the list of accounts found
        print("\n--- YOUR ZOHO ACCOUNTS ---")
        for account in data.get("data", []):
            print(f"Email:      {account.get('incomingUserName')}")
            print(f"Account ID: {account.get('accountId')}  <-- COPY THIS NUMBER")
            print("--------------------------")
    else:
        print("Error fetching accounts:", response.text)

if __name__ == "__main__":
    find_account_id()