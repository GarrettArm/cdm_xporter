

"""
be careful with this script.
it is intended to only be used for certain types of compound pdf collections
like some items in LSU_LNP.
If you use it against a healthy collection or a healthy part of LSU_LNP,
it will destroy your source data
"""


import json
import os
import shutil
import lxml.etree as ET


def extract_ptr_title(page_elem):
    page_dict = {elem.tag: elem.text for elem in page_elem}
    ptr, title = page_dict.get('pageptr'), page_dict.get('pagetitle')
    return ptr, title


def parse_cpd_file(filepath):
    etree = ET.parse(filepath)
    page_pointers = [i for i in etree.findall('.//page')]
    ptrs_titles = dict()
    for page in page_pointers:
        ptr, title = extract_ptr_title(page)
        if ptr in ptrs_titles:
            print('duplicate pointer', ptr)
            return
        ptrs_titles[ptr] = title
    return ptrs_titles


def gather_ptrs_titles(path):
    file_dict = dict()
    for root, dirs, files in os.walk(path):
        for file in files:
            if '_cpd.xml' in file:
                for k, v in parse_cpd_file(os.path.join(root, file)).items():
                    if file_dict.get(k):
                        print('duplicate pointer', k)
                        return
                    file_dict[k] = v
    return file_dict


def parse_json(filepath):
    with open(filepath, 'r') as f:
        cpd_metadata = json.loads(f.read())
    return cpd_metadata


def check_duplicates(cpd_metadata, page_metadata):
    for k in cpd_metadata:
        if page_metadata.get(k) and page_metadata[k] != cpd_metadata[k]:
            if k in ('title', 'fullrs', 'find', 'dmrecord', 'cdmfilesize', 'cdmfilesizeformatted'):
                continue
            print(k, '\t\t', page_metadata[k])
            return True
    else:
        return False


def merge(cpd_metadata, page_metadata):
    new_dict = dict()
    for k in cpd_metadata:
        if page_metadata.get(k):
            new_dict[k] = page_metadata[k]
        else:
            new_dict[k] = cpd_metadata[k]
    return new_dict


def process_json(cpd_subfolder):
    all_page_jsons = [
        os.path.join(root, file)
        for root, dirs, files in os.walk(cpd_subfolder)
        for file in files
        if ('.json' in file) and not('_parent.json' in file)
    ]
    for page in all_page_jsons:
        root, filename = os.path.split(page)
        cpd_root, cpd_ptr = os.path.split(root)
        collection_root, _ = os.path.split(cpd_root)
        cpd_metadata = parse_json(os.path.join(cpd_root, f"{cpd_ptr}.json"))
        ptr, _ = os.path.splitext(filename)
        merged_json = merge(cpd_metadata, parse_json(page))
        with open(os.path.join(collection_root, f"{ptr}.json"), 'w') as f:
            f.write(json.dumps(merged_json))
        shutil.move(os.path.join(root, f"{ptr}.pdf"), os.path.join(collection_root, f"{ptr}.pdf"))
        shutil.copy2(os.path.join(cpd_root, f"{cpd_ptr}_parent.json"), os.path.join(collection_root, f"{ptr}_parent.json"))
        shutil.copy2(os.path.join(cpd_root, f"{cpd_ptr}_parent.xml"), os.path.join(collection_root, f"{ptr}_parent.xml"))
    shutil.rmtree(cpd_subfolder)


def main(cpd_dir):
    for root, dirs, files in os.walk('/home/francis/Desktop/PagesToSimplesLSU_LNP/Cpd/'):
        for subdir in dirs:
            process_json(os.path.join(root, subdir))


if __name__ == "__main__":
    print('be nervous about this script\nit is intended to only be used for certain types of compound pdf collections\nlike some items in LSU_LNP.\nIf you use it against a healthy collection or a healthy part of LSU_LNP,\nit will destroy your source data')
    # main()  # accepts cpd_subfolders like:  '/home/francis/Cached_Cdm_files/LSU_LNP/Cpd/5134/'


    # all_page_jsons = [
    #     os.path.join(root, file)
    #     for root, dirs, files in os.walk('/media/francis/Storage/LNP_Source_datas/CachedCdmFiles/LSU_LNP/Cpd/5134/')
    #     for file in files
    #     if ('.json' in file) and not('_parent.json' in file)]


    # for page in all_page_jsons:
    #     check_duplicates(cpd_metadata, parse_json(page))

    # cpd_metadata = parse_json('/media/francis/Storage/LNP_Source_datas/CachedCdmFiles/LSU_LNP/Cpd/5134.json')
    # page_metadata = parse_json('/media/francis/Storage/LNP_Source_datas/CachedCdmFiles/LSU_LNP/Cpd/5134/5129.json')

    # for k, v in cpd_metadata.items():
    #     print(k, '\t\t', v)
