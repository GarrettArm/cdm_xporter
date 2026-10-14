#! /usr/bin/env python3

import os
import lxml.etree as etree
import urllib.request

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


def list_alias_cmp_types(alias):

    alias_dir = os.path.join(os.pardir, os.pardir, 'Cached_Cdm_files', alias, 'Cpd')
    if not os.path.isdir(alias_dir):
        return []
    cpd_files = [i for i in os.listdir(alias_dir) if '_cpd.xml' in i]
    cpdpointers_and_type = dict()
    for cpd_file in cpd_files:
        cpd_etree = etree.parse('{}/{}'.format(alias_dir, cpd_file))
        cpd_type = cpd_etree.find('.//type').text
        if cpd_type in cpdpointers_and_type:
            cpdpointers_and_type[cpd_type].append(cpd_file.strip('_cpd.xml'))
        else:
            cpdpointers_and_type[cpd_type] = [cpd_file.strip('_cpd.xml'), ]
    return cpdpointers_and_type


def list_all_aliases():
    url = 'https://{}.contentdm.oclc.org/dmwebservices/index.php?q=dmGetCollectionList/xml'.format(
        os.environ['CDM_API_SERVER'])
    with urllib.request.urlopen(url) as response:
        coll_list_etree = etree.parse(response)
    return [i.text.strip('/') for i in coll_list_etree.findall('.//alias')]


if __name__ == '__main__':
    repo_dict_cpd_objs = dict()
    alias_list = list_all_aliases()
    for alias in alias_list:
        alias_cpd_dict = list_alias_cmp_types(alias)
        if alias_cpd_dict:
            repo_dict_cpd_objs[alias] = alias_cpd_dict
    repo_cpd_objs_table = ''
    for alias in repo_dict_cpd_objs.keys():
        for cpdtype in repo_dict_cpd_objs[alias].keys():
            pointers = ', '.join(i for i in repo_dict_cpd_objs[alias][cpdtype])
            repo_cpd_objs_table += ('{}\n{}\n{}\n\n'.format(alias, cpdtype, pointers))
    with open('cpd_types.txt', 'w') as f:
        f.write(repo_cpd_objs_table)
