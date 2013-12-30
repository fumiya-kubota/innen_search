#coding: utf-8
from SPARQLWrapper import SPARQLWrapper, JSON
import json
import codecs
from collections import defaultdict


def data_arrange(data):
    numbers = frozenset(['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'])
    name2pref = {}
    post2pref = json.load(open('data/post2pref.json', 'r'))

    for idx in xrange(len(data)):
        row = data[idx]
        code = row['code']['value']
        name = row['team_label']['value']
        abst = row['abst']['value']
        code = ''.join([c for c in code if c in numbers])[:3]
        if code in post2pref:
            name2pref[name] = (post2pref[code], abst)
        else:
            print name
    return name2pref


def get_data(query):
    sparql = SPARQLWrapper('http://ja.dbpedia.org/sparql')
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    data = results['results']['bindings']
    return data

def make_json(data, file_name):
    outfile = open('data/{}.json'.format(file_name), 'w')
    outfile = codecs.lookup('utf-8')[-1](outfile)
    json.dump(
        data, outfile,
        ensure_ascii=False, encoding='utf-8', indent=2, sort_keys=True)


highschool_pref_query = u'''
    PREFIX dbp-owl: <http://dbpedia.org/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX dbpprop-ja: <http://ja.dbpedia.org/property/>

    select distinct ?team_label ?abst ?code
    where {
        ?team dbpprop-ja:wikiPageUsesTemplate <http://ja.dbpedia.org/resource/Template:日本の高等学校> ;
            rdfs:label ?team_label ;
            dbp-owl:abstract ?abst ;
            dbp-owl:postalCode ?code .
    }
'''

def main():
    data = get_data(highschool_pref_query)
    data = data_arrange(data)
    make_json(data, 'highschool_pref')


if __name__ == '__main__':
    main()
