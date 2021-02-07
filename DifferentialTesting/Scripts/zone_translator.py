#!/usr/bin/env python3

import json
import pathlib
import random
import sys
import time
from argparse import ArgumentParser


def txt_gen():
    sample_txts = []
    sample_txts.append("This_is_a_sample_text")
    sample_txts.append("This_is_a_sample_text_too")
    sample_txts.append("An_example_data_for_txt_record")
    sample_txts.append("Simple_txt_record")
    sample_txts.append("TXT")
    while True:
        for t in sample_txts:
            yield t


def ipv4_gen():
    sample_ips = ['1.1.1.1', '2.2.2.2', '3.3.3.3', '4.4.4.4', '5.5.5.5']
    while True:
        for i in sample_ips:
            yield i


def ipv6_gen():
    sample_ips = ['2400:cb00:2049:1::a29f:1804', '2001:0db8:85a3:0000:0000:8a2e:0370:7334', '0:0:0:0:0:ffff:192.1.56.10',
                  'FE80:CD00:0000:0CDE:1257:0000:211E:729C', '2001:0db8:0000:0000:0000:8a2e:0370:7334']
    while True:
        for i in sample_ips:
            yield i


def label_gen():
    labels = ["foo", "bar", "campus", "example", "com", "bankcard",
              "mybankcard", "fnni", "net", "bank", "email", "www", "uni"]
    while True:
        rand = random.sample(labels, len(labels))
        for l in rand:
            yield l


def get_domain_name(labels, label_translator, name):
    char_name = []
    for i, v in enumerate(name):
        if v == 1:
            char_name.append('*')
        else:
            if v not in label_translator[i]:
                label_translator[i][v] = next(labels[i])
            char_name.append(label_translator[i][v])
    return '.'.join(char_name[::-1])


TYPES = ['SOA', 'NS', 'A', 'CNAME', 'DNAME', 'AAAA', 'TXT', 'N']


def zone_translator(zone_json):

    records = zone_json["Zone"]["Records"]
    labels = [label_gen(), label_gen(), label_gen(),
              label_gen(), label_gen(), label_gen(),
              label_gen(), label_gen(), label_gen(), label_gen()]
    label_translator = [{}, {}, {}, {}, {}, {}, {}, {}, {}, {}]

    translated_records = []
    ipv4 = ipv4_gen()
    ipv6 = ipv6_gen()
    txts = txt_gen()

    zone_name = ''
    ns_records = []
    soa_count = 0
    for i, record in enumerate(records):
        if 0 <= record["RType"] < len(TYPES):
            rtype = TYPES[record["RType"]]
        else:
            # Bogus Type
            rtype = 'B'
        if rtype == 'N':
            continue
        rname = get_domain_name(
            labels, label_translator, record["RName"]["Value"]) + '.'
        if rtype == 'SOA':
            zone_name = rname
        elif rtype == 'TXT':
            rdata = next(txts)
        elif rtype == 'A':
            rdata = next(ipv4)
        elif rtype == 'AAAA':
            rdata = next(ipv6)
        else:
            rdata = get_domain_name(
                labels, label_translator, record["RData"]["Value"]) + '.'
        if rtype == 'NS':
            ns_records.append(i)
        if rtype != 'SOA':
            translated_records.append(
                rname + '\t' + rtype + '\t' + rdata + '\n')
        else:
            soa_count += 1

    zone_ns = False
    for i in ns_records:
        if get_domain_name(labels, label_translator, records[i]["RName"]["Value"]) + '.' == zone_name:
            zone_ns = True
            break

    # Required for BIND to accept a zone file.
    if not zone_ns:
        translated_records.append(zone_name + '\tNS\tns1.outside.edu.')

    # SOA should be first with TTL to have no errors.
    while soa_count:
        translated_records.insert(
            0, zone_name + '\t500\tSOA\tns1.outside.edu. root.campus.edu. 3 6048 86400 2419200 6048\n')
        soa_count -= 1

    return translated_records, labels, label_translator, zone_name


def zone_translator_helper(input_path):
    if path.exists():
        if path.is_dir():
            if (path / 'ZoneFiles').exists() and (path / 'ZoneFiles').is_dir():
                (path / 'TranslatedZones/').mkdir(parents=True, exist_ok=True)
                for zone in (path / 'ZoneFiles').iterdir():
                    if zone.is_file():
                        with open(zone, 'r') as f:
                            translated_records, _, _, _ = zone_translator(
                                json.load(f))
                            if len(translated_records):
                                with open(path / ('TranslatedZones/' + zone.stem + '.txt'), 'w') as wf:
                                    wf.writelines(translated_records)
                                    wf.write('\n')
                            else:
                                print(f'Records are empty for {zone}')
            else:
                for subdir in path.iterdir():
                    zone_translator_helper(subdir)


if __name__ == '__main__':
    parser = ArgumentParser(
        description='Translates zone files from Zen generated integer labels to English labels.')
    parser.add_argument('Path', metavar='DIRECTORY_PATH',
                        help='The path to the directory containing (searches recursively) ZoneFiles directory.')
    args = parser.parse_args()
    path = pathlib.Path(args.Path)
    if path.exists():
        zone_translator_helper(path)
    else:
        print(f'The input path {sys.argv[1]} does not exist.')
