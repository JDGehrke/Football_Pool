# =============================================================================
# FOOTBALL POOL - UPDATE JSON.DATA
# =============================================================================

import ast
import pandas as pd
import json
import datetime as dt
import requests
import os
import glob
from dotenv import load_dotenv,dotenv_values
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

os.chdir(r'C:\\Users\\jdgeh\Documents\Github\Football_Pool')

# =============================================================================
# ENV VARIABLES
# =============================================================================
# 1. First, load the .env file into os.environ normally
load_dotenv()

# 2. Get a dictionary of JUST the keys defined in your .env file
env_vars = dotenv_values(".env")

# 3. Inject them into your Python global namespace
globals().update(env_vars)

# 4. Adjust variable types
players = ast.literal_eval(players)
GOOGLE_CREDENTIALS = json.loads(os.getenv("GOOGLE_CREDENTIALS"))

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
    "Commanders": "WSH"
}

# =============================================================================
# READ IN CURRENT JSON FILE
# =============================================================================
with open("data.json", "r", encoding="utf-8") as file:
    current_json = json.load(file)
del file   
 
# =============================================================================
# GET PLAYER PICKS
# =============================================================================
if f'Week {current_week}' not in current_json['weeks'].keys():
    current_json['metadata']['currentWeek'] = f'Week {current_week}'
    get_picks = True    

elif dt.datetime.strptime(current_json['weeks'][f'Week {current_week}']['lockTime'], "%Y-%m-%dT%H:%MZ") > dt.datetime.now():
    get_picks = True 
    
else: #After Locktime
    get_picks = False
    

if get_picks == True:
    # =============================================================================
    # DOWNLOAD PICKS FROM GOOGLE SHEETS
    # =============================================================================
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
    picks = picks.reindex(columns=ordered_columns, fill_value="")

    #Limit Players Picks to most recent in case they submit more than 1 set
    picks = picks.drop_duplicates(subset=['Select Your Name'], keep='last')

    #Confirm every player has picks
    no_picks = []
    for p in players:
        if p not in picks.iloc[:,2].unique():
            no_picks.append(p)
    
    #If missing picks, create null picks ('-')
    if len(no_picks) > 0:
        no_picks = pd.DataFrame("—",index=no_picks,columns=picks.columns)
        no_picks.iloc[:, 2] = no_picks.index
        #no_picks.iloc[:,-1] = 0

        #Combine No picks
        picks = pd.concat([picks,no_picks])

    #Push Picks to CSV
    picks.to_csv(f'{season}\Week {current_week}.csv',index=False)
    

else: #Read locked picks from csv 
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
picks = picks.map(lambda x:x.split(' (')[0]) #remove records
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
response = requests.get(ESPN_URL, params= {'seasontype':1
                                           ,'week':current_week
                                           ,'dates':season})
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
    
    if comp['status']['type'].get("description") == 'In Progress':
        status = "🔴 Live 🔴"
    else:
        status = comp['status']['type'].get("description")

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
            
            #"status": comp['status']['type'].get("description"),
            "status": status,
            "period": comp['status'].get("period"),
            "clock": comp['status'].get("displayClock"),
            "totalScore": int(away.get("score")) + int(home.get("score")),
            "winner": winner,
            }
        })
    
# =============================================================================
# FINALIZING MATCHUPS FOR JSON 
# =============================================================================
#BUILD INDIVIDUAL GAME DICTS
for game in picks_by_game:
    gid = game['id']
    
    game.update(
        {'game': games_list[gid].get('label')
         ,'date' : games_list[gid].get('date')
         ,'winner': games_list[gid].get('winner')
         ,'status': games_list[gid].get('status')
         })
    
#BUILD TIEBREAKER WITH FINAL GAME
tiebreaker_picks = {}
for p in players: 
    if tiebreaker_scores[p] == '—':
        tiebreaker_picks.update({p: {
                                     'winner': game['picks'][p]
                                     ,'predictedTotal': tiebreaker_scores[p]
                                     }
                                 })
    else:
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
    
#FINAL WEEK DICTIONARY
week_json = {'lockTime': games_list[picks_by_game[0]['id']]['date']
             ,'matchups': picks_by_game
             ,'tiebreaker': tiebreaker}

# =============================================================================
# UPDATE JSON
# =============================================================================
#Set Week's Json into final
current_json['weeks'][f'Week {current_week}'] = week_json
    
#Set Header Update Time
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

# =============================================================================
# PUSH TO GITHUB
# =============================================================================
# 1. Locate GitHub Desktop's git.exe path FIRST
app_data = os.getenv("LOCALAPPDATA")
git_paths = glob.glob(
    os.path.join(
        app_data,
        "GitHubDesktop",
        "app-*",
        "resources",
        "app",
        "git",
        "cmd",
        "git.exe",
    )
)

# 2. Set environment variable BEFORE importing git/GitPython
os.environ["GIT_PYTHON_GIT_EXECUTABLE"] = max(git_paths, key=os.path.getmtime)

# 3. NOW import Repo (it will read the environment variable during initialization)
from git import Repo

#FUNCTION TO PUSH TO GITHUB
def commit_and_push_data_json(repo_path=".", file_relative_path="data.json", commit_message="Update pool data"):
    """
    Stages, commits, and pushes data.json to GitHub using GitPython.
    """
    try:
        # Load local git repository
        repo = Repo(repo_path)
        
        # Verify repository is valid and not detached
        if repo.bare:
            print("Error: Target directory is a bare repository.")
            return False

        # Stage specific file
        abs_file_path = os.path.join(repo.working_dir, file_relative_path)
        if not os.path.exists(abs_file_path):
            print(f"Error: {file_relative_path} does not exist.")
            return False

        repo.index.add([file_relative_path])

        # Check if there are changes staged for commit
        if not repo.index.diff("HEAD"):
            print("No changes detected in data.json. Skipping commit and push.")
            return True

        # Commit changes
        repo.index.commit(commit_message)
        print(f"Committed changes with message: '{commit_message}'")

        # Push to remote 'origin' on current active branch
        origin = repo.remote(name="origin")
        push_info = origin.push()

        # Check for errors in push response
        for info in push_info:
            if info.flags & info.ERROR:
                print(f"Push error: {info.summary}")
                return False

        print("Successfully pushed data.json to GitHub!")
        return True

    except Exception as e:
        print(f"An error occurred during Git operation: {e}")
        return False


# PUSH TO GITHUB!
commit_and_push_data_json(
    file_relative_path="data.json",
    commit_message="Auto-update NFL pool data.json"
)