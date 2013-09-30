#coding: utf-8
from flask import *
from get_innen import build_data
from datetime import datetime

app = Flask(__name__)

players, teams, birthdate, areas, teams_list = build_data()


@app.route('/<any(highschool, college, others, pro):team_category>', methods=['GET'])
def show_teams(team_category):
    return render_template('team_list.html', teams_list=teams_list[team_category])


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


def get_player_list(player_names):
    return sorted([(players[pl], pl) for pl in player_names], key=lambda p:p[0].birth_date if p[0].birth_date else datetime(1900, 1, 1), reverse=True)


def player(player_name):
    target = players[player_name]
    ctxt = {
        'target': player_name,
        'info': target
    }
    return render_template('player.html', **ctxt)


def birthyear(year):
    year_players = birthdate[year]
    player_info = get_player_list(year_players)
    ctxt = {
        'target': year,
        'players': player_info
    }
    return render_template('year.html', **ctxt)


def team(team_name):
    team_players = teams[team_name]
    player_info = get_player_list(team_players)
    ctxt = {
        'target': team_name,
        'players': player_info
    }
    return render_template('team.html', **ctxt)


def place(place_name):
    place_player = areas[place_name]
    player_info = get_player_list(place_player)
    ctxt = {
        'target': place_name,
        'players': player_info
    }
    return render_template('place.html', **ctxt)
