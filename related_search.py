#coding: utf-8
from flask import *
from get_innen import data_build
from datetime import datetime
from collections import defaultdict
app = Flask(__name__)

players, teams, birthdate, areas, teams_list, h_alias, SORTED_PLAYERS_LIST = data_build()
PLAYERS_LENGTH = len(SORTED_PLAYERS_LIST)


REDIRECT_URL = frozenset([
    'www.innen-search.com',
    'innen-search.herokuapp.com',
    'innen-search.heroku.com',
])
URL = u'http://innen-search.com{}'


@app.before_request
def before_request():
    if request.host in REDIRECT_URL:
        return redirect(URL.format(request.path) , 301)


@app.route('/favicon.ico', methods=['GET'])
def favicon():
    abort(404)


@app.route(u'/使い方', methods=['GET'])
def functions():
    return render_template('functions.html', target=u'使い方')


@app.route('/<any(highschool, college, others, pro):team_category>', methods=['GET'])
def show_teams(team_category):
    return render_template('team_list.html', teams_list=teams_list[team_category])


DATA_KIND_PLAYER = 0
DATA_KIND_TEAM = 1
DATA_KIND_GENERATION = 2
DATA_KIND_AREA = 3
DATA_KIND_PREFIX = 4

KIND2STORE = {
    DATA_KIND_TEAM: teams,
    DATA_KIND_GENERATION: birthdate,
    DATA_KIND_AREA: areas
}

@app.route('/', methods=['GET'])
@app.route('/<target>', methods=['GET'])
def top(target=''):
    if not target:
        return render_template('top.html')
    target = h_alias.get(target, target)

    kind = get_data_kind(target)
    if kind == DATA_KIND_PLAYER:
        return player(target)
    return player_list(target, kind)


def get_data_kind(target):
    if target in players:
        return DATA_KIND_PLAYER
    elif target in teams or target in h_alias:
        return DATA_KIND_TEAM
    elif target in birthdate:
        return DATA_KIND_GENERATION
    elif target in areas:
        return DATA_KIND_AREA
    else:
        return DATA_KIND_PREFIX

def binary_search(word):
    s = PLAYERS_LENGTH
    lo = 0
    while lo < s:
        mid = (lo + s) / 2
        name = SORTED_PLAYERS_LIST[mid]
        if name.startswith(word):
            return mid
        else:
            if name < word:
                lo = mid + 1
            else:
                s = mid
    return None


def prefix_search(target):
    idx = binary_search(target)
    if idx:
        up = down = True
        search = 1
        players = {SORTED_PLAYERS_LIST[idx]}
        while up or down:
            if up:
                name = SORTED_PLAYERS_LIST[idx - search]
                if name.startswith(target):
                    players.add(name)
                else:
                    up = False
            if down:
                name = SORTED_PLAYERS_LIST[idx + search]
                if name.startswith(target):
                    players.add(name)
                else:
                    down = False
            search += 1

        return players


def get_player_list(player_names):
    return sorted([(players[pl], pl) for pl in player_names], key=lambda p:p[0].birth_date if p[0].birth_date else datetime(1, 1, 1), reverse=True)


def get_teammate(target, teamname, birth_year, diff):
    teammate_data = defaultdict(list)
    [teammate_data[int(players[pl].birth_year)].append((players[pl], pl)) for pl in teams[teamname] if pl != target and players[pl].birth_year and abs(int(players[pl].birth_year) - int(birth_year)) <= diff]
    return teammate_data

def player_list(target, kind):
    if kind == DATA_KIND_PREFIX:
        players = prefix_search(target)
    else:
        players = KIND2STORE[kind][target]

    if players:
        players = get_player_list(players)
        return render_template('list.html', target=target, players=players, kind=kind)
    return render_template('not_found.html', target=target)

def player(player_name):
    target = players[player_name]
    ctxt = {
        'target': player_name,
        'info': target,
        'get_teammate': get_teammate,
        'abs': abs
    }
    return render_template('player.html', **ctxt)


if __name__ == '__main__':
    app.run(debug=True)
