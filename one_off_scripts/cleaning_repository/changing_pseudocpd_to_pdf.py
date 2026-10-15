#! /usr/bin/env python3

import argparse
import os
import re
import json
from lxml import etree as ET

file_match = re.compile(r'[0-9]+\.(xml|json)')
filetype_match = re.compile(r'([0-9]+)\.cpd')

parser = argparse.ArgumentParser(description='Changes cpd objects that have a {pointer}.pdf in source_dir into pdf objects')
parser.add_argument('source_dir', help='collection folder, e.g. Cached_Cdm_files/p17190coll7')
source_dir = parser.parse_args().source_dir
starting_file_list = [file for file in os.listdir(source_dir) if (file_match.match(file)) or ('Elems_in' in file)]
subfolder = [file for file in os.listdir(source_dir) if os.path.isdir(os.path.join(source_dir, file))]
full_dir = [file for file in os.listdir(source_dir)]


for file in starting_file_list:
    if "Elems_in_" in file:
        if '.xml' in file:
            elems_etree = ET.parse(os.path.join(source_dir, file))
            for elem in elems_etree.findall('.//record'):
                pointer = [i.text for i in elem if i.tag == 'pointer']
                filename = [i for i in elem if i.tag == 'find']
                filetype = [i for i in elem if i.tag == 'filetype']
                if pointer and filename:
                    pointer, filename, filetype = pointer[0], filename[0], filetype[0]
                if '{}.pdf'.format(pointer) in full_dir:
                    filename.text = '{}.pdf'.format(pointer)
                    filetype.text = 'pdf'
            print(file, 'elems in collection wrote')
            elems_etree.write(os.path.join(source_dir, file), pretty_print=True)
        if '.json' in file:
            with open(os.path.join(source_dir, file), 'r') as f:
                parsed_json = json.loads(f.read())
            for elem in parsed_json['records']:
                pointer, filename, filetype = elem['pointer'], elem['find'], elem['filetype']
                if '{}.pdf'.format(pointer) in full_dir:
                    elem['find'] = '{}.pdf'.format(pointer)
                    elem['filetype'] = 'pdf'
            with open(os.path.join(source_dir, file), 'w') as f:
                print(file, 'json elems wrotten')
                json.dump(parsed_json, f)
        continue


    if "{}.pdf".format(file.split('.')[0]) not in full_dir:
        continue

    with open('{}/{}'.format(source_dir, file), 'r') as f:
        file_text = f.read()

    match = filetype_match.search(file_text)
    while match:
        file_text = file_text.replace(match.group(), "{}.pdf".format(match.group(1)))
        match = filetype_match.search(file_text)

    while "<filetype><![CDATA[cpd]]></filetype>" in file_text:
        print(file)
        print('entered_loop')
        file_text = file_text.replace("<filetype><![CDATA[cpd]]></filetype>", '<filetype><![CDATA[pdf]]></filetype>')

    while '"filetype":"cpd",' in file_text:
        print(file)
        print('json loop')
        file_text = file_text.replace('"filetype":"cpd",', '"filetype":"pdf",')

    with open(os.path.join(source_dir, file), 'w') as f:
        print(file, 'normal file written')
        f.write(file_text)
