"""
Fingerprint and group the tests that resulted in differences based on the model case (for valid zone
files) as well as the unique implementations in each group from the responses.
For invalid zone files, they are already separated into different directories based on the condition
violated. Therefore, only the unique implementations in each group is used.

usage: triaging.py [-h] [-path DIRECTORY_PATH]

optional arguments:
  -h, --help            show this help message and exit
  -path DIRECTORY_PATH  The path to the directory containing Differences directory.
                        Searches recursively (default: Results/)
"""

import json
import pathlib
import sys
from argparse import SUPPRESS, ArgumentDefaultsHelpFormatter, ArgumentParser
from collections import defaultdict
from typing import Any, Dict

from Scripts.test_with_valid_zone_files import (DIFFERENCES, QUERIES,
                                                QUERY_RESPONSES)


def fingerprint_group_tests(dir_path: pathlib.Path,
                            model_cases: Dict[str, Dict[str, str]]) -> None:
    """
    Fingerprints each test with the model case if available and the unique
    implementations in each group from the responses.
    Then groups the tests with the same fingerprint and outputs the groups as
    a JSON file.

    :param dir_path: The path to the directory containing the Differences directory
    """
    # Either all the zone files that resulted in some difference have the model cases
    # or none of them have it.
    # If all of them are not True and there is a True in the list then print error
    # and return: All of them are not true - there is at least one False and there
    # is a True => some zones have model cases and some don't.
    # The only acceptable scenarios are the list being all true and all false
    difference_zones = list((dir_path / DIFFERENCES).iterdir())
    has_model_cases = [zone.stem in model_cases for zone in difference_zones]
    if not all(model_cases) and any(has_model_cases):
        sys.exit(
            f'Some of the tests have model cases and other don\'t in {dir_path}')
    vectors = defaultdict(set)
    for diff in difference_zones:
        with open(diff, 'r') as diff_fp:
            diff_json = json.load(diff_fp)
        for difference in diff_json:
            query_str = difference["Query Name"] + \
                ":" + difference["Query Type"]
            zoneid = diff.stem
            groups = difference["Groups"]
            frozen_groups = []
            for group in groups:
                servers = set(group["Server/s"].strip().split())
                if servers:
                    frozen_groups.append(frozenset(servers))
            if len(frozen_groups) > 1:
                if zoneid in model_cases:
                    test_model_case = model_cases[zoneid][query_str]
                    vectors[(test_model_case, frozenset(frozen_groups))].add(
                        (zoneid, query_str))
                else:
                    vectors[("-", frozenset(frozen_groups))
                            ].add((zoneid, query_str))
    summary = []
    keys = sorted(vectors.keys())
    output_json = defaultdict(list)
    model_cases_present = set(k[0] for k in keys)
    for model_case in model_cases_present:
        for k in keys:
            if k[0] != model_case:
                continue
            sorted_groups = sorted(k[1], key=len, reverse=True)
            json_groups = []
            groups_summary = ''
            for grp in sorted_groups:
                groups_summary += f' {{{",".join(grp)}}} '
                json_groups.append(list(grp))
            if model_case != '-':
                summary.append(
                    f'{model_case} {len(vectors[k])} {groups_summary}')
                output_json[model_case].append({
                    'Groups': json_groups,
                    'Count': len(vectors[k]),
                    'Tests': list(vectors[k])
                })
            else:
                summary.append(
                    f'{len(vectors[k])} {groups_summary}')
                output_json["Fingerprints"].append({
                    'Groups': json_groups,
                    'Count': len(vectors[k]),
                    'Tests': list(vectors[k])
                })
    output = {}# type: Dict[str, Any]
    output["Summary"] = summary
    output["Details"] = output_json
    with open(dir_path / "Fingerprints.json", 'w') as cj_fp:
        json.dump(output, cj_fp, indent=2)


def get_model_cases(dir_path: pathlib.Path) -> Dict[str, Dict[str, str]]:
    """
    Returns the Zen model case for each test if it exists.

    :param dir_path: The path to the directory containing the DIFFERENCES directory.
    """
    model_cases = defaultdict(dict) # type: Dict[str, Dict[str, str]]
    queries_dir = dir_path / QUERIES
    expected_res_dir = dir_path / QUERY_RESPONSES
    tag_dir = None
    if queries_dir.exists() and queries_dir.is_dir():
        tag_dir = queries_dir
    elif expected_res_dir.exists() and expected_res_dir.is_dir():
        tag_dir = expected_res_dir
    if isinstance(tag_dir, pathlib.Path):
        for queries_file in tag_dir.iterdir():
            with open(queries_file, 'r') as qf_fp:
                queries_info = json.load(qf_fp)
                for qinfo in queries_info:
                    if "ZenResponseTag" in qinfo:
                        query_str = qinfo["Query"]["Name"] + ":" +\
                            qinfo["Query"]["Type"]
                        model_cases[queries_file.stem][query_str] = qinfo["ZenResponseTag"]
    return model_cases


def fingerprint_group_tests_helper(input_dir: pathlib.Path) -> None:
    """

    :param input_dir: The input directory
    """
    # Exit if the inputted path does not exist or is not a directory.
    if not (input_dir.exists() or input_dir.is_dir()):
        return
    differences_dir = input_dir / DIFFERENCES
    if differences_dir.exists() and differences_dir.is_dir():
        model_cases = get_model_cases(input_dir)
        fingerprint_group_tests(input_dir, model_cases)
    else:
        if input_dir.is_dir():
            for subdir in input_dir.iterdir():
                fingerprint_group_tests_helper(subdir)


if __name__ == '__main__':
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter,
                            description='Fingerprint and group the tests that resulted in '
                            'differences based on the model case (for valid zone files) as '
                            'well as the unique implementations in each group from '
                            'the responses. For invalid zone files, they are already '
                            'separated into different directories based on the condition violated. '
                            'Therefore, only the unique implementations in each group is used.')
    parser.add_argument('-path', metavar='DIRECTORY_PATH', default=SUPPRESS,
                        help='The path to the directory containing Differences directory.'
                        ' Searches recursively (default: Results/)')
    args = parser.parse_args()
    if "path" in args:
        directory_path = pathlib.Path(args.path)
    else:
        directory_path = pathlib.Path("Results/")
    fingerprint_group_tests_helper(directory_path)
