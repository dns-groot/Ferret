"""
Translates zone files with Zen generated integer labels to English labels.

usage: zone_translator.py [-h] DIRECTORY_PATH

positional arguments:
  DIRECTORY_PATH  The path to the directory containing (searches recursively)
                  ZenZoneFiles directory.
"""
#!/usr/bin/env python3

import json
import pathlib
import random
from argparse import ArgumentParser
from typing import Any, Dict, Generator, List, Tuple

# Same order as in
# https://github.com/dns-groot/Ferret/blob/main/TestGenerator/Authoritative/ResourceRecord.cs#L12-L52
SUPPORTED_TYPES = ['SOA', 'NS', 'A', 'CNAME', 'DNAME', 'AAAA', 'TXT', 'N']


def txt_gen() -> Generator[str, None, None]:
    """
    Returns RDATA for TXT (text) records.
    Zen generated zone files have empty RDATA for text records, which are
    filled during translation.
    """
    sample_txts = []
    sample_txts.append("This_is_a_sample_text")
    sample_txts.append("This_is_a_sample_text_too")
    sample_txts.append("An_example_data_for_txt_record")
    sample_txts.append("Simple_txt_record")
    sample_txts.append("TXT")
    while True:
        for text in sample_txts:
            yield text


def ipv4_gen() -> Generator[str, None, None]:
    """
    Returns RDATA for A (IPv4) records.
    Zen generated zone files have empty RDATA for IPv4 records, which are
    filled during translation.
    """
    sample_ips = ['1.1.1.1', '2.2.2.2', '3.3.3.3', '4.4.4.4', '5.5.5.5']
    while True:
        for i in sample_ips:
            yield i


def ipv6_gen() -> Generator[str, None, None]:
    """
    Returns RDATA for AAAA (IPv6) records.
    Zen generated zone files have empty RDATA for IPv6 records, which are
    filled during translation.
    """
    sample_ips = ['2400:cb00:2049:1::a29f:1804', '2001:0db8:85a3:0000:0000:8a2e:0370:7334',
                  '0:0:0:0:0:ffff:192.1.56.10', 'FE80:CD00:0000:0CDE:1257:0000:211E:729C',
                  '2001:0db8:0000:0000:0000:8a2e:0370:7334']
    while True:
        for i in sample_ips:
            yield i


def label_gen() -> Generator[str, None, None]:
    """
    Returns a random English label from the list of labels.
    Zen generated zone files have integers instead of string labels for a domain name.
    The integer labels are mapped to the following list of English labels.
    """
    labels = ["foo", "bar", "campus", "example", "com", "bankcard",
              "mybankcard", "fnni", "net", "bank", "email", "www", "uni"]
    while True:
        rand = random.sample(labels, len(labels))
        for i in rand:
            yield i


def get_domain_name(labels: List[Generator[str, None, None]],
                    label_translator: List[Dict[int, str]], name: List[int]) -> str:
    """
    Returns a English domain name for the input Zen generated integer domain name.

    :param labels: List of label generators, one for each label index
    :param label_translator: List of maps for each label index from an
                                integer label to an English label.
    :param name: Zen generated domain name as a list of integers
    """
    english_name = []
    for index, integer_label in enumerate(name):
        # If integer label is 1, then it is a wildcard label
        if integer_label == 1:
            english_name.append('*')
        else:
            if integer_label not in label_translator[index]:
                label_translator[index][integer_label] = next(labels[index])
            english_name.append(label_translator[index][integer_label])
    # Zen generated domain names are in reverse order.
    # https://github.com/dns-groot/Ferret/blob/main/TestGenerator/Authoritative/DomainName.cs#L15-L17
    return '.'.join(english_name[::-1])


def zone_translator(zone_json: Dict[str, Any]) -> Tuple[List[str],
                                                        List[Generator[str,
                                                                       None, None]],
                                                        List[Dict[int, str]],
                                                        str]:
    """
    Translates a Zen generated zone file to one with English labels.

    :param zone_json: Zen generated zone file in JSON format.

    Returns the translated zone file as a list of resource records along with
    the integer to label maps to translate Zen generated queries in case of
    ValidZoneFileTests.
    """
    records = zone_json["Zone"]["Records"]
    # The maximum labels in a domain name is taken as 10.
    # Therefore, there are 10 label generators and 10
    # maps that store mapping from integer label to string label.
    labels = [label_gen(), label_gen(), label_gen(),
              label_gen(), label_gen(), label_gen(),
              label_gen(), label_gen(), label_gen(), label_gen()]
    label_translator = [{}, {}, {}, {}, {}, {}, {},
                        {}, {}, {}]  # type: List[Dict[int, str]]

    translated_records = []
    ipv4 = ipv4_gen()
    ipv6 = ipv6_gen()
    txts = txt_gen()

    zone_name = ''
    ns_records = []
    soa_count = 0
    for i, record in enumerate(records):
        if 0 <= record["RType"] < len(SUPPORTED_TYPES):
            rtype = SUPPORTED_TYPES[record["RType"]]
        else:
            # Bogus Type
            rtype = 'B'
        #  Empty Non-Terminal
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

    # Check if there is an NS record for the zone
    zone_ns = False
    for i in ns_records:
        if get_domain_name(labels, label_translator,
                           records[i]["RName"]["Value"]) + '.' == zone_name:
            zone_ns = True
            break

    # Add a dummy nameserver at the origin.
    # Required for nameservers to accept a zone file.
    if not zone_ns and zone_name:
        translated_records.append(zone_name + '\tNS\tns1.outside.edu.')

    # SOA should be first with TTL to have no errors.
    while soa_count:
        translated_records.insert(
            0, zone_name + '\t500\tSOA\tns1.outside.edu. root.campus.edu. '
                           '3 6048 86400 2419200 6048\n')
        soa_count -= 1

    return translated_records, labels, label_translator, zone_name


def zone_translator_helper(input_dir: pathlib.Path) -> None:
    """
    Helper function to translate Zen generated zone files with integer labels
    to English labels. Iterates recursively over the input directory to find
    ZenZoneFiles directory and calls zone_translator function to translate each
    zone file in that directory.

    :param input_dir: The path to the parent directory with ZenZoneFiles.
    """
    # Exit if the inputted path does not exist or is not a directory.
    if not (input_dir.exists() or input_dir.is_dir()):
        return
    input_zone_files_dir = input_dir / 'ZenZoneFiles'
    output_zone_file_dir = input_dir / 'ZoneFiles/'
    if input_zone_files_dir.exists() and input_zone_files_dir.is_dir():
        output_zone_file_dir.mkdir(parents=True, exist_ok=True)
        for zone_path in input_zone_files_dir.iterdir():
            if not zone_path.is_file():
                continue
            with open(zone_path, 'r') as zone_fp:
                translated_records, _, _, _ = zone_translator(
                    json.load(zone_fp))
                if translated_records:
                    with open(output_zone_file_dir / (zone_path.stem + '.txt'), 'w') as write_fp:
                        write_fp.writelines(translated_records)
                        write_fp.write('\n')
                else:
                    print(f'Records are empty for {zone_path}')
    else:
        if input_dir.is_dir():
            for subdir in input_dir.iterdir():
                zone_translator_helper(subdir)


if __name__ == '__main__':
    parser = ArgumentParser(
        description='Translates zone files with Zen generated integer labels to English labels.')
    parser.add_argument('Path', metavar='DIRECTORY_PATH',
                        help='The path to the directory containing (searches '
                        'recursively) ZenZoneFiles directory.')
    args = parser.parse_args()
    input_path = pathlib.Path(args.Path)
    if input_path.exists():
        zone_translator_helper(input_path)
    else:
        print(f'The input path {input_path} does not exist.')
