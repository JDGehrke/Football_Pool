import json
import os
import requests
from dotenv import load_dotenv,dotenv_values
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# =============================================================================
# PROGRAM VARIABLES
# =============================================================================
season = 2026
current_week = 1

# =============================================================================
# ENV VARIABLES
# =============================================================================
# 1. First, load the .env file into os.environ normally
load_dotenv()

# 2. Get a dictionary of JUST the keys defined in your .env file
env_vars = dotenv_values(".env")

# 3. Inject them into your Python global namespace
globals().update(env_vars)

# ==============================================================================
# 1. AUTHENTICATION & CONFIGURATION
# ==============================================================================
# Read credentials from environment
GOOGLE_CREDENTIALS = json.loads(os.getenv("GOOGLE_CREDENTIALS"))

#App Scripts url to delete forms
WEB_APP_URL = 'https://script.google.com/macros/s/AKfycbxz8B8CwE5-iTZ7Zxz0NedkeFOggyIlatyaiBf5AK0M1lmzlSkI9ipMeDnzP0_aKaVC/exec'

# Read Form ID
FORM_ID = os.getenv("FORM_ID")

# BOTH scopes must be explicitly requested
SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly",
]

ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"

players = ['AUSTIN','BRANDON','JORDAN','MOM']

# ==============================================================================
# 2. FUNCTIONS
# ==============================================================================
def fetch_espn_games(week_num=None, season_type=1, season_year=None):
    """
    Fetches NFL games from ESPN API.
    
    Parameters:
      - week_num (int): Week number (1-18 for regular season, 1-3 for preseason, 1-5 for playoffs)
      - season_type (int): 1 = Preseason, 2 = Regular Season, 3 = Postseason/Playoffs
      - season_year (int/str): e.g. 2026
    """
    params = {
        "seasontype": season_type
    }
    
    if week_num:
        params["week"] = week_num
    if season_year:
        params["dates"] = season_year

    response = requests.get(ESPN_URL, params=params)
    data = response.json()

    # Get ESPN's week title (e.g., "Regular Season Week 1", "Wild Card Weekend")
    raw_week_text = data.get("week", {}).get("text", f"Week {week_num or ''}")
    
    # Prepend season phase label for clear Google Form titles
    season_labels = {1: "Preseason", 2: "NFL", 3: "Playoffs"}
    phase_label = season_labels.get(season_type, "NFL")
    
    week_title = f"{phase_label} - {raw_week_text}"

    games = []
    for event in data.get("events", []):
        comp = event["competitions"][0]
        try:
            odds = comp["odds"][0]
        except: 
            odds = {'spread':'N/A','overUnder':'N/A'}

        away = next(t for t in comp["competitors"] if t["homeAway"] == "away")
        home = next(t for t in comp["competitors"] if t["homeAway"] == "home")

        games.append({
            "id": event.get("id"),
            "name": event.get("name"),
            "label": event.get("shortName"),
            
            "away": away["team"].get("displayName"),
            "awayShort": away["team"].get("abbreviation"),
            "awayLocation": away["team"].get("location"),
            "awayMascot": away["team"].get("name"),
            "awayRecord": away["records"][0].get("summary"),
            
            "home": home["team"].get("displayName"),
            "homeShort": home["team"].get("abbreviation"),
            "homeLocation": home["team"].get("location"),
            "homeMascot": home["team"].get("name"),
            "homeRecord": home["records"][0].get("summary"),
            
            "date": event.get("date"),
            "broadcast": comp.get("broadcast"),
            "spread": odds.get("spread"),
            "overUnder": odds.get("overUnder")
        })

    return week_title, games

# #Testing
# fetch_espn_games(5,3,2025)


def clear_form_responses(form_id):
    try:
        response = requests.get(WEB_APP_URL, params={"formId": form_id})

        # Safeguard: Verify HTTP status before parsing JSON
        if response.status_code != 200:
            print(
                f"⚠️ Server returned HTTP {response.status_code}: {response.text[:200]}"
            )
            return

        data = response.json()
        print(f"Status: {data.get('status')} | {data.get('message')}")

    except Exception as e:
        print(f"⚠️ Failed to parse response: {e}")

# # Usage
# clear_form_responses(FORM_ID)
        
def to_unicode_bold(text):
    """Converts plain ASCII letters and numbers into bold Unicode characters."""
    bold_mapping = {}

    # Map uppercase letters (A-Z)
    for i, char in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        bold_mapping[char] = chr(0x1D400 + i)

    # Map lowercase letters (a-z)
    for i, char in enumerate("abcdefghijklmnopqrstuvwxyz"):
        bold_mapping[char] = chr(0x1D41A + i)

    # Map numbers (0-9)
    for i, char in enumerate("0123456789"):
        bold_mapping[char] = chr(0x1D7CE + i)

    return "".join(bold_mapping.get(c, c) for c in text)


def update_existing_form(week_num, season_type, season_year):
    """Clears existing questions and updates the fixed Google Form with new games."""
    # 1. Fetch upcoming matchups from ESPN
    week_title, games = fetch_espn_games(week_num, season_type, season_year)
    print(f"Loaded {len(games)} games for {week_title}.")

    # 2. Authenticate
    creds = Credentials.from_service_account_info(GOOGLE_CREDENTIALS, scopes=SCOPES)
    forms_service = build("forms", "v1", credentials=creds)
    
    # 3. Clear out last week's player responses
    clear_form_responses(FORM_ID)

    # 4. Get existing form structure to find current items to delete
    current_form = forms_service.forms().get(formId=FORM_ID).execute()
    current_items = current_form.get("items", [])

    requests_list = []

    # Step A: Update Form Title
    requests_list.append(
        {
            "updateFormInfo": {
                "info": {"title": f"Orser Family Football Pool: {week_title}"},
                "updateMask": "title",
            }
        }
    )

    # Step B: Delete all existing questions (done in reverse index order)
    for i in range(len(current_items) - 1, -1, -1):
        requests_list.append({"deleteItem": {"location": {"index": i}}})

    # Step C: Re-build questions from scratch
    location_index = 0

    # Item 1: Player Name Question
    requests_list.append({
    "createItem": {
        "item": {
            "title": "Select Your Name",
            "questionItem": {
                "question": {
                    "required": True,
                    "choiceQuestion": {
                        "type": "DROP_DOWN",
                        "options": [{"value": player} for player in players]
                    }
                }
            }
        },
        "location": {"index": location_index}
        }
    })
    location_index += 1

    # Item 2: Weekly Matchups
    for game in games:
        requests_list.append(
            {
                "createItem": {
                    "item": {
                        "title": game['id'] + ': ' + to_unicode_bold(game["name"]) + ' (' + str(game["spread"]) + ')',
                        "description": game['broadcast'],
                        "questionItem": {
                            "question": {
                                "required": True,
                                "choiceQuestion": {
                                    "type": "RADIO",
                                    "options": [
                                        {"value": game["awayMascot"] + ' (' + game['awayRecord'] + ')'},
                                        {"value": game["homeMascot"] + ' (' + game['homeRecord'] + ')'},
                                    ],
                                },
                            }
                        },
                    },
                    "location": {"index": location_index},
                }
            }
        )
        location_index += 1

    # Item 3: Tiebreaker Question
    requests_list.append(
        {
            "createItem": {
                "item": {
                    "title": "Tiebreaker: Total Combined Score",
                    "description": "Vegas O/U: " + str(game['overUnder']),
                    "questionItem": {
                        "question": {
                            "required": True,
                            "textQuestion": {"paragraph": False},
                        }
                    },
                },
                "location": {"index": location_index},
            }
        }
    )

    # 4. Execute all changes atomically in a single API request
    forms_service.forms().batchUpdate(
        formId=FORM_ID, body={"requests": requests_list}
    ).execute()

    public_url = f"https://docs.google.com/forms/d/{FORM_ID}/viewform"
    print(f"\n Form successfully updated for {week_title}!")
    print(f"Permanent Player Link: {public_url}")
    
    
# =============================================================================
# RUN UPDATE TO FORM 
# =============================================================================
update_existing_form(1, 1, 2026)
