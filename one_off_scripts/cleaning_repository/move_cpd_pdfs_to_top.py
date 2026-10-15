#! /usr/bin/env python3

"""
Moves compound objects that are really a single pdf up out of {alias}/Cpd/ into {alias}/.

A candidate is any Cpd/{pointer}.pdf whose Cpd/{pointer}/ page folder is missing or empty.
Its {pointer}.pdf, .xml, .json, _parent.xml and _parent.json are moved to the collection folder,
and its {pointer}_cpd.xml is deleted. Then any empty folders in Cpd/ are removed,
and Cpd/ itself if nothing is left in it (.DS_Store files don't count, and are deleted with the folder).

Objects are skipped if their page folder has files in it, or if a file would overwrite one
already in the collection folder.

Dry run by default; nothing is changed unless --apply is given.
Afterwards, run changing_pseudocpd_to_pdf.py to change the metadata's filetype from cpd to pdf.
"""

import os
import re
import shutil
import sys


pdf_match = re.compile(r'([0-9]+)\.pdf$')
moved_suffixes = ('.pdf', '.xml', '.json', '_parent.xml', '_parent.json')
ignored_files = {'.DS_Store'}  # don't count toward a folder being non-empty


def contents(folder):
    return set(os.listdir(folder)) - ignored_files


def find_candidates(cpd_dir, collection_dir):
    for file in sorted(os.listdir(cpd_dir)):
        match = pdf_match.match(file)
        if not match:
            continue
        pointer = match.group(1)
        page_dir = os.path.join(cpd_dir, pointer)
        if os.path.isdir(page_dir) and contents(page_dir):
            print('skipping', pointer, '- page folder is not empty')
            continue
        sources = [os.path.join(cpd_dir, f"{pointer}{suffix}") for suffix in moved_suffixes]
        sources = [source for source in sources if os.path.isfile(source)]
        clashes = [source for source in sources
                   if os.path.exists(os.path.join(collection_dir, os.path.basename(source)))]
        if clashes:
            print('skipping', pointer, '- already in collection folder:', [os.path.basename(i) for i in clashes])
            continue
        yield pointer, sources


def plan(cpd_dir, collection_dir):
    moves, deletes = [], []
    candidates = list(find_candidates(cpd_dir, collection_dir))
    for pointer, sources in candidates:
        moves += [(source, os.path.join(collection_dir, os.path.basename(source))) for source in sources]
        cpd_xml = os.path.join(cpd_dir, f"{pointer}_cpd.xml")
        if os.path.isfile(cpd_xml):
            deletes.append(cpd_xml)
    rmdirs = [os.path.join(cpd_dir, i) for i in sorted(os.listdir(cpd_dir))
              if os.path.isdir(os.path.join(cpd_dir, i)) and not contents(os.path.join(cpd_dir, i))]
    leaving = {os.path.basename(path) for path in [source for source, _ in moves] + deletes + rmdirs}
    if not contents(cpd_dir) - leaving:
        rmdirs.append(cpd_dir)
    return len(candidates), moves, deletes, rmdirs


def move_up(collection_dir, apply):
    cpd_dir = os.path.join(collection_dir, 'Cpd')
    count, moves, deletes, rmdirs = plan(cpd_dir, collection_dir)
    for source, destination in moves:
        print(source, '->', destination)
        if apply:
            shutil.move(source, destination)
    for filepath in deletes:
        print('deleting', filepath)
        if apply:
            os.remove(filepath)
    for folder in rmdirs:
        print('removing empty', folder)
        if apply:
            for file in ignored_files & set(os.listdir(folder)):
                os.remove(os.path.join(folder, file))
            os.rmdir(folder)
    verb = '' if apply else 'would be '
    print(f"\n{count} objects {verb}moved, {len(deletes)} _cpd.xml files {verb}deleted, "
          f"{len(rmdirs)} empty folders {verb}removed")
    if not apply:
        print('dry run, use --apply')


if __name__ == '__main__':
    args = [i for i in sys.argv[1:] if i != '--apply']
    try:
        collection_dir = args[0]
    except IndexError:
        print('\nChange to: "python move_cpd_pdfs_to_top.py $collection_folder [--apply]"\n\n')
        quit()
    if not os.path.isdir(os.path.join(collection_dir, 'Cpd')):
        print('no Cpd folder in', collection_dir)
        quit()
    move_up(collection_dir, '--apply' in sys.argv)
