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
    with open(file_name, 'r') as f:
        file_data = f.read()
    return file_data

def write_out_file(file_name, file_data):
    with open(file_name, 'w') as f:
        f.write(file_data)

def update_uuid_dictionary(old_uuid):
    if old_new_uuids.get(old_uuid) is None:
        new_uuid = uuid.uuid4()
        old_new_uuids[old_uuid] = new_uuid

def find_replace_uuids(file_data):
    for line in file_data.split('\n'):
        match = re_uuid.search(line)
        if bool(match):
            old_uuid = match.group()
            update_uuid_dictionary(old_uuid)
            new_uuid = old_new_uuids[old_uuid]
            file_data = file_data.replace(old_uuid, str(new_uuid))
    return file_data


if __name__ == '__main__':

    args = _get_argparser()

    spinnaker_file = 'spinnaker.yaml'
    spinnaker_path = 'resources/'

    pipeline_files = ['pipeline-develop.json',
                      'pipeline-production.json',
                      'pipeline-stage.json']
    pipeline_path = 'deploy/spinnaker/'

    re_uuid = re.compile("[0-F]{8}-([0-F]{4}-){3}[0-F]{12}", re.I)

    old_new_uuids = {}

    all_files = []
    spinnaker_file = spinnaker_path + spinnaker_file
    all_files.append(spinnaker_file)

    for pipeline_file in pipeline_files:
        pipeline_file = pipeline_path + pipeline_file
        all_files.append(pipeline_file)

    file_not_found = False
    for file in all_files:
        if os.path.exists(file) is False:
            file_not_found = True
            print("Cannot find", file)
    if file_not_found:
        sys.exit(1)

    print("The following files will be searched for uuid's.\n")
    for file_name in all_files:
        print(file_name)
    print('')

    for file_name in all_files:
        file_data = read_in_file(file_name)
        updated_file_data = find_replace_uuids(file_data)
        if args.new is not None:
            updated_file_data = file_data.replace(args.current, args.new)
        if args.dryrun is False:
            write_out_file(file_name, updated_file_data)

    print("Number of unique uuid's found:", str(len(old_new_uuids)) + '\n')
    print('Old and New uuids:')
    for old_uuid, new_uuid in old_new_uuids.items():
        print(old_uuid, new_uuid)
    print('')

    if args.dryrun is True:
        print('No files changed, dryrun complete.')
        sys.exit()

    print('All files updated, done.')
