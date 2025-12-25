import requests

# ================= CONFIGURATION =================
# Use the same credentials you used before
CLIENT_ID = "1000.X8QFPJNB2WIW9G0SMN9JWTHJ9G795K"
CLIENT_SECRET = "59accf3361bfbd7a19bb84ee9b9cb0a221d7b9e334"
REFRESH_TOKEN = "1000.8f65edce81b2d97785e6a2fa048a47db.2e16a0811a8dab5f893554f4c556dedc" 
# =================================================

def get_access_token():
    # 1. Get a fresh Access Token first
    url = "https://accounts.zoho.in/oauth/v2/token" # Note: .in for India
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
    # Note: .in for India
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