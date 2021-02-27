#!/usr/bin/env python3

import copy
import json
import os
import pathlib
import subprocess
import sys
import time
from argparse import (SUPPRESS, ArgumentDefaultsHelpFormatter, ArgumentParser,
                      ArgumentTypeError, FileType)
from multiprocessing import Process

import dns.query
import dns.rdataclass
import dns.rdatatype
import dns.resolver
from Implementations.Bind.prepare import run as bind
from Implementations.Coredns.prepare import run as coredns
from Implementations.Knot.prepare import run as knot
from Implementations.Maradns.prepare import run as maradns
from Implementations.Nsd.prepare import run as nsd
from Implementations.Powerdns.prepare import run as powerdns
from Implementations.Trustdns.prepare import run as trustdns
from Implementations.Yadifa.prepare import run as yadifa


def get_ports(args):
    implementations = {}
    implementations['bind'] = (not args.b, 8000)
    implementations['nsd'] = (not args.n, 8100)
    implementations['knot'] = (not args.k, 8200)
    implementations['powerdns'] = (not args.p, 8300)
    implementations['yadifa'] = (not args.y, 8400)
    implementations['coredns'] = (not args.c, 8500)
    implementations['maradns'] = (not args.m, 8600)
    implementations['trustdns'] = (not args.t, 8700)
    return implementations


def stop_container(cid):
    cmds = ["_bind_server", "_nsd_server", "_knot_server", "_powerdns_server",
            "_maradns_server", "_yadifa_server",  "_trustdns_server", "_coredns_server"]
    for cmd in cmds:
        subprocess.run(['docker', 'container', 'rm', str(cid) + cmd, '-f'],
                       stdout=subprocess.PIPE)


def start_containers(cid, implementations):
    stop_container(cid)
    for impl, (check, port) in implementations.items():
        if check:
            subprocess.run(['docker', 'run', '-dp', str(port * int(cid))+':53/udp',
                            '--name=' + str(cid) + '_' + impl + '_server', impl])


def querier(query_name, query_type, port):
    domain = dns.name.from_text(query_name)
    addr = '127.0.0.1'
    try:
        query = dns.message.make_query(domain, query_type)
        # Removes the default Recursion Desired Flag
        query.flags = 0
        result = dns.query.udp(query, addr, 3, port=port)
        return result
    except dns.exception.Timeout:
        return "No response"
    except:
        return f'Unexpected error {sys.exc_info()[1]}'
    return "Error"


def response_equality_check(response_a, response_b):
    if type(response_a) != type(response_b):
        return False
    if type(response_a) is str:
        return response_a == response_b
    if response_a.rcode() != response_b.rcode():
        return False
    a_flags = dns.flags.to_text(response_a.flags).split()
    if 'RA' in a_flags:
        a_flags.remove('RA')
    b_flags = dns.flags.to_text(response_b.flags).split()
    if 'RA' in b_flags:
        b_flags.remove('RA')
    if a_flags != b_flags:
        return False

    def check_section(section_a, section_b):
        for n in section_a:
            if n not in section_b:
                return False
        for n in section_b:
            if n not in section_a:
                return False
        return True

    if check_section(response_a.question,  response_b.question) == False:
        return False
    if check_section(response_a.answer,  response_b.answer) == False:
        return False
    if check_section(response_a.additional,  response_b.additional) == False:
        return False
    if not(len(response_a.answer) and len(response_b.answer)):
        return check_section(response_a.authority,  response_b.authority)
    return True


def group_response(responses):
    groups = []
    for response in responses:
        found = False
        for group in groups:
            if response_equality_check(group[0][1], response[1]):
                group.append(response)
                found = True
                break
        if not found:
            groups.append([response])
    return groups


def groups_to_string(groups):
    tmp = []
    for g in groups:
        servers = ""
        for server in g:
            servers += server[0] + " "
        group = {}
        group["Server/s"] = servers
        group["Response"] = g[0][1] if type(
            g[0][1]) == str else g[0][1].to_text().split('\n')
        tmp.append(group)
    return tmp


def prepare_containers(zone_file, zone_domain, cid, restart, args):
    processPool = []
    for impl, (check, port) in args.items():
        if check:
            processPool.append(
                Process(target=globals()[impl], args=(zone_file, zone_domain, str(cid) + '_' + impl + '_server', port*int(cid), restart)))
    for t in processPool:
        t.start()
    for t in processPool:
        t.join()


def run_test(zoneid, directory_path, errors, cid, ports, log):
    has_dname = False
    zone_domain = ''
    with open(directory_path / "FormattedZones" / (zoneid + '.txt'), 'r') as z:
        for line in z:
            if 'SOA' in line:
                zone_domain = line.split('\t')[0]
            if 'DNAME' in line:
                has_dname = True
    if not len(zone_domain):
        log.write(f'SOA not found in {zoneid}')
        errors[zoneid] = 'SOA not found'
        return
    implementations = copy.deepcopy(ports)
    if has_dname:
        implementations['yadifa'] = (
            False, implementations['yadifa'][1])  # Yadifa
        implementations['trustdns'] = (
            False, implementations['trustdns'])    # TrustDns
        implementations['maradns'] = (
            False, implementations['maradns'])    # MaraDns
    if not (directory_path / "QueryResponses" / (zoneid + '.json')).exists():
        log.write(
            f'No corresponding file in QueryResponses folder for {zoneid}')
        errors[zoneid] = 'No corresponding file in QueryResponses folder'
        return

    prepare_containers(directory_path / "FormattedZones" /
                       (zoneid + '.txt'), zone_domain, cid, False, implementations)

    queries = []
    with open(directory_path / "QueryResponses" / (zoneid + '.json'), 'r') as f:
        data = json.load(f)
        if 'Query' in data:
            queries.append((data['Query']['Name'], data['Query']['Type']))
        elif 'Queries' in data:
            for q in data['Queries']:
                queries.append((q['Name'], q['Type']))

    differences = []
    for qname, qtype in queries:
        responses = []
        for impl, (check, port) in implementations.items():
            if check:
                respo = querier(qname, qtype, port * int(cid))
                if not isinstance(respo, dns.message.Message):
                    single_impl = {}
                    single_impl[impl] = (True, port * int(cid))
                    prepare_containers(directory_path / "FormattedZones" /
                                       (zoneid + '.txt'), zone_domain, cid, True, single_impl)
                    time.sleep(1)
                    respo = querier(qname, qtype, port * int(cid))
                responses.append((impl, respo))
        groups = group_response(responses)
        if len(groups) > 1:
            difference = {}
            difference["Query Name"] = qname
            difference["Query Type"] = qtype
            difference["Groups"] = groups_to_string(groups)
            differences.append(difference)
    if len(differences):
        with open(directory_path / "Differences" / (zoneid + '.json'), 'w') as f:
            json.dump(differences, f, indent=2)


def run_tests(path, start, end, args):
    errors = {}
    i = 0
    timer = time.time()
    sub_timer = time.time()
    implementations = get_ports(args)
    start_containers(args.id, implementations)
    with open(path / (str(args.id) + '_log.txt'), 'w') as f:
        for zone in sorted((path / "FormattedZones").iterdir())[start:end]:
            f.write(f'Checking zone: {zone.stem}\n')
            run_test(zone.stem, path, errors, str(args.id), implementations, f)
            i += 1
            if i % 25 == 0:
                f.write(
                    f'Time taken for {i-25} - {i}: {time.time()-sub_timer}s\n')
                f.flush()
                sub_timer = time.time()
        f.write(
            f'Total time for checking from {start}-{end if end else i}: {time.time()-timer}s\n')
        f.write("Errors:\n")
        f.write(str(errors))
        stop_container(str(args.id))


def check_non_negative(value):
    ivalue = int(value)
    if ivalue < 0:
        raise ArgumentTypeError(f"{value} is an invalid range value")
    return ivalue


if __name__ == '__main__':
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter,
                            description='Compares implementations responses for the input tests.')
    parser.add_argument('-path', metavar='DIRECTORY_PATH', default=SUPPRESS,
                        help='The path to the directory containing FormattedZones and QueryResponses directories. (default: Results/)')
    parser.add_argument('-id', type=int, default=1, choices=range(1, 6),
                        help='Unique id for all the containers (useful when running comparison in parallel).')
    parser.add_argument('-r', nargs=2, type=check_non_negative, metavar=('START', 'END'), default=SUPPRESS,
                        help='The range of tests to compare. (default: All tests)')
    parser.add_argument('-b',  help='Disable Bind.', action="store_true")
    parser.add_argument('-n',  help='Disable Nsd.', action="store_true")
    parser.add_argument('-k',  help='Disable Knot.', action="store_true")
    parser.add_argument('-p',  help='Disable PowerDns.', action="store_true")
    parser.add_argument('-c',  help='Disable CoreDns.', action="store_true")
    parser.add_argument('-y',  help='Disable Yadifa.', action="store_true")
    parser.add_argument('-m',  help='Disable MaraDns.', action="store_true")
    parser.add_argument('-t',  help='Disable TrustDns.', action="store_true")

    args = parser.parse_args()
    checked_implementations = (not args.b) + (not args.n) + (not args.k) + \
       (not args.p) + (not args.c) + (not args.y) + (not args.m) + (not args.t)
    if checked_implementations < 2:
        sys.exit(
            'At least two implemetations have to be allowed to perform differential testing.')

    if "path" in args:
        directory_path = pathlib.Path(args.path)
    else:
        directory_path = pathlib.Path("Results/")
    if not (directory_path / "FormattedZones").exists() or not (directory_path / "QueryResponses").exists():
        sys.exit(
            f'The directory {directory_path} does not have FormattedZones and QueryResponses folders.')
    if "r" in args:
        start = args.r[0]
        end = args.r[1]
    else:
        start = 0
        end = None
    (directory_path / "Differences").mkdir(parents=True, exist_ok=True)
    run_tests(directory_path, start, end, args)
