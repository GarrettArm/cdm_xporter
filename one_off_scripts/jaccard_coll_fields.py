#! /usr/bin/env python3

import os
from pathlib import Path
import xml.etree.ElementTree as ET
import itertools
import csv

from owner_col import owner_col_dict


def make_alias_terms_set():
    dict_a = dict()
    coll_dir = Path(os.getcwd()).parent.joinpath('Collections')
    for alias_dir in (x for x in coll_dir.iterdir() if x.is_dir()):
        alias = alias_dir.stem
        if alias in ('DUBLIN2', 'p15140coll57', 'p16313coll49', 'WIS'):
            continue  # ignore collections slated for deletion
        if alias in ('LST', 'p15140coll11', 'p16313coll61', 'p16313coll67', 'p16313coll87', 'p16313coll90', 'p16313coll98', 'p120701coll11', 'p120701coll14'):
            continue  # ignore collection with no objects
        if alias in owner_col_dict['Tulane']:
            print(alias, "tulane")
            continue  # ignore Tulane collections
        for filepath in (x for x in alias_dir.iterdir() if x.name == 'Collection_Fields.xml'):
            with open(str(filepath), 'r') as f:
                xmltext = f.read()
                etree = ET.fromstring(xmltext)
                alias_name_set = set()
                for name in etree.iterfind('.//name'):
                    alias_name_set.add(name.text)
                dict_a[alias] = alias_name_set
    return dict_a


def jaccard_sim(set_x, set_y):
    intersect = len(set_x & set_y)
    union = len(set_x | set_y)
    if union == 0:
        return 0
    return intersect/union


coll_tags_dict = make_alias_terms_set()

with open('jaccard_collections.csv', 'w') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    for i in itertools.combinations(coll_tags_dict, 2):
        csvwriter.writerow((i[0], i[1], str(jaccard_sim(coll_tags_dict[i[0]], coll_tags_dict[i[1]]))))
