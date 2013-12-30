#coding: utf-8
import os
import csv
import json
import codecs

DATA_CSV = os.path.join('data', 'KEN_ALL.CSV')

def main():
    post2pref = {}
    with open(DATA_CSV, 'r') as fp:
        for row in csv.reader(fp):
            post_number = row[2]
            pref = row[6]
            post2pref[post_number[:3]] = unicode(pref, 'cp932')
        outfile = open('data/post2pref.json', 'w')
        outfile = codecs.lookup('utf-8')[-1](outfile)
        json.dump(
            post2pref, outfile,
            ensure_ascii=False, encoding='utf-8', indent=2, sort_keys=True)
        outfile.close()

if __name__ == '__main__':
    main()