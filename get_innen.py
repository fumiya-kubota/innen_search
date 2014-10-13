# coding: utf-8
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
        teams_list[k] = tuple(sorted([tn for tn in teams_list[k].iteritems()], key=lambda x: x[1], reverse=True))

    alias = json.load(open('dump/team_alias.json'))
    alias_reverse = defaultdict(list)
    for k, v in alias.iteritems():
        alias_reverse[v].append(k)

    highschool_pref = json.load(open('dump/highschool_pref.json'))
    highschool_pref = {key: highschool_pref[key] for key in highschool_pref if key in teams}
    league_teams = defaultdict(list)
    for k, v in highschool_pref.iteritems():
        league_teams[v[0]].append(k)

    sorted_players = tuple(json.load(open('dump/sorted_players_list.json')))
    return players, dict(teams), dict(birth_year), dict(
        areas), teams_list, alias, alias_reverse, sorted_players, highschool_pref, league_teams
