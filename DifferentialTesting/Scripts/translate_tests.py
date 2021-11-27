"""
Translates valid zone files and queries with Zen generated integer labels to English labels.
Requires named-compilezone to properly format the translated zone files.
https://linux.die.net/man/8/named-compilezone

usage: translate_tests.py [-h] [-c COMPILEZONE_PATH] DIRECTORY_PATH

positional arguments:
  DIRECTORY_PATH       The path to the directory containing ZenTests
                       directory.

optional arguments:
  -h, --help           show this help message and exit
  -c COMPILEZONE_PATH  The path to the named-compilezone executable.
                        (default: system "named-compilzone" executable)
"""
#!/usr/bin/env python3

import argparse
import json
import pathlib
import subprocess
import time
from argparse import ArgumentParser, FileType
from datetime import datetime
from typing import Any, Dict, Generator, List, Set

from zone_translator import SUPPORTED_TYPES, get_domain_name, zone_translator

ZEN_TESTS = "ZenTests/"
ZONE_FILES = "ZoneFiles/"
QUERIES = "Queries/"
TESTS_INFO = "TestsTotalInfo/"


def get_domain_name_dname(labels: List[Generator[str, None, None]],
                          label_translator: List[Dict[int, str]],
                          name: List[int],
                          relevant_records: List[Dict[str, Any]]) -> str:
    """
    Returns a English domain name for the input Zen generated integer domain name
    when the domain name is generated due to DNAME rewriting in the responses.
    Since DNAME rewrites the prefix of the query, the labels at each index can not
    be translated independently in the responses. The query can be translated
    independently as Zen does single-step semantics and the target of DNAME does not the
    lookup logic.

    :param labels: List of label generators, one for each label index
    :param label_translator: List of maps for each label index from an
                                integer label to an English label
    :param name: Zen generated domain name as a list of integers
    :param relevant_records: Relevant records picked from the zone for a query
    """
    dname = None
    for record in relevant_records:
        if SUPPORTED_TYPES[record["RType"]] == 'DNAME':
            dname = record
            break
    if dname:
        dname_length = len(dname["RName"]["Value"])
        dname_result_length = tmp = len(dname["RData"]["Value"])
        i = 0
        char_name = []
        while dname_result_length:
            int_label = name[i]
            if int_label == 1:
                char_name.append('*')
            else:
                if int_label not in label_translator[i]:
                    label_translator[i][int_label] = next(labels[i])
                char_name.append(label_translator[i][int_label])
            i += 1
            dname_result_length -= 1
        while i < len(name):
            int_label = name[i]
            diff = tmp - dname_length
            if int_label == 1:
                char_name.append('*')
            else:
                if int_label not in label_translator[i - diff]:
                    label_translator[i -
                                     diff][int_label] = next(labels[i - diff])
                char_name.append(label_translator[i-diff][int_label])
            i = i + 1
        return '.'.join(char_name[::-1])
    raise ValueError(f'{datetime.now()}\tNo dname record found')


def query_response_relevant_translator(test_json: Dict[str, Any],
                                       zone: List[str],
                                       labels: List[Generator[str, None, None]],
                                       label_translator: List[Dict[int, str]],
                                       fileid: str,
                                       output_path: pathlib.Path) -> None:
    """
    Translates Zen query, relevant records and response with integers labels to English labels.
    Generates a JSON in the TESTS_INFO directory with all the test information generated from Zen
    Test generation module with English labels.
    Generates a JSON in the QUERIES directory with the translated query for use in testing.

    :param test_json: The Zen generated test in JSON format
    :param zone: The zone file as a list of resource records with English labels
    :param labels: List of label generators, one for each label index
    :param label_translator: List of maps for each label index from an
                                integer label to an English label.
    :param fileid: The unique test identifier
    :param output_path: The output parent directory path
    """
    # Zen response tags:
    # https://github.com/dns-groot/Ferret/blob/main/TestGenerator/Authoritative/Response.cs#L12-L72
    response_tags = ['E1', 'E2', 'E3', 'E4', 'W1', 'W2',
                     'W3', 'D1', 'R1', 'R2', 'REFUSED', 'SERVFAIL']
    test_info = {}  # type: Dict[str, Any]

    test_info["Zone"] = zone
    test_info["Query"] = {}
    query = test_json["Query"]
    # Translate the test query
    test_info["Query"]["Name"] = get_domain_name(
        labels, label_translator, query["QName"]["Value"]) + '.'
    test_info["Query"]["Type"] = SUPPORTED_TYPES[query["QType"]]

    test_info["Response"] = {}
    test_info["Response"]["Tag"] = response_tags[test_json["Response"]["ResTag"]]
    test_info["Response"]["Records"] = []
    for res_records in test_json["Response"]["ResRecords"]:
        record = {}
        record["Type"] = SUPPORTED_TYPES[res_records["RType"]]
        record["Name"] = get_domain_name(
            labels, label_translator, res_records["RName"]["Value"]) + '.'
        if test_info["Response"]["Tag"] == 'DQR' and record["Type"] == 'CNAME':
            record["Rdata"] = get_domain_name_dname(
                labels, label_translator, res_records["RData"]["Value"],
                test_json["Relevant"]) + '.'
        else:
            if res_records["RData"]["Value"]:
                record["Rdata"] = get_domain_name(
                    labels, label_translator, res_records["RData"]["Value"]) + '.'
        test_info["Response"]["Records"].append(record)

    test_info["Response"]["RewrittenQuery"] = {}
    test_info["Response"]["RewrittenQuery"]["HasValue"] = test_json["Response"]["RewrittenQuery"]["HasValue"]
    if test_info["Response"]["RewrittenQuery"]["HasValue"]:
        if test_info["Response"]["Tag"] == 'DQR':
            test_info["Response"]["RewrittenQuery"]["Name"] = get_domain_name_dname(
                labels,
                label_translator,
                test_json["Response"]["RewrittenQuery"]["Value"]["QName"]["Value"],
                test_json["Relevant"]) + '.'
        else:
            test_info["Response"]["RewrittenQuery"]["Name"] = get_domain_name(
                labels,
                label_translator,
                test_json["Response"]["RewrittenQuery"]["Value"]["QName"]["Value"]) + '.'
        test_info["Response"]["RewrittenQuery"]["Type"] = SUPPORTED_TYPES[test_json["Response"]
                                                                          ["RewrittenQuery"]["Value"]["QType"]]

    test_info["Relevant"] = []
    for res_records in test_json["Relevant"]:
        record = {}
        record["Type"] = SUPPORTED_TYPES[res_records["RType"]]
        record["Name"] = get_domain_name(
            labels, label_translator, res_records["RName"]["Value"]) + '.'
        if res_records["RData"]["Value"]:
            record["Rdata"] = get_domain_name(
                labels, label_translator, res_records["RData"]["Value"]) + '.'
        test_info["Relevant"].append(record)

    with open(output_path / (TESTS_INFO + fileid + '.json'), 'w') as test_info_fp:
        json.dump(test_info, test_info_fp, indent=2)
    with open(output_path / (QUERIES + fileid + '.json'), 'w') as query_fp:
        query_json = {}
        query_json["Query"] = test_info["Query"]
        query_json["ZenResponseTag"] = test_info["Response"]["Tag"]
        query_list = [query_json]
        json.dump(query_list, query_fp, indent=2)


def test_translator(test_json: Dict[str, Any], compilezone: str, fileid: str,
                    output_path: pathlib.Path, error_zone_ids: Set[str],
                    compilezone_output: Dict[str, Any]) -> None:
    """
    Translates Zen Tests to test with English labels
    Uses zone_translator.py to translate the zone file

    :param test_json: The Zen generated test in JSON format
    :param compilezone: The named-compilezone to use for formatting the translated zone files
    :param fileid: The unique test identifier
    :param output_path: The output parent directory path
    :param error_zone_ids: The set of test ids for which translation failed
    :param compilezone_output: The output from running named-compilezone on the test zone file
                                (Helpful when there is an error in the zone file)
    """
    records, labels, label_translator, zone_name = zone_translator(test_json)
    if records:
        with open(output_path / (ZONE_FILES + fileid + '.txt'), 'w') as zone_fp:
            zone_fp.writelines(records)
            zone_fp.write('\n')
        query_response_relevant_translator(
            test_json, records, labels, label_translator, fileid, output_path)
        # Overwrite the translated zone file with the named-compilezone formatted zone file
        cmd_output = subprocess.run([compilezone, '-i',
                                     'local', '-k', 'ignore', '-o',
                                     output_path /
                                     (ZONE_FILES + fileid + '.txt'), zone_name,
                                     output_path / (ZONE_FILES + fileid + '.txt')],
                                    stdout=subprocess.PIPE, check=False)
        output = cmd_output.stdout.decode("utf-8")
        if cmd_output.returncode != 0:
            error_zone_ids.add(fileid)
            compilezone_output[fileid] = output.split('\n')
        else:
            compilezone_output[fileid] = output
    else:
        print(f'{datetime.now()}\tRecords are empty for {fileid}')


def main(args: argparse.Namespace) -> None:
    """
    Main function to translate Zen Tests with integer labels to English labels.

    :param args: The input arguments
    """
    directory_path = pathlib.Path(args.Path)
    if args.c:
        compilezone = args.c.name
    else:
        compilezone = "named-compilezone"
    if directory_path.exists():
        if (directory_path / ZEN_TESTS).exists() and (directory_path / ZEN_TESTS).is_dir():
            # (path / 'TranslatedZones/').mkdir(parents=True, exist_ok=True)
            (directory_path / ZONE_FILES).mkdir(parents=True, exist_ok=True)
            (directory_path / QUERIES).mkdir(parents=True, exist_ok=True)
            (directory_path / TESTS_INFO).mkdir(parents=True, exist_ok=True)
            i = 0
            start_timer = time.time()
            intermediate_timer = time.time()
            error_zones = set()  # type: Set[str]
            compilezone_output = {}  # type: Dict[str, Any]
            for test in (directory_path / ZEN_TESTS).iterdir():
                if test.is_file():
                    with open(test, 'r') as test_fp:
                        test_translator(json.load(test_fp), compilezone, test.stem,
                                        directory_path, error_zones, compilezone_output)
                i = i + 1
                if i % 1000 == 0:
                    print(f'{datetime.now()}\tTime for translation of {i-1000} - {i} tests: '
                          f'{time.time()-intermediate_timer}s')
                    intermediate_timer = time.time()
            if error_zones:
                print(
                    f'{datetime.now()}\tErrors encountered while translation for: {error_zones}')
            with open(directory_path / 'CompileZoneOutput.json', 'w') as compile_output_fp:
                json.dump(compilezone_output, compile_output_fp, indent=2)
            print(
                f'{datetime.now()}\tTotal time for translation of {i} tests: '
                f'{time.time()-start_timer}s')
        else:
            print(
                f'{datetime.now()}\tThere is no ZenTests directory in {directory_path}')
    else:
        print(f'{datetime.now()}\tThe input path {directory_path} does not exist.')


if __name__ == '__main__':
    parser = ArgumentParser(
        description='Translates valid zone files and queries with Zen generated'
                    'integer labels to English labels.')
    parser.add_argument('Path', metavar='DIRECTORY_PATH',
                        help='The path to the directory containing ZenTests directory.')
    parser.add_argument('-c', metavar='COMPILEZONE_PATH', type=FileType('r'),
                        help='The path to the named-compilezone executable.')
    main(parser.parse_args())
