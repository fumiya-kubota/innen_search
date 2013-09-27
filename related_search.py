#coding: utf-8
from flask import *
from get_innen import build_data
import sys

app = Flask(__name__)

players, teams, birthdate, areas = build_data()


@app.route('/', methods=['GET'])
@app.route('/<target>', methods=['GET'])
def top(target=''):
    if not target:
        return render_template('top.html')
    elif target in players:
        return player(target)
    elif target in teams:
        return team(target)
    elif target in birthdate:
        return birthyear(target)
    elif target in areas:
        return place(target)
    else:
        return render_template('not_found.html', target=target)


def player(player_name):
    target = players[player_name]
    ctxt = {
        'target': player_name,
        'info': target
    }
    return render_template('player.html', **ctxt)


def birthyear(year):
    year_players = birthdate[year]
    player_info = [players[pl] for pl in year_players]
    ctxt = {
        'target': year,
        'player_info': player_info,
        'players': year_players
    }
    return render_template('year.html', **ctxt)


def team(team_name):
    team_players = teams[team_name]
    player_info = [players[pl] for pl in team_players]
    ctxt = {
        'target': team_name,
        'player_info': player_info,
        'players': team_players
    }
    return render_template('team.html', **ctxt)


def place(place_name):
    place_player = areas[place_name]
    player_info = [players[pl] for pl in place_player]
    ctxt = {
        'target': place_name,
        'player_info': player_info,
        'players': place_player
    }
    return render_template('place.html', **ctxt)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(sys.argv[1]), debug=True)
