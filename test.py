import requests

# CONFIGURATION
client_id = "1000.X8QFPJNB2WIW9G0SMN9JWTHJ9G795K"
client_secret = "59accf3361bfbd7a19bb84ee9b9cb0a221d7b9e334"
auth_code = "1000.3a765c9326606083e90201c50f9f2791.c6d4c8887192366ac639885db0bc3019"
redirect_uri = "http://localhost:8000/callback"

# URL to get tokens
token_url = "https://accounts.zoho.in/oauth/v2/token"

data = {
    "grant_type": "authorization_code",
    "client_id": client_id,
    "client_secret": client_secret,
    "redirect_uri": redirect_uri,
    "code": auth_code
}

response = requests.post(token_url, data=data)
tokens = response.json()

if "access_token" in tokens:
    print("SUCCESS!")
    print(f"Access Token: {tokens['access_token']}")
    print(f"Refresh Token: {tokens['refresh_token']}") 
    # SAVE THE REFRESH TOKEN! It is the only way to get new access tokens later.
else:
    print("Error:", tokens)