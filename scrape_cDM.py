#! /usr/bin/env python3

import os
import urllib
from lxml import etree as ET
import json
import logging
from dotenv import load_dotenv, find_dotenv

import cDM_api_calls as CdmAPI

load_dotenv(find_dotenv())


WE_DONT_MIGRATE = {'p16313coll70', 'p120701coll11', 'LSUHSCS_JCM', 'UNO_SCC', 'p15140coll36', 'p15140coll57',
                   'p15140coll13', 'p15140coll11', 'p16313coll32', 'p16313coll49', 'p16313coll50',
                   'p16313coll90', 'p120701coll14', 'p120701coll20', 'p120701coll21', 'DUBLIN2',
                   'HHN', 'p15140coll55', 'NOD', 'WIS', 'p16313coll55', 'LOU_RANDOM', 'p120701coll11',
                   'p16313coll67', 'AMA', 'HTU', 'p15140coll3', 'p15140coll15', 'p15140coll25',
                   'p15140coll29', 'p15140coll34', 'p15140coll37', 'p15140coll38', 'p15140coll39',
                   'p15140coll40', 'p15140coll45', 'p15140coll47', 'p15140coll58', 'p16313coll4',
                   'p16313coll6', 'p16313coll11', 'p16313coll12', 'p16313coll13', 'p16313coll14',
                   'p16313coll15', 'p16313coll16', 'p16313coll29', 'p16313coll27', 'p16313coll30',
                   'p16313coll33', 'p16313coll37', 'p16313coll38', 'p16313coll39', 'p16313coll41',
                   'p16313coll42', 'p16313coll46', 'p16313coll47', 'p16313coll53', 'p16313coll59',
                   'p16313coll63', 'p16313coll64', 'p16313coll66', 'p16313coll68', 'p16313coll71',
                   'p16313coll73', 'p16313coll75', 'p16313coll78', 'p16313coll84',
                   'p15140coll32', 'p16313coll82', 'p120701coll6', 'p267101coll4',
                   'p16313coll44', 'p16313coll88', 'p16313coll94', 'JSN', 'p15140coll24',
                   'p15140coll9', 'p15140coll59', 'p16313coll40', 'p15140coll53', 'p16313coll97',
                   'p16313coll18', 'p15140coll33', 'LST', 'MPF', 'p15140coll2', }



"""
"alias" is contentDM's term for collections.
"pointer" is contentDM's term for objects.

An alias will have pointers at its root, which may be simple or compound objects.
A compound object will have simple objects at its root.

This script outputs a collection as:
Cachec_Cdm_files-
    Alias-
        Pointer1
        Pointer2
        Pointer3-
            Pointer4
            Pointer5
        Pointer6
(where pointers 1, 2, and 6 are simple objects.  Pointers 4 and 5 are the simple object children
 of compound object pointer 3).
"""


class ScrapeAlias():
    def __init__(self, repo_dir, alias):
        self.alias = alias
        self.alias_dir = os.path.realpath(os.path.join(repo_dir, self.alias))
        self.compound_parents = []
        self.tree_snapshot = []

    def main(self):
        self.do_collection_level_metadata()
        self.do_root_level_objects()
        self.do_compound_objects()

    def do_collection_level_metadata(self):
        filepath = self.alias_dir
        os.makedirs(filepath, exist_ok=True)
        files = [i for i in os.listdir(filepath)]
        if 'Collection_TotalRecs.xml' not in files:
            CdmAPI.write_xml_to_file(
                CdmAPI.retrieve_collection_total_recs(self.alias),
                filepath,
                'Collection_TotalRecs')
            logging.info('{} Collection_TotalRecs.xml written'.format(self.alias))
        if 'Collection_Metadata.xml' not in files:
            CdmAPI.write_xml_to_file(
                CdmAPI.retrieve_collection_metadata(self.alias),
                filepath,
                'Collection_Metadata')
            logging.info('{} Collection_Metadata.xml written'.format(self.alias))
        if 'Collection_Fields.json' not in files:
            CdmAPI.write_json_to_file(
                CdmAPI.retrieve_collection_fields_json(self.alias),
                filepath,
                'Collection_Fields')
            logging.info('{} Collection_Fields.json written'.format(self.alias))
        if 'Collection_Fields.xml' not in files:
            CdmAPI.write_xml_to_file(
                CdmAPI.retrieve_collection_fields_xml(self.alias),
                filepath,
                'Collection_Fields')
            logging.info('{} Collection_Fields.xml written'.format(self.alias))

    def do_root_level_objects(self):
        chunksize = 1024
        num_chunks = self.calculate_chunks(chunksize)
        for num in range(num_chunks):
            starting_position = (num * chunksize) + 1
            if starting_position > 10001:
                starting_position = 10001
            self.write_chunk_of_elems_in_collection(starting_position, chunksize)
        self.tree_snapshot = [i for i in os.walk(self.alias_dir)]
        for pointer, filetype in self.find_root_pointers_filetypes():
            self.process_root_level_objects(pointer, filetype)

    def calculate_chunks(self, chunksize):
        num_root_objects = self.count_root_objects()
        return (num_root_objects // chunksize) + 1

    def count_root_objects(self):
        total_recs_etree = ET.parse(os.path.join(self.alias_dir, 'Collection_TotalRecs.xml'))
        this_elem = total_recs_etree.xpath('.//total')
        return int(this_elem[0].text)

    def write_chunk_of_elems_in_collection(self, starting_position, chunksize):
        filepath = self.alias_dir
        files = [i for i in os.listdir(filepath)]
        if 'Elems_in_Collection_{}.json'.format(starting_position) not in files:
            CdmAPI.write_json_to_file(
                CdmAPI.retrieve_elems_in_collection(self.alias, starting_position, chunksize, 'json'),
                filepath,
                'Elems_in_Collection_{}'.format(starting_position))
            logging.info('{} Elems_in_Collection_{}.json written'.format(self.alias, starting_position))
        if 'Elems_in_Collection_{}.xml'.format(starting_position) not in files:
            CdmAPI.write_xml_to_file(
                CdmAPI.retrieve_elems_in_collection(self.alias, starting_position, chunksize, 'xml'),
                filepath,
                'Elems_in_Collection_{}'.format(starting_position))
            logging.info('{} Elems_in_Collection_{}.xml written'.format(self.alias, starting_position))

    def find_root_pointers_filetypes(self):
        filepath = self.alias_dir
        files = [file for file in os.listdir(filepath) if 'Elems_in_Collection' in file and '.xml' in file]
        pointers_filetypes = []
        for file in files:
            elems_in_col_etree = ET.parse(os.path.join(filepath, file))
            for single_record in elems_in_col_etree.findall('.//record'):
                pointer = single_record.find('dmrecord').text or single_record.find('pointer').text
                filetype = single_record.find('filetype').text.lower()
                if pointer and filetype:
                    pointers_filetypes.append((pointer, filetype))
        return pointers_filetypes

    def process_root_level_objects(self, pointer, filetype):
        if filetype == 'cpd':
            cpd_path = os.path.join(self.alias_dir, 'Cpd')
            os.makedirs(cpd_path, exist_ok=True)
            self.write_metadata(cpd_path, pointer, 'cpd')
            self.compound_parents.append(pointer)
        else:
            self.write_metadata(self.alias_dir, pointer, 'simple')
            self.process_binary(self.alias_dir, pointer, filetype)

    def write_metadata(self, target_dir, pointer, simple_or_cpd):
        # checks presence of file before calling to contentDM or overwriting file
        # there can be up to 4000 files checked here per alias,
        # so it is useful to take a snapshot of the directory tree beforehand,
        # instead of reading from the harddrive for each file.
        files = [file for root, dirs, files in self.tree_snapshot
                 for file in files
                 if target_dir == root]

        if "{}.xml".format(pointer) not in files:
            xml_text = CdmAPI.retrieve_item_metadata(self.alias, pointer, 'xml')
            if is_it_a_404_xml(xml_text):
                logging.warning('{} {}.xml is 404'.format(self.alias, pointer))
            else:
                CdmAPI.write_xml_to_file(xml_text, target_dir, pointer)
                logging.info('{} {} xml_text written'.format(self.alias, pointer))

        if '{}.json'.format(pointer) not in files:
            json_text = CdmAPI.retrieve_item_metadata(self.alias, pointer, 'json')
            if is_it_a_404_json(json_text):
                logging.warning('{} {}.json is 404'.format(self.alias, pointer))
            else:
                CdmAPI.write_json_to_file(json_text, target_dir, pointer)
                logging.info('{} {} json_text written'.format(self.alias, pointer))

        if '{}_parent.xml'.format(pointer) not in files:
            xml_parent_text = CdmAPI.retrieve_parent_info(self.alias, pointer, 'xml')
            if is_it_a_404_xml(xml_parent_text):
                logging.warning('{} {}_parent.xml is 404'.format(self.alias, pointer))
            else:
                CdmAPI.write_xml_to_file(xml_parent_text, target_dir, '{}_parent'.format(pointer))
                logging.info('{} {} xml_parent_text written'.format(self.alias, pointer))

        if '{}_parent.json'.format(pointer) not in files:
            json_parent_text = CdmAPI.retrieve_parent_info(self.alias, pointer, 'json')
            if is_it_a_404_json(json_parent_text):
                logging.warning('{} {}_parent.json is 404'.format(self.alias, pointer))
            else:
                CdmAPI.write_json_to_file(json_parent_text, target_dir, '{}_parent'.format(pointer))
                logging.info('{} {} json_parent_text written'.format(self.alias, pointer))

        if simple_or_cpd == 'cpd':
            if '{}_cpd.xml'.format(pointer) not in files:
                index_file_text = CdmAPI.retrieve_compound_object(self.alias, pointer)
                if is_it_a_404_xml(index_file_text):
                    logging.warning('{} {}_cpd.xml is 404'.format(self.alias, pointer))
                else:
                    CdmAPI.write_xml_to_file(index_file_text, target_dir, '{}_cpd'.format(pointer))
                    logging.info('{} {} xml_index_file_text written'.format(self.alias, pointer))

    def process_binary(self, target_dir, pointer, filetype):
        files = [file for root, dirs, files in self.tree_snapshot for file in files if target_dir == root]
        if '{}.{}'.format(pointer, filetype) not in files and '{}.{}'.format(pointer, filetype.lower()) not in files:
            try:
                CdmAPI.write_binary_to_file(
                    CdmAPI.retrieve_binary(self.alias, pointer),
                    target_dir,
                    pointer,
                    filetype)
                logging.info('{} {}.{} written'.format(self.alias, pointer, filetype))
            except urllib.error.HTTPError:
                logging.warning('{} {} HTTP error caught on binary'.format(self.alias, pointer))

    def do_compound_objects(self):
        for parent_pointer in self.compound_parents:
            os.makedirs(os.path.join(self.alias_dir, 'Cpd', parent_pointer), exist_ok=True)
            self.write_child_data(parent_pointer)

    def write_child_data(self, parent_pointer):
        children_pointers_list = self.parse_children_of_cpd(parent_pointer)
        child_dir = os.path.realpath(os.path.join(self.alias_dir, 'Cpd', parent_pointer))
        if not children_pointers_list:
            logging.warning('{} no children to this compound'.format(parent_pointer))
            return None
        for child in children_pointers_list:
            child_pointer = child.text
            self.write_metadata(child_dir, child_pointer, 'simple')
            try:
                child_filetype = parse_binary_original_filetype(child_dir, child_pointer)
            except OSError:
                logging.warning('{} {} cannot parse original filetype'.format(self.alias, os.path.join(child_dir, child_pointer)))
                continue
            self.process_binary(child_dir, child_pointer, child_filetype)

    def parse_children_of_cpd(self, parent_pointer):
        index_filename = '{}_cpd.xml'.format(parent_pointer)
        index_filepath = os.path.join(self.alias_dir, 'Cpd', index_filename)
        children_pointers_list = ET.parse(index_filepath).findall('.//pageptr')
        if self.are_child_pointers_pdfpages(children_pointers_list, index_filename):
            return False
        return children_pointers_list

    def are_child_pointers_pdfpages(self, children_pointers_list, index_filename):
        if has_pdfpage_elems(children_pointers_list):
            self.try_to_get_a_hidden_pdf_at_root_of_cpd(index_filename)
            return True        # Psuedo-compound pdf object -- skip processing its children.
        return False

    def try_to_get_a_hidden_pdf_at_root_of_cpd(self, index_filename):
        filepath = os.path.join(self.alias_dir, 'Cpd')
        pointer, filetype = find_cpd_object_original_pointer_filetype(filepath, index_filename)
        sibling_files = self.find_sibling_files(index_filename)
        if '{}.{}'.format(pointer, filetype) not in sibling_files:
            binary = self.try_getting_hidden_pdf(pointer, filetype)
            if binary:
                self.write_hidden_pdf_if_a_binary(binary, filepath, pointer, filetype)

    def find_sibling_files(self, filename):
        return [file
                for root, dirs, files in self.tree_snapshot
                for file in files
                if filename in files]

    def try_getting_hidden_pdf(self, pointer, filetype):
        try:
            binary = CdmAPI.retrieve_binary(self.alias, pointer)
        except urllib.error.HTTPError:
            logging.warning('{} {} HTTP error caught on binary'.format(self.alias, pointer))
            return False
        return binary

    def write_hidden_pdf_if_a_binary(self, binary, filepath, pointer, filetype):
        # in some cases, contentDM gives an xml instead of a binary.
        # it's easier to discern whether something is an xml, than to discern
        # whether its one of millions of types of valid binaries.
        # we're going to try to decode the binary or xml into unicode.
        # if it succeeds, it's an xml & we'll discard it.
        # if it fails, it's a binary, which we'll write to file.
        try:
            binary.decode('utf-8')
            return False
        except UnicodeDecodeError:
            filetype_mapping = {
                'application/pdf': 'pdf'
            }
            print('filepath, pointer, filetype:', filepath, pointer, filetype_mapping[filetype])
            CdmAPI.write_binary_to_file(binary, filepath, pointer, filetype_mapping[filetype])
            logging.info('{} {} root hidden_pdf written'.format(filepath, pointer))
            return True


def find_cpd_object_original_pointer_filetype(filepath, index_filename):
    xml_file = "{}.xml".format(index_filename.split('_')[0])
    root_cpd_etree = ET.parse(os.path.join(filepath, xml_file))
    pointer = root_cpd_etree.find('.//dmrecord').text or root_cpd_etree.find('.//pointer').text
    filetype = root_cpd_etree.find('.//format').text
    if filetype:
        filetype = filetype.lower()
    else:
        filetype = 'pdf'
    return pointer, filetype


def is_it_a_404_xml(xml_text):
    xmldata = bytes(bytearray(xml_text, encoding='utf-8'))
    element_tree = ET.fromstring(xmldata)
    message_elem = element_tree.xpath('./message')
    if message_elem and message_elem[0].text == 'Requested item not found':
        return True
    return False


def is_it_a_404_json(json_text):
    parsed_json = json.loads(json_text)
    if 'message' in parsed_json and parsed_json['message'] == 'Requested item not found':
        return True
    return False


def has_pdfpage_elems(children_elements_list):
    file_elems = children_elements_list[0].getparent().xpath('./pagefile')
    if file_elems and 'pdfpage' in file_elems[0].text:
        return True
    return False


def parse_binary_original_filetype(folder, pointer):
    filepath = '{}.xml'.format(os.path.join(folder, pointer))
    parsed_etree = ET.parse(filepath)
    orig_name = parsed_etree.find('find').text
    filetype = os.path.splitext(orig_name)[-1].replace('.', '')
    return filetype


def do_collection(alias):
    logging.info('starting {}'.format(alias))
    scrapealias = ScrapeAlias(repo_dir, alias)
    scrapealias.main()
    logging.info('finished {}'.format(alias))


def do_repo_level_objects(repo_dir):
    os.makedirs(repo_dir, exist_ok=True)
    if not os.path.isfile(os.path.join(repo_dir, 'Collections_List.xml')):
        coll_list_txt = CdmAPI.retrieve_collections_list()
        CdmAPI.write_xml_to_file(coll_list_txt, repo_dir, 'Collections_List')
        logging.info('Collection_List.xml written')


def setup_logging():
    logging.basicConfig(filename='scrape_cDM_log.txt',
                        level=logging.INFO,
                        format='%(asctime)s: %(levelname)-8s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')
    console = logging.StreamHandler()
    console.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)


if __name__ == '__main__':
    setup_logging()
    repo_dir = os.path.join('..', 'Cached_Cdm_files')

    """ Get specific collections' metadata/binaries """

    # COLLECTION_ALIAS can be one alias or a comma-separated list
    collection_aliases = [i.strip() for i in os.environ.get('COLLECTION_ALIAS', '').split(',') if i.strip()]
    if not collection_aliases:
        raise RuntimeError('Set the COLLECTION_ALIAS environment variable, e.g. in a .env file (see README)')
    for alias in collection_aliases:
        do_collection(alias)

    """ Get all collections' metadata/binaries """

    # do_repo_level_objects(repo_dir)
    # coll_list_xml = ET.parse(os.path.join(repo_dir, 'Collections_List.xml'))
    # for alias in [alias.text.strip('/') for alias in coll_list_xml.findall('.//alias')
    #               if alias.text.strip('/') not in WE_DONT_MIGRATE]:
    #     do_collection(alias)
