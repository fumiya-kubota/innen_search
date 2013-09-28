#coding: utf-8
from SPARQLWrapper import SPARQLWrapper, JSON
import re
from datetime import datetime
from collections import defaultdict
import json
import codecs
import os
from player import Player

DATE_REGX = re.compile(ur'\d{4}年\d{1,2}月\d{1,2}日')
NENGO_REGX = re.compile(ur'[（\(]..\d{1,2}年[）\)]')
YEAR_REGX = re.compile(ur'\d{4}年')

nums = frozenset(map(str, xrange(10)))

data_dir = 'data'


def parse_date(birthdate):
    date = datetime.strptime(birthdate, '%Y-%m-%d')
    return str(date.year - 1) if 1 <= date.month <= 3 else str(date.year)


#例1清水 宏員（しみず ひろかず、1933年4月14日 - ）は、日本のプロ野球選手（投手）。
#例2新庄 剛志（しんじょう つよし、1972年（昭和47年）1月28日 - ）
def parse_abstract(abstract):
    #例2のような年号を取り除く
    n = NENGO_REGX.search(abstract)
    if n:
        b = n.start(), n.end()
        abstract = abstract.replace(abstract[b[0]:b[1]], '')
    match = DATE_REGX.search(abstract)
    if match:
        date = match.group(0)
        date = ''.join([d if d in nums else '-' for d in date[:-1]])
        date = datetime.strptime(date, '%Y-%m-%d')
        return str(date.year - 1) if 1 <= date.month <= 3 else str(date.year)

    match = YEAR_REGX.search(abstract)
    if match:
        date = match.group(0)
        return date[:4]

def label_common(label):
    #ラベルでも(野球)は辞書内で重複する可能性はないので取り除く
    if label.endswith(u' (野球)'):
        return label[:-5]
    return label

def build_data():
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

    club = {}
    filename = os.path.join(data_dir, 'club.json')
    with open(filename) as fp:
        club_data = json.load(fp)
    birthdate = defaultdict(set)
    for data in club_data:
        label = label_common(data['label']['value'])
        club[label] = data['club_label']['value']

    teams = defaultdict(set)
    for category in ('highschool', 'pro', 'others'):
        filename = os.path.join(data_dir, '{}_team.json'.format(category))
        with open(filename) as fp:
            teams_data = json.load(fp)
        for data in teams_data:
            label = label_common(data['label']['value'])
            teamname = data['team_label']['value']
            player = players[label]
            getattr(player, category).add(teamname)
            teams[teamname].add(label)
            player.cname = cname.get(label, label)
            player.club = club.get(label)

    COLLEGE = {
        u'東京農業大学北海道オホーツク硬式野球部': u'東京農業大学北海道',
        u'慶應義塾体育会野球部': u'慶應義塾大学',
        u'早稲田大学野球部': u'早稲田大学',
        u'同志社大学体育会硬式野球部': u'同志社大学',
        u'法政大学野球部': u'法政大学',
        u'近畿大学体育会硬式野球部': u'近畿大学'
    }
    filename = os.path.join(data_dir, 'college_team.json')
    with open(filename) as fp:
        college_data = json.load(fp)
    for data in college_data:
        label = label_common(data['label']['value'])
        teamname = data['team_label']['value']
        player = players[label]
        teamname = COLLEGE.get(teamname, teamname)
        if teamname.endswith(u'硬式野球部'):
            teamname = teamname[:-5]
        player.cname = cname.get(label, label)
        teams[teamname].add(label)
        player.college.add(teamname)

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
        year = parse_date(birth)
        player.set_year(year)
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
            year = parse_abstract(abstract)
            if year:
                player.set_year(year)
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

    return dict(players), dict(teams), dict(birthdate), dict(areas)


target_player = u'''
        #対象は日本人の野球選手
        {
            ?person dcterms:subject <http://ja.dbpedia.org/resource/Category:日本の野球選手> .
        } union {
            ?person dcterms:subject <http://ja.dbpedia.org/resource/Category:MLBの日本人選手> .
        } union {
            ?person dcterms:subject <http://ja.dbpedia.org/resource/Category:在日外国人の野球選手> .
        }'''

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

    select distinct ?label ?team_label
    where {
        *target_player

        ?person rdfs:label ?label ;
            dbp-owl:team ?team.
        {
            ?team dbp-owl:wikiPageRedirects ?redirects .
            ?redirects dcterms:subject ?category .
            ?category rdfs:label ?category_label .
            FILTER regex(?category_label, "大学")
            ?redirects rdfs:label ?team_label .
            FILTER NOT EXISTS {
                ?redirects dcterms:subject <http://ja.dbpedia.org/resource/Category:アマチュア野球チーム> .
            }
            FILTER NOT EXISTS {
                ?redirects dbpprop-ja:wikiPageUsesTemplate <http://ja.dbpedia.org/resource/Template:日本の高等学校> .
            }
        } union {
            ?team dcterms:subject ?category .
            ?category rdfs:label ?category_label .
            FILTER regex(?category_label, "大学")
            ?team rdfs:label ?team_label .
            FILTER NOT EXISTS {
                ?team dcterms:subject <http://ja.dbpedia.org/resource/Category:アマチュア野球チーム> .
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

        ?team rdfs:label ?team_label .
        FILTER NOT EXISTS {
            ?team dbp-owl:wikiPageRedirects ?redirects .
            ?redirects dbpprop-ja:wikiPageUsesTemplate <http://ja.dbpedia.org/resource/Template:日本の高等学校> .
        }
        FILTER NOT EXISTS {
            ?team dbpprop-ja:wikiPageUsesTemplate <http://ja.dbpedia.org/resource/Template:日本の高等学校> .
        }
        FILTER NOT EXISTS {
            ?team dbp-owl:wikiPageRedirects ?redirects__ .
            <http://ja.dbpedia.org/resource/プロ野球チーム一覧> dbp-owl:wikiPageWikiLink ?redirects__ .
        }
        FILTER NOT EXISTS {
            <http://ja.dbpedia.org/resource/プロ野球チーム一覧> dbp-owl:wikiPageWikiLink ?team .
        }

        FILTER NOT EXISTS {
            ?team dbp-owl:wikiPageRedirects ?redirects_ .
            ?redirects_ dcterms:subject ?category_ .
            ?category_ rdfs:label ?category_label_ .
            FILTER regex(?category_label_, "大学")
        }
        FILTER NOT EXISTS {
            ?team dcterms:subject ?category .
            ?category rdfs:label ?category_label .
            FILTER regex(?category_label, "大学")
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

    select distinct ?label ?club_label
    where {
        *target_player

        ?person rdfs:label ?label ;
            dbp-owl:club ?club .

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


def get_json(query, file_name):
    sparql = SPARQLWrapper("http://ja.dbpedia.org/sparql")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    outfile = open('data/{}.json'.format(file_name), 'w')
    outfile = codecs.lookup('utf-8')[-1](outfile)
    json.dump(
        results["results"]["bindings"], outfile,
        ensure_ascii=False, encoding='utf-8', indent=2, sort_keys=True)


def main():
    def get_query(query):
        query = query.replace('*target_player', target_player)
        print query
        return query

    #get_json(get_query(highschool_query), 'highschool_team')
    #get_json(get_query(college_query), 'college_team')
    #get_json(get_query(pro_query), 'pro_team')
    #get_json(get_query(others_query), 'others_team')
    #get_json(get_query(abstract_query), 'abstract')
    #get_json(get_query(birth_query), 'birthdate')
    #get_json(get_query(pref_query), 'area')
    #get_json(get_query(cname_query), 'cname')
    #get_json(get_query(club_query), 'club')

if __name__ == '__main__':
    main()
