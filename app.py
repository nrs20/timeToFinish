import time
from flask import Flask, render_template, request
from howlongtobeatpy import HowLongToBeat
import os
import requests
from dotenv import load_dotenv
from steam_web_api import Steam

app = Flask(__name__)
load_dotenv()

KEY = os.environ.get("STEAM_API_KEY")
steam = Steam(KEY)


def get_game_times(game_name):
    results = HowLongToBeat().search(game_name)
    if not results:
        return None, []
    game = max(results, key=lambda x: x.similarity)

    suggestions = [
        {'name': g.game_name, 'main_story': g.main_story, 'completionist': g.completionist}
        for g in results if g != game
    ][:4]

    return {
        'name': game.game_name,
        'main_story': game.main_story,
        'completionist': game.completionist,
        'image_url': game.game_image_url,
        'game_review_score': game.review_score,
        'profile_platforms': game.profile_platforms,
        'game_web_link': game.game_web_link
    }, suggestions


def get_unplayed_games(steam_id, api_key):
    url = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={api_key}&steamid={steam_id}&include_appinfo=true"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        unplayed_games = []
        if "response" in data and "games" in data["response"]:
            for game in data["response"]["games"]:
                if game.get("playtime_forever", 0) == 0:
                    unplayed_games.append(game["name"])
        return unplayed_games
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None


def get_game_times_from_steam(unplayed_games, max_games=10, delay_between_requests=5):
    """
    Fetches HowLongToBeat data for unplayed games, with rate-limiting protection.

    Args:
        unplayed_games: List of unplayed game names from Steam.
        max_games: Max number of games to fetch (to prevent overloading HLTB).
        delay_between_requests: Seconds to wait between each request.

    Returns:
        A list of dicts with game name, main story, and completionist times.
    """
    game_data = []
    games_checked = 0

    for game in unplayed_games:
        if games_checked >= max_games:
            break

        try:
            print(f"Searching for game: {game}")
            results = HowLongToBeat().search(game)
            if results:
                best_match = max(results, key=lambda x: x.similarity)
                game_data.append({
                    'name': best_match.game_name,
                    'main_story': best_match.main_story,
                    'completionist': best_match.completionist
                })
                games_checked += 1
                time.sleep(delay_between_requests)  # Rate limiting protection
        except Exception as e:
            print(f"Error searching for '{game}': {e}")
            continue

    return game_data

@app.route('/', methods=['GET', 'POST'])
def index():
    completion_data = None
    est_days_main = None
    est_days_100 = None
    error = None
    suggestions = []
    user_unplayed_data = []
    total_hours_main = 0
    total_hours_completionist = 0

    game = None
    steam_id = None
    free_time = None
    free_time_unit = None

    if request.method == 'POST':
        game = request.form.get('game')
        steam_id = request.form.get('steam_id', '76561199494517477')
        free_time = request.form.get('free_time')
        free_time_unit = request.form.get('free_time_unit')

        if not game or not free_time or not free_time_unit or not steam_id:
            error = "Please fill out all fields."
        else:
            try:
                free_time = float(free_time)
                if free_time <= 0:
                    raise ValueError()
            except ValueError:
                error = "Please enter a valid number for free time."

            if not error:
                # Lookup one game for demo
                completion_data, suggestions = get_game_times(game)

                # Get user's unplayed games
                unplayed_games = get_unplayed_games(steam_id, KEY)
                if unplayed_games:
                    user_unplayed_data = get_game_times_from_steam(unplayed_games)
                    total_hours_main = sum([game['main_story'] or 0 for game in user_unplayed_data])
                    total_hours_completionist = sum([game['completionist'] or 0 for game in user_unplayed_data])
                else:
                    error = "Couldn't fetch unplayed games or none found."

                # Calculate estimates
                hours_per_day = free_time if free_time_unit == 'day' else free_time / 7
                if completion_data:
                    est_days_main = completion_data['main_story'] / hours_per_day
                    est_days_100 = completion_data['completionist'] / hours_per_day

    return render_template('dashboard.html',
                           completion_data=completion_data,
                           est_days_main=round(est_days_main, 1) if est_days_main else None,
                           est_days_100=round(est_days_100, 1) if est_days_100 else None,
                           error=error,
                           suggestions=suggestions,
                           user_input=game,
                           free_time=free_time,
                           free_time_unit=free_time_unit,
                           unplayed_data=user_unplayed_data,
                           total_hours_main=round(total_hours_main, 1),
                           total_hours_100=round(total_hours_completionist, 1)
                           )


if __name__ == '__main__':
    app.run(debug=True)
