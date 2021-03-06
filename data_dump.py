# coding: utf-8
from SPARQLWrapper import SPARQLWrapper, JSON
import re
from datetime import datetime
from collections import defaultdict
import json
import codecs
import os
from player import Player, player_from_dict
import dateutil.parser

DATE_REGX = re.compile(ur'\d{4}年\d{1,2}月\d{1,2}日')
NENGO_REGX = re.compile(ur'[（\(]..\d{1,2}年[）\)]')
YEAR_REGX = re.compile(ur'\d{4}年')

nums = frozenset(map(str, xrange(10)))

data_dir = 'data'


def parse_date(birthdate):
    return dateutil.parser.parse(birthdate, fuzzy=True)


# 例1清水 宏員（しみず ひろかず、1933年4月14日 - ）は、日本のプロ野球選手（投手）。
# 例2新庄 剛志（しんじょう つよし、1972年（昭和47年）1月28日 - ）
def parse_abstract(abstract):
    #例2のような年号を取り除く
    candidate = []
    n = NENGO_REGX.search(abstract)
    if n:
        b = n.start(), n.end()
        abstract = abstract.replace(abstract[b[0]:b[1]], '')

    match = DATE_REGX.search(abstract)
    if match:
        date = match.group(0)
        date = ''.join([d if d in nums else '-' for d in date[:-1]])
        candidate.append(datetime.strptime(date, '%Y-%m-%d'))

    match = YEAR_REGX.search(abstract)
    if match:
        date = match.group(0)
        candidate.append(datetime(int(date[:4]), 4, 2))
    if candidate:
        return min(candidate)


def label_common(label):
    #ラベルでも(野球)は辞書内で重複する可能性はないので取り除く
    if label.endswith(u' (野球)'):
        return label[:-5]
    return label


def label_common_first(label):
    #ラベルでも(野球)は辞書内で重複する可能性はないので取り除く
    if label.endswith(u' (野球)'):
        return label[:-5], '_' + label[-4:]
    return label, None


target_player = u'''
        #対象は日本人の野球選手
        {
            ?person dbp-owl:wikiPageWikiLink <http://ja.dbpedia.org/resource/Category:日本の野球選手> .
        } union {
            ?person dbp-owl:wikiPageWikiLink <http://ja.dbpedia.org/resource/Category:MLBの日本人選手> .
        } union {
            ?person dbp-owl:wikiPageWikiLink <http://ja.dbpedia.org/resource/Category:在日外国人の野球選手> .
        } union {
            ?person dbp-owl:wikiPageWikiLink <http://ja.dbpedia.org/resource/Category:日系人の野球選手> .
        }
'''

birth_query = u'''
    PREFIX dbp-owl: <http://dbpedia.org/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    select distinct ?label ?birthdate
    where {
        *target_player

        ?person rdfs:label ?label .

        #生年月日を探す手がかり
        #基本はbirthDateだが、それが無い人もいる。
        ?person dbp-owl:birthDate ?birthdate .
    }
'''

abstract_query = u'''
    PREFIX dbp-owl: <http://dbpedia.org/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    select distinct ?label ?abstract
    where {
        *target_player

        ?person rdfs:label ?label ;
            dbp-owl:abstract ?abstract .
    }
'''

highschool_query = u'''
    PREFIX dbp-owl: <http://dbpedia.org/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX dbpprop-ja: <http://ja.dbpedia.org/property/>

    select distinct ?label ?team_label
    where {
        *target_player

        ?person rdfs:label ?label ;
            dbp-owl:team ?team.

        {
            ?team dbp-owl:wikiPageRedirects ?redirects .
            ?redirects dbpprop-ja:wikiPageUsesTemplate <http://ja.dbpedia.org/resource/Template:日本の高等学校> ;
                rdfs:label ?team_label .
        } union {
            ?team dbpprop-ja:wikiPageUsesTemplate <http://ja.dbpedia.org/resource/Template:日本の高等学校> ;
                rdfs:label ?team_label .
        }
    }
'''

college_query = u'''
    PREFIX dbp-owl: <http://dbpedia.org/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX dbpprop-ja: <http://ja.dbpedia.org/property/>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    select distinct ?label ?team_label
    where {
        *target_player

        ?person rdfs:label ?label ;
            dbp-owl:team ?team.
        {
            ?team dbp-owl:wikiPageRedirects ?redirects .
            ?redirects dbp-owl:wikiPageWikiLink ?category .
            ?category rdf:type skos:Concept .
            ?category rdfs:label ?category_label .
            FILTER regex(?category_label, "大学")
            ?redirects rdfs:label ?team_label .
            FILTER NOT EXISTS {
                ?redirects dbp-owl:wikiPageWikiLink <http://ja.dbpedia.org/resource/Category:アマチュア野球チーム> .
            }
            FILTER NOT EXISTS {
                ?redirects dbpprop-ja:wikiPageUsesTemplate <http://ja.dbpedia.org/resource/Template:日本の高等学校> .
            }
        } union {
            ?team dbp-owl:wikiPageWikiLink ?category .
            ?category rdf:type skos:Concept .
            ?category rdfs:label ?category_label .
            FILTER regex(?category_label, "大学")
            ?team rdfs:label ?team_label .
            FILTER NOT EXISTS {
                ?team dbp-owl:wikiPageWikiLink <http://ja.dbpedia.org/resource/Category:アマチュア野球チーム> .
            }
            FILTER NOT EXISTS {
                ?team dbpprop-ja:wikiPageUsesTemplate <http://ja.dbpedia.org/resource/Template:日本の高等学校> .
            }
        }
    }
'''

pro_query = u'''
    PREFIX dbp-owl: <http://dbpedia.org/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    select distinct ?label ?team_label
    where {
        *target_player

        ?person dbp-owl:team ?team ;
            rdfs:label ?label .
        {
            ?team dbp-owl:wikiPageRedirects ?redirects .
            <http://ja.dbpedia.org/resource/プロ野球チーム一覧> dbp-owl:wikiPageWikiLink ?redirects .
            ?redirects rdfs:label ?team_label .
        } union {
            <http://ja.dbpedia.org/resource/プロ野球チーム一覧> dbp-owl:wikiPageWikiLink ?team .
            ?team rdfs:label ?team_label .
        }
    }
'''

others_query = u'''
    PREFIX dbp-owl: <http://dbpedia.org/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX dbpprop-ja: <http://ja.dbpedia.org/property/>

    select distinct ?label ?team_label
    where {
        *target_player

        ?person rdfs:label ?label ;
            dbp-owl:team ?team .

        {
            ?team dbp-owl:wikiPageRedirects ?redirects .
            FILTER NOT EXISTS {
                ?redirects dbpprop-ja:wikiPageUsesTemplate <http://ja.dbpedia.org/resource/Template:日本の高等学校> .
            }
            FILTER NOT EXISTS {
                <http://ja.dbpedia.org/resource/プロ野球チーム一覧> dbp-owl:wikiPageWikiLink ?redirects .
            }

            ?redirects rdfs:label ?team_label .
        } union {
            FILTER NOT EXISTS {
                ?team dbp-owl:wikiPageRedirects ?redirects .
            }
            FILTER NOT EXISTS {
                ?team dbpprop-ja:wikiPageUsesTemplate <http://ja.dbpedia.org/resource/Template:日本の高等学校> .
            }
            FILTER NOT EXISTS {
                <http://ja.dbpedia.org/resource/プロ野球チーム一覧> dbp-owl:wikiPageWikiLink ?team .
            }
            ?team rdfs:label ?team_label .
        }
    }
'''

pref_query = u'''
    PREFIX dbp-owl: <http://dbpedia.org/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX dbpprop-ja: <http://ja.dbpedia.org/property/>

    select distinct ?label ?pref_label ?home_town_label
    where {
        *target_player

        ?person rdfs:label ?label ;
            dbp-owl:birthPlace ?pref .

        #県にリダイレクトページの可能性を疑う必要はあるか？
        {
            ?pref dbp-owl:wikiPageRedirects ?redirects .
            ?redirects rdfs:label ?pref_label .
        } union {
            ?pref rdfs:label ?pref_label .
        }

        #出身地、フォーマットは特になし
        optional {
            {
                ?person dbpprop-ja:出身地 ?home_town .
                ?home_town rdfs:label ?home_town_label .
            } union {
                ?person dbpprop-ja:出身地 ?home_town_label .
            }
        }
    }
'''

cname_query = u'''
    PREFIX dbp-owl: <http://dbpedia.org/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX dbpprop-ja: <http://ja.dbpedia.org/property/>

    select distinct ?label ?cname
    where {
        *target_player

        ?person rdfs:label ?label ;
            dbp-owl:commonName ?cname .
    }
'''

club_query = u'''
    PREFIX dbp-owl: <http://dbpedia.org/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX dbpprop-ja: <http://ja.dbpedia.org/property/>

    select distinct ?label ?club_label ?division
    where {
        *target_player

        ?person rdfs:label ?label ;
            dbp-owl:club ?club .
        optional{?person dbpprop-ja:役職 ?division .}
        #県にリダイレクトページの可能性を疑う必要はあるか？
        {
            ?club dbp-owl:wikiPageRedirects ?redirects .
            <http://ja.dbpedia.org/resource/プロ野球チーム一覧> dbp-owl:wikiPageWikiLink ?redirects .
            ?redirects rdfs:label ?club_label .
        } union {
            <http://ja.dbpedia.org/resource/プロ野球チーム一覧> dbp-owl:wikiPageWikiLink ?club .
            ?club rdfs:label ?club_label .
        }
    }
'''

highschool_alias_query = u'''
    PREFIX dbp-owl: <http://dbpedia.org/ontology/>
    PREFIX dbpprop-ja: <http://ja.dbpedia.org/property/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    select distinct ?team_label ?r_label
    where {
        {
            ?team dbp-owl:wikiPageRedirects ?redirects .
            ?redirects dbpprop-ja:wikiPageUsesTemplate <http://ja.dbpedia.org/resource/Template:日本の高等学校> ;
                rdfs:label ?team_label .
        } union {
            ?team dbpprop-ja:wikiPageUsesTemplate <http://ja.dbpedia.org/resource/Template:日本の高等学校> ;
                rdfs:label ?team_label .
            FILTER NOT EXISTS{?team dbp-owl:wikiPageRedirects ?redirects .}
        }
        ?r dbp-owl:wikiPageRedirects ?team ;
            rdfs:label ?r_label .
    }
'''

proteam_alias_query = u'''
    PREFIX dbp-owl: <http://dbpedia.org/ontology/>
    PREFIX dbpprop-ja: <http://ja.dbpedia.org/property/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    select distinct ?team_label ?r_label
    where {
        {
            ?team dbp-owl:wikiPageRedirects ?redirects .
            <http://ja.dbpedia.org/resource/プロ野球チーム一覧> dbp-owl:wikiPageWikiLink ?redirects .
            ?redirects rdfs:label ?team_label .
        } union {
            <http://ja.dbpedia.org/resource/プロ野球チーム一覧> dbp-owl:wikiPageWikiLink ?team .
            ?team rdfs:label ?team_label .
            FILTER NOT EXISTS{?team dbp-owl:wikiPageRedirects ?redirects .}
        }
        ?r dbp-owl:wikiPageRedirects ?team ;
            rdfs:label ?r_label .
    }
'''


def get_json(query, file_name):
    sparql = SPARQLWrapper('http://ja.dbpedia.org/sparql')
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    outfile = open('data/{}.json'.format(file_name), 'w')
    outfile = codecs.lookup('utf-8')[-1](outfile)
    json.dump(
        results['results']['bindings'], outfile,
        ensure_ascii=False, encoding='utf-8', indent=2, sort_keys=True)


def make_data():
    #選手情報を作成する。
    players = defaultdict(Player)
    """
    始めにチーム情報を設定する。
    チーム情報が存在する選手はしっかりとした「野球選手」である可能性が高いためである。
    """

    cname = {}
    filename = os.path.join(data_dir, 'cname.json')
    with open(filename) as fp:
        cname_data = json.load(fp)
    birthdate = defaultdict(set)
    for data in cname_data:
        label = label_common(data['label']['value'])
        cname[label] = data['cname']['value']

    club = defaultdict(dict)
    filename = os.path.join(data_dir, 'club.json')
    with open(filename) as fp:
        club_data = json.load(fp)
    birthdate = defaultdict(set)
    for data in club_data:
        label = label_common(data['label']['value'])
        club[label]['club'] = data['club_label']['value']
        if 'division' in data:
            club[label]['division'] = data['division']['value']

    teams = {}
    teams_list = {}

    college_names = set()
    college_name_fix = {
        u'東京農業大学北海道オホーツク硬式野球部': u'東京農業大学北海道',
        u'慶應義塾体育会野球部': u'慶應義塾大学',
        u'早稲田大学野球部': u'早稲田大学',
        u'同志社大学体育会硬式野球部': u'同志社大学',
        u'法政大学野球部': u'法政大学',
        u'近畿大学体育会硬式野球部': u'近畿大学'
    }

    def college_team_name(team_name):
        team_name = college_name_fix.get(team_name, team_name)
        if team_name.endswith(u'硬式野球部'):
            return team_name[:-5]
        elif team_name.endswith(u'野球部'):
            return team_name[:-3]
        return team_name

    filename = os.path.join(data_dir, 'college_team.json')
    with open(filename) as fp:
        college_data = json.load(fp)
    category_teams = defaultdict(set)
    for data in college_data:
        label, label_end = label_common_first(data['label']['value'])
        team_name = data['team_label']['value']
        player = players[label]
        if label_end:
            player.label_end = label_end
        college_names.add(team_name)
        team_name = college_team_name(team_name)
        college_names.add(team_name)
        player.cname = cname.get(label, label)
        category_teams[team_name].add(label)
        player.college.add(team_name)
    teams_list['college'] = sorted(list(category_teams))
    teams.update(category_teams)

    for category in ('highschool', 'pro', 'others'):
        category_teams = defaultdict(set)
        filename = os.path.join(data_dir, '{}_team.json'.format(category))
        with open(filename) as fp:
            teams_data = json.load(fp)
        for data in teams_data:
            label, label_end = label_common_first(data['label']['value'])
            team_name = data['team_label']['value']
            if team_name in college_names:
                continue
            if team_name.endswith(u'硬式野球部'):
                team_name = team_name[:-5]
            elif team_name.endswith(u'野球部'):
                team_name = team_name[:-3]
            player = players[label]
            if label_end:
                player.label_end = label_end

            getattr(player, category).add(team_name)
            category_teams[team_name].add(label)
            player.cname = cname.get(label, label)
            current_state = club.get(label)
            if current_state:
                player.current_club = current_state['club']
                if 'division' not in current_state or u'選手' in current_state['division']:
                    player.is_active = True
        teams_list[category] = category_teams
        teams.update(category_teams)

    for k in teams_list:
        member_num = [(team, len(teams[team])) for team in teams_list[k]]
        teams_list[k] = sorted(member_num, key=lambda x: x[1], reverse=True)

    del category_teams

    filename = os.path.join(data_dir, 'birthdate.json')
    with open(filename) as fp:
        birthdate_data = json.load(fp)
    birthdate = defaultdict(set)
    for data in birthdate_data:
        label = label_common(data['label']['value'])
        if label not in players:
            continue
        player = players[label]
        birth = data['birthdate']['value']
        date = parse_date(birth)
        year = player.set_birth_date(date)
        if year:
            birthdate[year].add(label)

    filename = os.path.join(data_dir, 'abstract.json')
    with open(filename) as fp:
        abstract_data = json.load(fp)
    for data in abstract_data:
        label = label_common(data['label']['value'])
        if label not in players:
            continue
        player = players[label]
        abstract = data['abstract']['value']
        if not player.birth_year:
            date = parse_abstract(abstract)
            if date:
                year = player.set_birth_date(date)
                birthdate[year].add(label)
        player.abstract = abstract

    areas = defaultdict(set)
    filename = os.path.join(data_dir, 'area.json')
    with open(filename) as fp:
        areas_data = json.load(fp)

    for data in areas_data:
        label = label_common(data['label']['value'])
        if label not in players:
            continue
        player = players[label]
        pref = data['pref_label']
        if pref['type'] == 'literal':
            player.add_area(pref['value'])
            areas[pref['value']].add(label)

        ht = data.get('home_town_label')
        if ht and ht['type'] == 'literal':
            player.add_area(ht['value'])
            areas[ht['value']].add(label)

    my_fix(players)

    dump_file = open('dump/dump.json', 'w')
    dump_file = codecs.lookup('utf-8')[-1](dump_file)

    dump_data = [pl.dump(k) for k, pl in players.iteritems()]
    json.dump(
        dump_data, dump_file,
        ensure_ascii=False, encoding='utf-8', indent=2, sort_keys=True)
    dump_file.close()

    dump_file = open('dump/team_alias.json', 'w')
    dump_file = codecs.lookup('utf-8')[-1](dump_file)
    alias = {}
    for filename in ('highschool_alias.json', 'proteam_alias.json'):
        for row in json.load(open('data/' + filename)):
            label = row['team_label']['value']
            if label not in teams:
                continue
            alias[row['r_label']['value']] = label
    alias.update(
        {
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
    )
    json.dump(
        alias, dump_file,
        ensure_ascii=False, encoding='utf-8', indent=2, sort_keys=True)
    dump_file.close()

    dump_file = open('dump/sorted_players_list.json', 'w')
    dump_file = codecs.lookup('utf-8')[-1](dump_file)
    players_list = sorted([label for label in players])
    json.dump(
        players_list, dump_file,
        ensure_ascii=False, encoding='utf-8', indent=2)
    dump_file.close()


def my_fix(players):
    players[u'小谷正勝'].is_active = False
    players[u'門倉健'].is_active = False
    players[u'鶴岡賢二郎'].cname = u'靍岡 賢二郎'
    players[u'元木大介'] = player_from_dict({
        'abstract': u'元木 大介（もとき だいすけ、1971年12月30日 - ）は、大阪府豊中市出身の元プロ野球選手（内野手、外野手）。',
        'areas': [
            u'大阪府',
            u'大阪府豊中市'
        ],
        'birth_date': '1971-12-30',
        'cname': u'元木 大介',
        'college': [],
        'current_club': None,
        'highschool': [
            u'上宮中学校・高等学校'
        ],
        'is_active': False,
        'others': [],
        'pro': [
            u'読売ジャイアンツ',
        ]
    })
    players[u'板東英二'] = player_from_dict({
        'abstract': u'板東 英二（ばんどう えいじ、1940年4月5日 - ）は、日本の元プロ野球選手・野球解説者・タレント・司会者・俳優。愛称は板ちゃん（ばんちゃん）。「坂東英二」は誤記。',
        'areas': [
            u'徳島県',
            u'徳島県板野郡板東町（のちの鳴門市）'
        ],
        'birth_date': '1940-4-5',
        'cname': u'坂東 英二',
        'college': [],
        'current_club': None,
        'highschool': [
            u'徳島県立徳島商業高等学校'
        ],
        'is_active': False,
        'others': [],
        'pro': [
            u'中日ドラゴンズ',
        ]
    })


def main():
    def get_query(query):
        query = query.replace('*target_player', target_player)
        print query
        return query

    get_json(get_query(highschool_query), 'highschool_team')
    get_json(get_query(college_query), 'college_team')
    get_json(get_query(pro_query), 'pro_team')
    get_json(get_query(others_query), 'others_team')
    get_json(get_query(abstract_query), 'abstract')
    get_json(get_query(birth_query), 'birthdate')
    get_json(get_query(pref_query), 'area')
    get_json(get_query(cname_query), 'cname')
    get_json(get_query(club_query), 'club')
    get_json(highschool_alias_query, 'highschool_alias')
    #かなり修正を球団模様が変わるまで加えたので実行しない##get_json(proteam_alias_query, 'proteam_alias')
    make_data()


if __name__ == '__main__':
    main()
