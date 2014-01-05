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

    alias = {
        u'阪神': u'阪神タイガース',
        u'タイガース': u'阪神タイガース',
        u'読売': u'読売ジャイアンツ',
        u'巨人': u'読売ジャイアンツ',
        u'ジャイアンツ': u'読売ジャイアンツ',
        u'中日': u'中日ドラゴンズ',
        u'ドラゴンズ': u'中日ドラゴンズ',
        u'ホークス': u'福岡ソフトバンクホークス',
        u'ソフトバンク': u'福岡ソフトバンクホークス',
        u'日本ハム': u'北海道日本ハムファイターズ',
        u'ファイターズ': u'北海道日本ハムファイターズ',
        u'日ハム': u'北海道日本ハムファイターズ',
        u'オリックス': u'オリックス・バファローズ',
        u'バファローズ': u'オリックス・バファローズ',
        u'DeNA': u'横浜DeNAベイスターズ',
        u'ベイスターズ': u'横浜DeNAベイスターズ',
        u'横浜': u'横浜DeNAベイスターズ',
        u'ライオンズ': u'埼玉西武ライオンズ',
        u'埼玉西武': u'埼玉西武ライオンズ',
        u'西武': u'埼玉西武ライオンズ',
        u'千葉ロッテ': u'千葉ロッテマリーンズ',
        u'ロッテ': u'千葉ロッテマリーンズ',
        u'マリーンズ': u'千葉ロッテマリーンズ',
        u'広島': u'広島東洋カープ',
        u'広島東洋': u'広島東洋カープ',
        u'カープ': u'広島東洋カープ',
        u'東京ヤクルト': u'東京ヤクルトスワローズ',
        u'ヤクルト': u'東京ヤクルトスワローズ',
        u'スワローズ': u'東京ヤクルトスワローズ',
        u'近鉄': u'大阪近鉄バファローズ',
        u'大阪近鉄': u'大阪近鉄バファローズ',
        u'楽天': u'東北楽天ゴールデンイーグルス',
        u'東北楽天': u'東北楽天ゴールデンイーグルス',
        u'ゴールデンイーグルス': u'東北楽天ゴールデンイーグルス',
        u'イーグルス': u'東北楽天ゴールデンイーグルス',
    }
    team_alias = json.load(open('dump/team_alias.json'))
    alias.update(team_alias)
    alias_reverse = defaultdict(list)
    for k, v in alias.iteritems():
        alias_reverse[v].append(k)

    highschool_pref = json.load(open('dump/highschool_pref.json'))
    highschool_pref = {key:highschool_pref[key] for key in highschool_pref if key in teams}
    leage_teams = defaultdict(list)
    for k, v in highschool_pref.iteritems():
        leage_teams[v[0]].append(k)

    sorted_players = tuple(json.load(open('dump/sorted_players_list.json')))
    return players, dict(teams), dict(birth_year), dict(areas), teams_list, alias, alias_reverse, sorted_players, highschool_pref, leage_teams

