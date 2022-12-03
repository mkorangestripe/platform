#!/usr/bin/env python3

"""
This script replaces uuid's in the given files with new uuid's.
Multiple occurrences of a unique uuid will be replaced with the same new uuid.
Optionally the application name can also be replaced with a new name.
"""

import os
import re
import sys
import uuid
from argparse import ArgumentParser


def _get_argparser():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--dryrun", action="store_true",
                        help="find all occurrences of uuid's and optionally application name, print example output, do not write to file")
    update_app_name = parser.add_argument_group('update app name', 'optional arguments but must be used together')
    update_app_name.add_argument('--current', help='current app name')
    update_app_name.add_argument('--new', help='new app name')
    args = parser.parse_args()
    if args.current is not None and args.new is None:
        print("Arguments 'current' and 'new' must be used together.")
        sys.exit(1)
    if args.current is None and args.new is not None:
        print("Arguments 'current' and 'new' must be used together.")
        sys.exit(1)
    return args

def read_in_file(file_name):
    """Read in file"""
    with open(file_name, 'r', encoding="utf-8") as in_file:
        file_data = in_file.read()
    return file_data

def write_out_file(file_name, file_data):
    """Write out file"""
    with open(file_name, 'w', encoding="utf-8") as out_file:
        out_file.write(file_data)

def update_uuid_dictionary(old_uuid):
    """Update UUID dictionary"""
    if old_new_uuids.get(old_uuid) is None:
        new_uuid = uuid.uuid4()
        old_new_uuids[old_uuid] = new_uuid

def find_replace_uuids(file_data):
    """Find and replace UUIDs"""
    for line in file_data.split('\n'):
        match = re_uuid.search(line)
        if bool(match):
            old_uuid = match.group()
            update_uuid_dictionary(old_uuid)
            new_uuid = old_new_uuids[old_uuid]
            file_data = file_data.replace(old_uuid, str(new_uuid))
    return file_data


if __name__ == '__main__':

    parsed_args = _get_argparser()

    SPINNAKER_FILE = 'spinnaker.yaml'
    SPINNAKER_PATH = 'resources/'

    pipeline_files = ['pipeline-develop.json',
                      'pipeline-production.json',
                      'pipeline-stage.json']
    PIPELINE_PATH = 'deploy/spinnaker/'

    re_uuid = re.compile("[0-F]{8}-([0-F]{4}-){3}[0-F]{12}", re.I)

    old_new_uuids = {}

    all_files = []
    SPINNAKER_FILE = SPINNAKER_PATH + SPINNAKER_FILE
    all_files.append(SPINNAKER_FILE)

    for pipeline_file in pipeline_files:
        PIPELINE_FILE_PATH = PIPELINE_PATH + pipeline_file
        all_files.append(PIPELINE_FILE_PATH)

    FILE_NOT_FOUND = False
    for file in all_files:
        if os.path.exists(file) is False:
            FILE_NOT_FOUND = True
            print("Cannot find", file)
    if FILE_NOT_FOUND:
        sys.exit(1)

    print("The following files will be searched for uuid's.\n")
    for file in all_files:
        print(file)
    print('')

    for file in all_files:
        file_content = read_in_file(file)
        updated_file_content = find_replace_uuids(file_content)
        if parsed_args.new is not None:
            updated_file_content = file_content.replace(parsed_args.current, parsed_args.new)
        if parsed_args.dryrun is False:
            write_out_file(file, updated_file_content)

    print("Number of unique uuid's found:", str(len(old_new_uuids)) + '\n')
    print('Old and New uuids:')
    for old_uuid_item, new_uuid_item in old_new_uuids.items():
        print(old_uuid_item, new_uuid_item)
    print('')

    if parsed_args.dryrun is True:
        print('No files changed, dryrun complete.')
        sys.exit()

    print('All files updated, done.')
