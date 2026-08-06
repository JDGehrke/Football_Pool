# #OAUTH CREDENTIALS
# CLIENT_ID = '985194480544-erqkndbi8cl2n374ehsaq357tlmmatbc.apps.googleusercontent.com'
# CLIENT_SECRET = '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'

FORM_ID = '19k6S5kZaubLzZclV8enzQuz0Iv7JVK8Fn6GtiIWnqnY'

#SERVICE ACCOUNT CREDENTIALS
MY_CREDENTIALS = {
  "type": "service_account",
  "project_id": "football-pool-501500",
  "private_key_id": "2c121b141cfe673e35bf629036af9190eccbe99e",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCqTbvLIFPRfnjR\nJYnU+69z3HyxcWeOWZgRq/2AxVNWcikcLHcPc9ON8X/HAl8+dygOtoAkWsuOspao\nnCFaODlxYDOqVC4I5MsGNigw+jSoFpFBqiEQk/vg0gAFXEwRscSjX2z/EnOP3e+0\n0mn9bycV8PWUBnfR3bQMmwgTLENfQryw7qKNp4N0S1uqufswQf11oVQ/GER9VzIi\nOlgFBkgXpD0DsGqD0M0Kf/Jd+dtfiYUJw4vgbBro9Oph7z+XJyicP+JNQCrnd4TZ\n+gHunNg7KPkIPss6cdlKi4W4OEzX6h2LsMGPh14YRBG4VLzUf8z6C7SeigJTWBRb\nJIz8S4TBAgMBAAECggEAAfE113zJz+1ovH6N2ka44HH5ib7bbubBLU8VlUrK0Zp8\nMwojx81AR/xi2BbEFiQ0P1S1VJTPgP6y6VSHLIOlzg/05Df7uBYUkFXSSAVhJTCa\nsqcZeO+tyJ7Z1Asn1+97017S0VGOeAEl4HKiNaXMn5CvsE2RlMG58bHb70y1g6gs\nVx7BJkHsWjXU/466zm020A1PHTu3WISOvQKghwAYzapjchnwgoNm3kb98daYnanc\nOH8HANeLDTbI8jNYSOcKXE5mdtSf64n0xQ/UXu9JxJPw6S7Oqhrodp73SclZWFC+\n16lPOZjnfAgIFvjV2BCiq/iIpJB10l0N+IXB2x3JUQKBgQDXJ3MJNMocuF3VJYKB\n/BRhf9YbxTtMfrJuQ3jZ204gOX6SeGYG4sP6DZ79eamHjv0H6CSHKvOVThkaFR4H\nvaGxEcEJPK3cKU19mNlVEfVaEagRETjrL7CDjMh7WyEBh7QdH+MMJIt2DOoRaQUa\nRit7esQO5n6+noqLSxStfsnhKQKBgQDKoooXjyDWt/uceqKG4RyZ9OVWX9VKzX9f\nO9KiVw9OkUXaVAOX9tKjM/UA0uOCc0AtNCVl2yjsjmJlIIE/EmjrctRwzfq3fu1i\nKC0ADyYnPPvX95N/4gdFD/XvTeNF1XmCH22dlo2W1W3Ethc2Peclly92E3WusBQf\nDp0k68aB2QKBgBt35uDjA3a9NwWSX2IW+8ci2gP7n0F532/iX1h4/jVxAa7Tfjsc\n0mZnPMghszoiUD2lLpyvKCAEs4G39niIhk8j9CAoxg2YnFMPo5ePzmIsZOeg6kJk\neUWiQKo3DTSzzZP2UTdopwFwTqXgYY1kLgL6vnMkjEPr28ZC1KX9zOpZAoGBAIJx\nF4wK6wzN6v7UQwOorgy9hVSQ5HD+0Fux2un+OTBOfDULmDSfAwFkVPduyl4TauCu\njNSAvFtrXRPUVN8RLtFCXlcvgZHV92IUksNS/TCNJWHlUeIk0qE2oQ6niQJPZaTK\nLnofjI3oXn0e6tpUBxQ/uqG77SnC13EWqzo1PNghAoGAGBZ0q7ugqi+nUE2R1THH\no/fA8GW6whB2R4BH1wtQUfUn+BkodGmx7LgDZh+R3Yxkui8DyyDre2nSshasgCQE\nQsSJY7C1d7JuwvXi7R/yzKBY3Q5V99vbU7dZZQtmWaN139UWHCYNV5rxNkEdps8f\nn3Sa21ouYFDDWBvXw+QA8Oo=\n-----END PRIVATE KEY-----\n",
  "client_email": "python-google-service-account@football-pool-501500.iam.gserviceaccount.com",
  "client_id": "112226814251799453970",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/python-google-service-account%40football-pool-501500.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


print("Authenticating hands-free from local dictionary...")

# 1. We call Credentials directly to build the authentication token manually
creds = Credentials.from_service_account_info(
    MY_CREDENTIALS,
    scopes=[
            "https://www.googleapis.com/auth/forms.responses.readonly",
            "https://www.googleapis.com/auth/forms.body.readonly"
        ]
)

# 2. Connect to the Google Forms API engine
service = build("forms", "v1", credentials=creds)

# 1. FETCH THE FORM STRUCTURE (To get real question names and their order)
print("Fetching form structure for column names...")
form_structure = service.forms().get(formId=FORM_ID).execute()

# Build a mapping dictionary and keep track of the precise question order
question_map = {}
ordered_columns = ["Response_ID", "Timestamp"]

for item in form_structure.get("items", []):
    # Only process items that are actual questions (ignoring text descriptions or images)
    if "questionItem" in item:
        q_id = item["questionItem"]["question"]["questionId"]
        title = item["title"]
        question_map[q_id] = title
        ordered_columns.append(title)

# 2. FETCH THE FORM RESPONSES
print("Fetching form responses...")
result = service.forms().responses().list(formId=FORM_ID).execute()

# 3. PARSE RESPONSES USING THE NEW MAP
rows = []
for response in result.get("responses", []):
    row_data = {
        "Response_ID": response["responseId"],
        "Timestamp": response["lastSubmittedTime"],
    }
    for q_id, answer_obj in response.get("answers", {}).items():
        answers = [
            a.get("value", "")
            for a in answer_obj.get("textAnswers", {}).get("answers", [])
        ]
        # Convert the cryptic Question ID into the human-readable Question Title
        clean_column_name = question_map.get(q_id, q_id)
        row_data[clean_column_name] = ", ".join(answers)
    rows.append(row_data)

# 4. CREATE DATAFRAME & FORCE THE CORRECT ORDER
df = pd.DataFrame(rows)

# Reindex columns to guarantee they match the exact visual layout of your form
# (Using errors='ignore' in case a question exists but has zero submissions yet)
df = df.reindex(columns=ordered_columns, fill_value="")




# =============================================================================
# 
# =============================================================================
import pandas as pd
import requests

print("Fetching live NFL scores from ESPN...")

# Public ESPN live scoreboard endpoint for the NFL
url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"

# Pass the parameters as a dictionary to requests
params = {"dates": 2025, "week": 5, "seasontype": 3}

response = requests.get(url, params=params)
assert response.status_code == 200

data = response.json()

# Extract the current week info
week_info = data.get("week", {})
week_number = week_info.get("number", "Unknown")
print(f"🏈 Successfully loaded data for NFL Week {week_number}\n")

games_list = []

# Loop through every game scheduled for the current week
for event in data.get("events", []):
    game_name = event.get("name")
    status = event.get("status", {}).get("type", {}).get("description")

    # ESPN splits teams into a list: usually [home_team, away_team]
    competitors = event.get("competitions", [{}])[0].get("competitors", [])

    home_team = "Unknown"
    home_score = "0"
    away_team = "Unknown"
    away_score = "0"

    for team in competitors:
        team_name = team.get("team", {}).get("displayName")
        score = team.get("score", "0")

        if team.get("homeAway") == "home":
            home_team = team_name
            home_score = score
        else:
            away_team = team_name
            away_score = score

    # Create a clean layout for the DataFrame row
    games_list.append(
        {
            "Game": game_name,
            "Away Team": away_team,
            "Away Score": away_score,
            "Home Team": home_team,
            "Home Score": home_score,
            "Status": status,  # e.g., "Scheduled", "In Progress", or "Final"
        }
    )

# Convert into a structured DataFrame
df = pd.DataFrame(games_list)



