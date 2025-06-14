from flask import Flask, render_template, request
from howlongtobeatpy import HowLongToBeat
import os
# importing necessary functions from dotenv library
from dotenv import load_dotenv, dotenv_values 
from steam_web_api import Steam


app = Flask(__name__)
load_dotenv() 
KEY = os.environ.get("STEAM_API_KEY")
# accessing and printing value
steam = Steam(KEY)
print(os.getenv("STEAM_API_KEY"))
""" print(steam.users.search_user("natnat4434"))
print(steam.users.get_user_details("76561199494517477"))  """# example steam id
#idea: add steam api to calculate  76561199494517477

def get_game_times(game_name):
    results = HowLongToBeat().search(game_name)
    if not results:
        return None, []
    game = max(results, key=lambda x: x.similarity) 
    print(game)# best match
    print("Image URL:", game.game_image_url)
    print("Review Score:", game.review_score)
   # Suggest up to 4 other games (excluding the best match)
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

@app.route('/', methods=['GET', 'POST'])
def index():
    completion_data = None
    est_days_main = None 
    est_days_100 = None
    error = None
    suggestions = []

    if request.method == 'POST':
        game = request.form.get('game')
        free_time = request.form.get('free_time')
        free_time_unit = request.form.get('free_time_unit')

        if not game or not free_time or not free_time_unit:
            error = "Please fill out all fields."
        else:
            try:
                free_time = float(free_time)
                if free_time <= 0:
                    raise ValueError()
            except ValueError:
                error = "Please enter a valid positive number for free time."
            
            if not error:
                times, suggestions = get_game_times(game)
                if not times:
                    error = "Sorry, no data found for that game."
                else:
                    hours_per_day = free_time if free_time_unit == 'day' else free_time / 7
                    est_days_main = times['main_story'] / hours_per_day
                    est_days_100 = times['completionist'] / hours_per_day
                    completion_data = times

    return render_template('dashboard.html',
                           completion_data=completion_data,
                           est_days_main=est_days_main,
                           est_days_100=est_days_100,
                           error=error,
                           suggestions=suggestions,
                            user_input=game if request.method == 'POST' else None,
                           free_time=free_time if request.method == 'POST' else None,
                           free_time_unit=free_time_unit if request.method == 'POST' else None
                           )
if __name__ == '__main__':
    app.run(debug=True)
