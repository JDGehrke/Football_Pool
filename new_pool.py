
import pandas as pd
import os
import json
from dotenv import load_dotenv,dotenv_values
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# =============================================================================
# ENV VARIABLES
# =============================================================================
# 1. First, load the .env file into os.environ normally
load_dotenv()

# 2. Get a dictionary of JUST the keys defined in your .env file
env_vars = dotenv_values(".env")

# 3. Inject them into your Python global namespace
globals().update(env_vars)


# =============================================================================
# 
# =============================================================================
print("Authenticating hands-free from local dictionary...")

# 1. We call Credentials directly to build the authentication token manually
creds = Credentials.from_service_account_info(
    GOOGLE_CREDENTIALS,
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
picks = pd.DataFrame(rows)

# Reindex columns to guarantee they match the exact visual layout of your form
# (Using errors='ignore' in case a question exists but has zero submissions yet)
picks = picks.reindex(columns=ordered_columns, fill_value="")

# =============================================================================
# CLEAN AND REFORMAT
# =============================================================================
picks = picks.iloc[:,2:]
picks = picks.set_index('Select Your Name')

#Split data
tiebreaker_scores = dict(picks.iloc[:,-1])
picks = picks.iloc[:,:-1]

#CLEAN
picks.columns = picks.columns.map(lambda x : x.split(':')[0])
picks = picks.applymap(lambda x:x.split(' (')[0]).reset_index()


# Identify player column and game ID columns
name_col = picks.columns[0]  # "Select Your Name"
game_cols = picks.columns[1:]  # ["401873272", "401873275", ...]

result = []

for game_id in game_cols:
    x = {}
    for _, row in picks.iterrows():
        player_name = str(row[name_col]).strip().upper()
        pick = str(row[game_id]).strip()
        x[player_name] = pick

    result.append({"id": str(game_id).strip(), "picks": x})


# =============================================================================
# FETCHING LIVE SCORES
# =============================================================================
import pandas as pd
import requests

print("Fetching live NFL scores from ESPN...")

# Public ESPN live scoreboard endpoint for the NFL
url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"

# Pass the parameters as a dictionary to requests
params = {"dates": 2026, "week": 2, "seasontype": 1}

response = requests.get(url, params=params)
assert response.status_code == 200

data = response.json()

# Extract the current week info
week_info = data.get("week", {})
week_number = week_info.get("number", "Unknown")
print(f"🏈 Successfully loaded data for NFL Week {week_number}\n")

games_list = {}

# Loop through every game scheduled for the current week
for event in data.get("events", []):
    comp = event["competitions"][0]

    away = next(t for t in comp["competitors"] if t["homeAway"] == "away")
    home = next(t for t in comp["competitors"] if t["homeAway"] == "home")

    if comp['status']['type'].get("description") != 'Final':
        winner = None
    elif away.get("winner") == True:
        winner = away["team"].get("abbreviation")
    elif home.get("winner") == True:
        winner = home["team"].get("abbreviation")
    else:
        winner = 'TIE'

    games_list.update({event['id']: 
        {
            "id": event.get("id"),
            "name": event.get("name"),
            "label": event.get("shortName"),
            "date": event.get("date"),
            
            "away": away["team"].get("displayName"),
            "awayShort": away["team"].get("abbreviation"),
            "awayLocation": away["team"].get("location"),
            "awayMascot": away["team"].get("name"),
            "awayScore": away.get("score"),
            "awayWinner": away.get("winner"),
            
            "home": home["team"].get("displayName"),
            "homeShort": home["team"].get("abbreviation"),
            "homeLocation": home["team"].get("location"),
            "homeMascot": home["team"].get("name"),
            "homeScore": home.get("score"),
            "homeWinner": home.get("winner"),
            
            "status": comp['status']['type'].get("description"),
            "period": comp['status'].get("period"),
            "clock": comp['status'].get("displayClock"),
            "totalScore": int(away.get("score")) + int(home.get("score")),
            "winner": winner,
            }
        })
    
# =============================================================================
# FINALIZING MATCHUPS FOR JSON 
# =============================================================================
for game in result:
    gid = game['id']
    
    game.update(
        {'game': games_list[gid].get('label')
         ,'winner': games_list[gid].get('winner')
         ,'status': games_list[gid].get('status')
         
         })
    
#BUILD TIEBREAKER WITH FINAL GAME
tiebreaker_picks = {}
for p in ['JORDAN','MOM']: #players
    tiebreaker_picks.update({p: {
                                 'winner': game['picks'][p]
                                 ,'predictedTotal': tiebreaker_scores[p]
                                 }
                             })
tiebreaker = {
                'game': game.get('game')
                ,'status': game.get('status')
                ,'winner': game.get('winner')
                ,'actualTotalScore': games_list[gid].get('totalScore')
                ,'picks': tiebreaker_picks
    }
    

week_json = {'matchups':result
             ,'tiebreaker':tiebreaker}







