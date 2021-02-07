#!/usr/bin/env python3

import json
import os
import pathlib
import random
import subprocess
import sys
import time
from argparse import ArgumentParser, FileType

from zone_translator import TYPES, get_domain_name, zone_translator


def get_domain_name_dname(labels, label_translator, name, relevant_records):
    dname = None
    for r in relevant_records:
        if TYPES[r["RType"]] == 'DNAME':
            dname = r
            break
    if dname:
        dname_length = len(r["RName"]["Value"])
        dname_result_length = tmp = len(r["RData"]["Value"])
        i = 0
        char_name = []
        while dname_result_length:
            v = name[i]
            if v == 1:
                char_name.append('*')
            else:
                if v not in label_translator[i]:
                    label_translator[i][v] = next(labels[i])
                char_name.append(label_translator[i][v])
            i += 1
            dname_result_length -= 1
        while i < len(name):
            v = name[i]
            diff = tmp - dname_length
            if v == 1:
                char_name.append('*')
            else:
                if v not in label_translator[i - diff]:
                    label_translator[i - diff][v] = next(labels[i - diff])
                char_name.append(label_translator[i-diff][v])
            i = i + 1
        return '.'.join(char_name[::-1])
    else:
        print(f'No dname record found')


def query_response_relevant_translator(zone_json, zone, labels, label_translator, fileid, output_path):
    response_tags = ['EAA', 'EAQ', 'EAE', 'ERE', 'WSA', 'WQR',
                     'WEA', 'DQR', 'PRE', 'PNX', 'REFUSED', 'SERVFAIL']
    translated = {}

    translated["Zone"] = zone
    translated["Query"] = {}
    query = zone_json["Query"]
    translated["Query"]["Name"] = get_domain_name(
        labels, label_translator, query["QName"]["Value"]) + '.'
    translated["Query"]["Type"] = TYPES[query["QType"]]

    translated["Response"] = {}
    translated["Response"]["Tag"] = response_tags[zone_json["Response"]["ResTag"]]
    translated["Response"]["Records"] = []
    for r in zone_json["Response"]["ResRecords"]:
        record = {}
        record["Type"] = TYPES[r["RType"]]
        record["Name"] = get_domain_name(
            labels, label_translator, r["RName"]["Value"]) + '.'
        if translated["Response"]["Tag"] == 'DQR' and record["Type"] == 'CNAME':
            record["Rdata"] = get_domain_name_dname(
                labels, label_translator, r["RData"]["Value"], zone_json["Relevant"]) + '.'
        else:
            if len(r["RData"]["Value"]):
                record["Rdata"] = get_domain_name(
                    labels, label_translator, r["RData"]["Value"]) + '.'
        translated["Response"]["Records"].append(record)
    translated["Response"]["RewrittenQuery"] = {}
    translated["Response"]["RewrittenQuery"]["HasValue"] = zone_json["Response"]["RewrittenQuery"]["HasValue"]
    if translated["Response"]["RewrittenQuery"]["HasValue"]:
        if translated["Response"]["Tag"] == 'DQR':
            translated["Response"]["RewrittenQuery"]["Name"] = get_domain_name_dname(
                labels, label_translator, zone_json["Response"]["RewrittenQuery"]["Value"]["QName"]["Value"],  zone_json["Relevant"]) + '.'
        else:
            translated["Response"]["RewrittenQuery"]["Name"] = get_domain_name(
                labels, label_translator, zone_json["Response"]["RewrittenQuery"]["Value"]["QName"]["Value"]) + '.'
        translated["Response"]["RewrittenQuery"]["Type"] = TYPES[zone_json["Response"]
                                                                 ["RewrittenQuery"]["Value"]["QType"]]

    translated["Relevant"] = []
    for r in zone_json["Relevant"]:
        record = {}
        record["Type"] = TYPES[r["RType"]]
        record["Name"] = get_domain_name(
            labels, label_translator, r["RName"]["Value"]) + '.'
        if len(r["RData"]["Value"]):
            record["Rdata"] = get_domain_name(
                labels, label_translator, r["RData"]["Value"]) + '.'
        translated["Relevant"].append(record)

    with open(output_path / ('QueryResponses/' + fileid + '.json'), 'w') as f:
        json.dump(translated, f, indent=2)


def zone_translator_compilezone(zone_json, compilezone, fileid, output_path, error_zones, compilezone_output):

    records, labels, label_translator, zone_name = zone_translator(zone_json)
    if len(records):
        with open(output_path / ('TranslatedZones/' + fileid + '.txt'), 'w') as f:
            f.writelines(records)
            f.write('\n')
        query_response_relevant_translator(
            zone_json, records, labels, label_translator, fileid, output_path)
        compilezone = subprocess.run([compilezone, '-i',
                                      'local', '-k', 'ignore', '-o', output_path / ('FormattedZones/' + fileid + '.txt'), zone_name, output_path / ('TranslatedZones/' + fileid + '.txt')], stdout=subprocess.PIPE)
        output = compilezone.stdout.decode("utf-8")
        if compilezone.returncode != 0:
            error_zones.add(fileid)
            compilezone_output[fileid] = output.split('\n')
        else:
            compilezone_output[fileid] = output
    else:
        print(f'Records are empty for {fileid}')


if __name__ == '__main__':
    parser = ArgumentParser(
        description='Translates valid zone files and queries from Zen generated integer labels to English labels.')
    parser.add_argument('Path', metavar='DIRECTORY_PATH',
                        help='The path to the directory containing LookupTests directory.')
    parser.add_argument('-c', metavar='COMPILEZONE_PATH', type=FileType('r'),
                        help='The path to the named-compilezone executable.')
    args = parser.parse_args()
    if args.c:
        compilezone = pathlib.Path(args.c.name)
    else:
        compilezone = "named-compilezone"
    path = pathlib.Path(args.Path)
    if path.exists():
        if (path / 'LookupTests').exists() and (path / 'LookupTests').is_dir():
            (path / 'TranslatedZones/').mkdir(parents=True, exist_ok=True)
            (path / 'FormattedZones/').mkdir(parents=True, exist_ok=True)
            (path / 'QueryResponses/').mkdir(parents=True, exist_ok=True)
            i = 0
            start = time.time()
            intermediate_timer = time.time()
            error_zones = set()
            compilezone_output = {}
            for zone in (path / 'LookupTests').iterdir():
                if zone.is_file():
                    with open(zone, 'r') as f:
                        zone_translator_compilezone(
                            json.load(f), compilezone, zone.stem, path, error_zones, compilezone_output)
                i = i + 1
                if i % 1000 == 0:
                    print(
                        f' Time for translation of {i-1000} - {i} tests: {time.time()-intermediate_timer}s')
                    intermediate_timer = time.time()
            print('Errors encountered while translation for:', error_zones)
            with open(path / 'CompileZoneOutput.json', 'w') as jf:
                json.dump(compilezone_output, jf, indent=2)
            print(
                f'Total time for translation of {i} tests: {time.time()-start}s')
        else:
            print(
                f'There is no LookupTests directory under the input path {path}')
    else:
        print(f'The input path {path} does not exist.')
