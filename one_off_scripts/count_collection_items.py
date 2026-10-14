#! /usr/bin/env python3
import os
import sys

from lxml import etree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cDM_api_calls as CdmAPI


"""
Prints the number of items in each contentDM collection ("alias"),
followed by the total number of items across all collections.
"""


def get_collections():
    coll_list_xml = ET.fromstring(CdmAPI.retrieve_collections_list().encode('utf-8'))
    collections = []
    for coll in coll_list_xml.findall('.//collection'):
        alias = coll.findtext('alias').strip('/')
        name = coll.findtext('name') or ''
        collections.append((alias, name))
    return collections


def get_item_count(alias):
    total_recs_xml = ET.fromstring(CdmAPI.retrieve_collection_total_recs(alias).encode('utf-8'))
    return int(total_recs_xml.findtext('.//total'))


def main():
    collections = get_collections()
    alias_width = max(len(alias) for alias, name in collections)
    grand_total = 0
    for alias, name in collections:
        count = get_item_count(alias)
        grand_total += count
        print('{:<{width}}  {:>8,}  {}'.format(alias, count, name, width=alias_width))
    print('-' * (alias_width + 10))
    print('{:<{width}}  {:>8,}  ({} collections)'.format('TOTAL', grand_total, len(collections), width=alias_width))


if __name__ == '__main__':
    main()
