# =============================================================================
# FOOTBALL POOL
# =============================================================================
import pandas as pd
import json
import datetime as dt
import requests
import os
from dotenv import load_dotenv,dotenv_values
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

os.chdir(r'C:\\Users\\jdgeh\Documents\Github\Football_Pool')

# =============================================================================
# PROGRAM VARIABLES
# =============================================================================
season = 2026
current_week = 1

players = ['AUSTIN','BRANDON','JORDAN','MOM']

TEAM_MAP = {
    # Mascot / Short Name Mappings
    "Cardinals": "ARI",
    "Falcons": "ATL",
    "Ravens": "BAL",
    "Bills": "BUF",
    "Panthers": "CAR",
    "Bears": "CHI",
    "Bengals": "CIN",
    "Browns": "CLE",
    "Cowboys": "DAL",
    "Broncos": "DEN",
    "Lions": "DET",
    "Packers": "GB",
    "Texans": "HOU",
    "Colts": "IND",
    "Jaguars": "JAX",
    "Chiefs": "KC",
    "Raiders": "LV",
    "Chargers": "LAC",
    "Rams": "LAR",
    "Dolphins": "MIA",
    "Vikings": "MIN",
    "Patriots": "NE",
    "Saints": "NO",
    "Giants": "NYG",
    "Jets": "NYJ",
    "Eagles": "PHI",
    "Steelers": "PIT",
    "49ers": "SF",
    "Seahawks": "SEA",
    "Buccaneers": "TB",
    "Titans": "TEN",
    "Commanders": "WAS"
}

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
# READ IN CURRENT JSON FILE
# =============================================================================
with open("data.json", "r", encoding="utf-8") as file:
    current_json = json.load(file)
    
if f'Week {current_week}' not in current_json['weeks'].keys():
    new_week = True
    current_json['metadata']['currentWeek'] = f'Week {current_week}'
else:
    new_week = False

# =============================================================================
# DOWNLOAD PICKS FROM GOOGLE SHEETS
# =============================================================================
print("Authenticating hands-free from local dictionary...")

# 1. We call Credentials directly to build the authentication token manually
creds = Credentials.from_service_account_info(
    json.loads(os.getenv("GOOGLE_CREDENTIALS")),
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

if new_week == True:
    picks.to_csv(f'{season}\Week {current_week}.csv',index=False)
else:
    picks = pd.read_csv(f'{season}\Week {current_week}.csv')

# =============================================================================
# CLEAN AND REFORMAT
# =============================================================================
#Reset Index
picks = picks.iloc[:,2:]
picks = picks.set_index('Select Your Name')

#Split data
tiebreaker_scores = dict(picks.iloc[:,-1])
picks = picks.iloc[:,:-1]

#Clean Data
picks.columns = picks.columns.map(lambda x : x.split(':')[0]) #rename columns with just game id
picks = picks.applymap(lambda x:x.split(' (')[0]) #remove records
picks = picks.replace(TEAM_MAP)

# Identify player column and game ID columns
picks = picks.reset_index()
name_col = picks.columns[0]  # "Select Your Name"
game_cols = picks.columns[1:]  # ["401873272", "401873275", ...]

picks_by_game = []

for game_id in game_cols:
    x = {}
    for _, row in picks.iterrows():
        player_name = str(row[name_col]).strip().upper()
        pick = str(row[game_id]).strip()
        x[player_name] = pick

    picks_by_game.append({"id": str(game_id).strip(), "picks": x})


# =============================================================================
# FETCHING LIVE SCORES
# =============================================================================
print("Fetching live NFL scores from ESPN...")

# Public ESPN live scoreboard endpoint for the NFL
url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"

# Pass the parameters as a dictionary to requests
params = {"dates": season, "week": current_week, "seasontype": 1}

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
for game in picks_by_game:
    gid = game['id']
    
    game.update(
        {'game': games_list[gid].get('label')
         ,'winner': games_list[gid].get('winner')
         ,'status': games_list[gid].get('status')
         
         })
    
#BUILD TIEBREAKER WITH FINAL GAME
tiebreaker_picks = {}
for p in players: 
    tiebreaker_picks.update({p: {
                                 'winner': game['picks'][p]
                                 ,'predictedTotal': int(tiebreaker_scores[p])
                                 }
                             })
tiebreaker = {
                'game': game.get('game')
                ,'status': game.get('status')
                ,'winner': game.get('winner')
                ,'actualTotalScore': games_list[gid].get('totalScore')
                ,'picks': tiebreaker_picks
    }
    

week_json = {'matchups':picks_by_game
             ,'tiebreaker':tiebreaker}

# =============================================================================
# UPDATE JSON
# =============================================================================
#Set Week's Json into final
current_json['weeks'][f'Week {current_week}'] = week_json
    
#Set final update time
# 1. Get current local time with timezone information
now = dt.datetime.now().astimezone()

# 2. Format individual parts
day = now.strftime("%A")  # Full weekday ("Sunday")
hour = str(int(now.strftime("%I")))  # 12-hour format without leading zero ("4")
minute = now.strftime("%M")  # Minute with leading zero ("16")
ampm = now.strftime("%p").lower()  # am/pm in lowercase ("pm")
# tz = now.strftime("%Z")  # Timezone name ("CST" / "CDT")

# 3. Build formatted timestamp
timestamp = f"{day} @ {hour}:{minute}{ampm}"
current_json['metadata']['lastUpdated'] = timestamp
    

# Overwrite local data.json
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(current_json, f, indent=2)

print("Saved updates to data.json!")

# # =============================================================================
# # PUSH TO GITHUB
# # =============================================================================
# import subprocess


# def push_to_github(file_path="data.json", commit_message="Auto Update data.json"):
#     try:
#         # Pass shell=True so Windows can locate 'git'
#         subprocess.run(["git", "add", file_path], check=True, shell=True)
#         subprocess.run(["git", "commit", "-m", commit_message], check=True, shell=True)
#         subprocess.run(["git", "push"], check=True, shell=True)

#         print("🚀 Successfully pushed to GitHub!")
#     except subprocess.CalledProcessError as e:
#         print(f"Git push failed: {e}")

# # Run after saving data.json
# push_to_github()
