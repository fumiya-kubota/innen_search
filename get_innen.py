#coding: utf-8
import json
from collections import defaultdict
from player import Player, player_from_dict


def data_build():
    players = {}
    teams = defaultdict(set)
    areas = defaultdict(set)
    birth_year = defaultdict(set)
    teams_list = {
        'highschool': defaultdict(int),
        'college': defaultdict(int),
        'pro': defaultdict(int),
        'others': defaultdict(int),
    }
    with open('dump/dump.json') as fp:
        data = json.load(fp)
        for row in data:
            players[row['label']] = player_from_dict(row)
    for k, v in players.iteritems():
        for h in v.highschool:
            teams[h].add(k)
            teams_list['highschool'][h] += 1
        for c in v.college:
            teams[c].add(k)
            teams_list['college'][c] += 1
        for p in v.pro:
            teams[p].add(k)
            teams_list['pro'][p] += 1
        for o in v.others:
            teams[o].add(k)
            teams_list['others'][o] += 1
        for a in v.areas:
            areas[a].add(k)
        birth_year[str(v.birth_year)].add(k)
    for k in teams_list:
        teams_list[k] = tuple(sorted([tn for tn in teams_list[k].iteritems()], key=lambda x:x[1], reverse=True))

    h_alias = json.load(open('dump/highschool_alias.json'))
    sorted_players = tuple(json.load(open('dump/sorted_players_list.json')))
    return players, dict(teams), dict(birth_year), dict(areas), teams_list, h_alias, sorted_players
