import os
import requests
import json
from dotenv import load_dotenv, dotenv_values 
load_dotenv() 
KEY = os.environ.get("STEAM_API_KEY")
def get_unplayed_games(steam_id, api_key):
    """
    Retrieves a list of unplayed games for a given Steam user.

    Args:
        steam_id: The SteamID of the user.
        api_key: The Steam Web API key (optional, but recommended).

    Returns:
        A list of app IDs for unplayed games, or None if an error occurs.
    """
    url = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={api_key}&steamid={steam_id}&include_appinfo=true"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()

        unplayed_games = []
        if "response" in data and "games" in data["response"]:
            for game in data["response"]["games"]:
                if game.get("playtime_forever") == 0:
                    unplayed_games.append(game["name"])
        return unplayed_games
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Example usage (replace with actual SteamID and API key)
steam_id = "76561199494517477"  # Example SteamID
api_key = KEY  # Replace with your Steam Web API key
unplayed = get_unplayed_games(steam_id, api_key)

if unplayed:
    print(f"Unplayed games: {unplayed}")
else:
    print("Could not retrieve unplayed games.")