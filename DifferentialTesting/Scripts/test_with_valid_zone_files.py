"""
Runs tests with valid zone files on different implementations.
Either compares responses from mulitple implementations with each other or uses a
expected response to flag differences (only when one implementation is passed for testing).

usage: test_with_valid_zone_files.py [-h] [-path DIRECTORY_PATH]
                                     [-id {1,2,3,4,5}] [-r START END] [-b]
                                     [-n] [-k] [-p] [-c] [-y] [-m] [-t] [-l]

optional arguments:
  -h, --help            show this help message and exit
  -path DIRECTORY_PATH  The path to the directory containing ZoneFiles
                        and either Queries or ExpectedResponses directories.
                        (default: Results/ValidZoneFileTests/)
  -id {1,2,3,4,5}       Unique id for all the containers (useful when running
                        comparison in parallel). (default: 1)
  -r START END          The range of tests to compare. (default: All tests)
  -b                    Disable Bind. (default: False)
  -n                    Disable Nsd. (default: False)
  -k                    Disable Knot. (default: False)
  -p                    Disable PowerDns. (default: False)
  -c                    Disable CoreDns. (default: False)
  -y                    Disable Yadifa. (default: False)
  -m                    Disable MaraDns. (default: False)
  -t                    Disable TrustDns. (default: False)
  -l, --latest          Test using latest image tag. (default: False)
"""
#!/usr/bin/env python3

import copy
import json
import pathlib
import subprocess
import sys
import time
from argparse import (SUPPRESS, ArgumentDefaultsHelpFormatter, ArgumentParser,
                      ArgumentTypeError, Namespace)
from datetime import datetime
from multiprocessing import Process
from typing import Any, Dict, List, Optional, TextIO, Tuple, Union

import dns.message
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

ZONE_FILES = "ZoneFiles/"
QUERIES = "Queries/"
QUERY_RESPONSES = "ExpectedResponses/"
DIFFERENCES = "Differences/"

# A response is a tuple where the first element is the implementation in string format
# and second element is a DNS response (or "No response") of that implementation
ResponseType = Tuple[str, Union[str, dns.message.Message]]


def get_ports(input_args: Namespace) -> Dict[str, Tuple[bool, int]]:
    """
    Returns a map from an implementation to the host port its container port 53
    should be mapped and whether that implementation should be tested.

    :param input_args: The input arguments
    """
    implementations = {}
    implementations['bind'] = (not input_args.b, 8000)
    implementations['nsd'] = (not input_args.n, 8100)
    implementations['knot'] = (not input_args.k, 8200)
    implementations['powerdns'] = (not input_args.p, 8300)
    implementations['yadifa'] = (not input_args.y, 8400)
    implementations['coredns'] = (not input_args.c, 8500)
    implementations['maradns'] = (not input_args.m, 8600)
    implementations['trustdns'] = (not input_args.t, 8700)
    return implementations


def remove_container(cid: int) -> None:
    """
    Stops the running containers of all the implementations.

    :param cid: The unique id for all the containers
    """
    # Get the list of containers
    cmd_status = subprocess.run(
        ['docker', 'ps', '-a', '--format', '"{{.Names}}"'], stdout=subprocess.PIPE, check=False)
    output = cmd_status.stdout.decode("utf-8")
    if cmd_status.returncode != 0:
        sys.exit(f'Error in executing Docker ps command: {output}')
    all_container_names = [name[1:-1] for name in output.strip().split("\n")]
    servers = ["_bind_server", "_nsd_server", "_knot_server", "_powerdns_server",
               "_maradns_server", "_yadifa_server", "_trustdns_server", "_coredns_server"]
    for server in servers:
        # Force remove the container if it is running
        if str(cid) + server in all_container_names:
            subprocess.run(['docker', 'container', 'rm', str(cid) + server, '-f'],
                           stdout=subprocess.PIPE, check=False)


def start_containers(cid: int, implementations: Dict[str, Tuple[bool, int]], tag: str) -> None:
    """
    Starts a container for each requested implementation

    :param cid: The unique id for all the containers
    :param implementations: Map from an implementation to a tuple of two items
                            - 1. whether to check that implementation 2. which host port
                            should be mapped to the container port 53
    :param tag: Tag of the images to use
    """
    remove_container(cid)
    for impl, (check, port) in implementations.items():
        if check:
            subprocess.run(['docker', 'run', '-dp', str(port * cid)+':53/udp',
                            '--name=' + str(cid) + '_' + impl + '_server', impl + tag], check=True)


def querier(query_name: str, query_type: str, port: int) -> Union[str, dns.message.Message]:
    """
    Sends the input query to the input host port and either DNS response or an error message

    :param query_name: Domain name of the query
    :param query_type: Record type requested
    :param port: The host port to send the query
    """
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
    except:  # pylint: disable=bare-except
        return f'Unexpected error {sys.exc_info()[1]}'


def response_equality_check(response_a: Union[str, dns.message.Message],
                            response_b: Union[str, dns.message.Message]) -> bool:
    """
    Checks whether the two input responses are same or not.

    :param response_a: The first response
    :param response_b: The second response

    Either of the responses can be a string if there was an error during querying.
    """
    if type(response_a) != type(response_b):
        return False
    if isinstance(response_a, str):
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
        for record in section_a:
            if record not in section_b:
                return False
        for record in section_b:
            if record not in section_a:
                return False
        return True

    if not check_section(response_a.question, response_b.question):
        return False
    if not check_section(response_a.answer, response_b.answer):
        return False
    if not check_section(response_a.additional, response_b.additional):
        return False
    # Check authority section only when both the answer sections are non-empty
    # as implementations can add SOA/NS records to the authority section
    if not(len(response_a.answer) and len(response_b.answer)):
        return check_section(response_a.authority, response_b.authority)
    return True


def group_responses(responses: List[ResponseType]) -> List[List[ResponseType]]:
    """
    Groups (creates a list of lists) responses where in each group (inner list)
    all the implementations have the same response.

    :param responses: List of responses
    """
    groups = []  # type: List[List[ResponseType]]
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


def groups_to_json(groups: List[List[ResponseType]]) -> List[Dict[str, Any]]:
    """
    Returns the input grouped responses in a JSON format to output to a file.

    :param groups: The list of implementations with the same response
    """
    tmp = []
    for same_response_group in groups:
        servers = ""
        for server in same_response_group:
            servers += server[0] + " "
        group = {}
        group["Server/s"] = servers
        group["Response"] = same_response_group[0][1] if isinstance(
            same_response_group[0][1], str) else same_response_group[0][1].to_text().split('\n')
        tmp.append(group)
    return tmp


def prepare_containers(zone_file: pathlib.Path,
                       zone_domain: str,
                       cid: int,
                       restart: bool,
                       implementations: Dict[str, Tuple[bool, int]],
                       tag: str) -> None:
    """
    Either starts new containers or reuses existing containers to prepare the
    container to serve the input zone file.
    Uses one process for each implementation tested to speedup preparation.

    :param zone_file: The path to the zone file
    :param zone_domain: The zone origin
    :param cid: The unique id for all the containers
    :param restart: Whether to load the input zone file in a new container
                        or reuse the existing container
    :param implementations: Map from an implementation to a tuple of two items
                            - 1. whether to load that implementation container
                              2. which host port should be mapped to the container port 53
    :param tag: Tag of the images to use
    """
    process_pool = []
    for impl, (check, port) in implementations.items():
        if check:
            process_pool.append(
                Process(target=globals()[impl],
                        args=(zone_file, zone_domain,
                              str(cid) + '_' + impl + '_server',
                              port*cid, restart, tag)))
    for process in process_pool:
        process.start()
    for process in process_pool:
        process.join()


def get_queries(zoneid: str,
                num_implemetations: int,
                directory_path: pathlib.Path,
                log_fp: TextIO,
                errors: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Returns a list of queries to test againt the zone file with zoneid.
    If num_implementations is 1, then it looks for ExpectedResponses directory; otherwise
    use Queries directory to get the queries.

    :param zoneid: The unique zone identifier
    :param num_implementations: The number of implementations being tested
    :param directory_path: The path to the directory containing zone files and queries
    :param log_fp: The log file pointer
    :param errors: A map from zoneid to any error encountered during testing
    """
    if num_implemetations == 1:
        if not (directory_path / QUERY_RESPONSES).exists():
            log_fp.write(
                f'{datetime.now()}\tNo {QUERY_RESPONSES} directory with '
                'expected responses exists\n')
            errors[zoneid] = f'No {QUERY_RESPONSES} directory with expected responses exists'
            return []
        if not (directory_path / QUERY_RESPONSES / (zoneid + '.json')).exists():
            log_fp.write(f'{datetime.now()}\tThere is no {zoneid}.json expected responses file in'
                         f' {QUERY_RESPONSES} directory\n')
            errors[zoneid] = f'There is no {zoneid}.json expected responses file' \
                             f' in {QUERY_RESPONSES} directory\n'
            return []
        with open(directory_path / QUERY_RESPONSES / (zoneid + '.json'), 'r') as query_resp_fp:
            return json.load(query_resp_fp)
    else:
        if not (directory_path / QUERIES).exists():
            log_fp.write(f'{datetime.now()}\tThere is no {QUERIES} directory\n')
            errors[zoneid] = f'There is no {QUERIES} directory\n'
            return []
        if not (directory_path / QUERIES / (zoneid + '.json')).exists():
            log_fp.write(
                f'{datetime.now()}\tThere is no {zoneid}.json queries'
                f' file in {QUERIES} directory\n')
            errors[zoneid] = f'There is no {zoneid}.json queries file in {QUERIES} directory\n'
            return []
        with open(directory_path / QUERIES / (zoneid + '.json'), 'r') as query_fp:
            return json.load(query_fp)


def run_test(zoneid: str,
             parent_directory_path: pathlib.Path,
             errors: Dict[str, str],
             cid: int,
             port_mappings: Dict[str, Tuple[bool, int]],
             log_fp: TextIO,
             tag: str) -> None:
    """
    Runs the tests on the input single zone file.

    :param zoneid: The unique zone identifier
    :param parent_directory_path: The path to the directory containing zone files and queries
    :param errors: A map from zoneid to any error encountered during testing
    :param cid: The unique id for all the containers
    :param implementations: Map from an implementation to a tuple of two items
                            - 1. whether to check that implementation 2. which host port
                            should be mapped to the container port 53
    :param log_fp: The log file pointer
    :param tag: Tag of the images to use
    """
    has_dname = False
    zone_domain = ''
    with open(parent_directory_path / ZONE_FILES / (zoneid + '.txt'), 'r') as zone_fp:
        for line in zone_fp:
            if 'SOA' in line:
                zone_domain = line.split('\t')[0]
                if ' ' in zone_domain:
                    zone_domain = line.split()[0]
            if 'DNAME' in line:
                has_dname = True
    if not zone_domain:
        log_fp.write(f'{datetime.now()}\tSOA not found in {zoneid}\n')
        errors[zoneid] = 'SOA not found'
        return

    implementations = copy.deepcopy(port_mappings)
    # Exclude implementations that do not support DNAME type if the zone file has a DNAME record
    if has_dname:
        implementations['yadifa'] = (
            False, implementations['yadifa'][1])  # Yadifa
        implementations['trustdns'] = (
            False, implementations['trustdns'][1])    # TrustDns
        implementations['maradns'] = (
            False, implementations['maradns'][1])    # MaraDns
    total_impl_tested = sum(x[0] for x in list(implementations.values()))
    queries = get_queries(zoneid, total_impl_tested,
                          parent_directory_path, log_fp, errors)
    if not queries:
        return

    prepare_containers(parent_directory_path / ZONE_FILES /
                       (zoneid + '.txt'), zone_domain, cid, False, implementations, tag)

    differences = []
    for query in queries:
        qname = query["Query"]["Name"]
        qtype = query["Query"]["Type"]
        responses = []
        for impl, (check, port) in implementations.items():
            if check:
                respo = querier(qname, qtype, port * int(cid))
                #  If it is not a proper DNS response, try again with a new container
                if not isinstance(respo, dns.message.Message):
                    single_impl = {}
                    single_impl[impl] = (True, port)
                    prepare_containers(parent_directory_path / ZONE_FILES /
                                       (zoneid + '.txt'), zone_domain, cid, True, single_impl, tag)
                    log_fp.write(f'{datetime.now()}\tRestarted {impl}\'s container while '
                                 f'testing zone {zoneid}\n')
                    time.sleep(1)
                    respo = querier(qname, qtype, port * int(cid))
                responses.append((impl, respo))
        # If there is only one implementation tested, use expected response/s
        if len(responses) == 1:
            exp_resps = query["Expected Response"]
            for exp_res in exp_resps:
                responses.append((exp_res["Server/s"],
                                  dns.message.from_text('\n'.join(exp_res["Response"]))))
        groups = group_responses(responses)
        if len(groups) > 1:
            difference = {}
            difference["Query Name"] = qname
            difference["Query Type"] = qtype
            difference["Groups"] = groups_to_json(groups)
            differences.append(difference)
    if differences:
        with open(parent_directory_path / DIFFERENCES / (zoneid + '.json'), 'w') as difference_fp:
            json.dump(differences, difference_fp, indent=2)


def run_tests(parent_directory_path: pathlib.Path,
              start: int,
              end: Optional[int],
              input_args: Namespace) -> None:
    """
    Runs the tests in the parent directory path against all the implementations in
    the input arguments and compares their responses. If a difference in responses
    is found, then the responses are outputted as a JSON to the Differences directory.

    :param parent_directory_path: The path to the directory containing zone files and queries
    :param start: The start index of the tests
    :param end: The end index of the tests
    :param input_args: The input arguments
    """
    errors = {}  # type: Dict[str, str]
    i = 0
    timer = time.time()
    sub_timer = time.time()
    implementations = get_ports(input_args)
    tag = ':oct'
    if input_args.latest:
        tag = ':latest'
    start_containers(input_args.id, implementations, tag)
    # Create and dump logs to a file
    with open(parent_directory_path / (str(input_args.id) + '_log.txt'), 'w', 1) as log_fp:
        for zone in sorted((parent_directory_path / ZONE_FILES).iterdir(),
                           key=lambda x: int(x.stem))[start:end]:
            log_fp.write(f'{datetime.now()}\tChecking zone: {zone.stem}\n')
            run_test(zone.stem, parent_directory_path, errors,
                     input_args.id, implementations, log_fp, tag)
            i += 1
            if i % 25 == 0:
                log_fp.write(
                    f'{datetime.now()}\tTime taken for {start + i - 25} - {start + i}: '
                    f'{time.time()-sub_timer}s\n')
                sub_timer = time.time()
        log_fp.write(
            f'{datetime.now()}\tTotal time for checking from {start}-{end if end else i}: '
            f'{time.time()-timer}s\n')
        log_fp.write("Errors:\n")
        log_fp.write(str(errors))
        remove_container(input_args.id)


def check_non_negative(value: str) -> int:
    """Check if the input value is non-negative"""
    ivalue = int(value)
    if ivalue < 0:
        raise ArgumentTypeError(f"{value} is an invalid range value")
    return ivalue


if __name__ == '__main__':
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter,
                            description='Runs tests with valid zone files on different '
                            'implementations. Either compares responses from mulitple '
                            'implementations with each other or uses a '
                            'expected response to flag differences '
                            '(only when one implementation is passed for testing)')
    parser.add_argument('-path', metavar='DIRECTORY_PATH', default=SUPPRESS,
                        help='The path to the directory containing ZoneFiles and '
                        'either Queries or ExpectedResponses directories.'
                        '(default: Results/ValidZoneFileTests/)')
    parser.add_argument('-id', type=int, default=1, choices=range(1, 6),
                        help='Unique id for all the containers '
                        '(useful when running comparison in parallel).')
    parser.add_argument('-r', nargs=2, type=check_non_negative, metavar=('START', 'END'),
                        default=SUPPRESS,
                        help='The range of tests to compare. (default: All tests)')
    parser.add_argument('-b', help='Disable Bind.', action="store_true")
    parser.add_argument('-n', help='Disable Nsd.', action="store_true")
    parser.add_argument('-k', help='Disable Knot.', action="store_true")
    parser.add_argument('-p', help='Disable PowerDns.', action="store_true")
    parser.add_argument('-c', help='Disable CoreDns.', action="store_true")
    parser.add_argument('-y', help='Disable Yadifa.', action="store_true")
    parser.add_argument('-m', help='Disable MaraDns.', action="store_true")
    parser.add_argument('-t', help='Disable TrustDns.', action="store_true")
    parser.add_argument(
        '-l', '--latest', help='Test using latest image tag.', action="store_true")

    args = parser.parse_args()
    if "path" in args:
        dir_path = pathlib.Path(args.path)
    else:
        dir_path = pathlib.Path("Results/ValidZoneFileTests")
    if not (dir_path / ZONE_FILES).exists():
        sys.exit(
            f'The directory {dir_path} does not have ZoneFiles directory')
    checked_implementations = (not args.b) + (not args.n) + (not args.k) + \
        (not args.p) + (not args.c) + (not args.y) + (not args.m) + (not args.t)
    if checked_implementations == 0:
        sys.exit('Enable at least one implementation')
    if checked_implementations < 2:
        if not (dir_path / QUERY_RESPONSES).exists():
            sys.exit('Either choose at least two implementations to perform differential testing or'
                     f' the directory "{dir_path}" should have ExpectedResponses directory')
    if not (dir_path / QUERIES).exists() and \
            not (dir_path / QUERY_RESPONSES).exists():
        sys.exit(
            f'There is no Queries or ExpectedResponses directory in "{dir_path}".')
    if "r" in args:
        START = args.r[0]
        END = args.r[1]
    else:
        START = 0
        END = None
    (dir_path / DIFFERENCES).mkdir(parents=True, exist_ok=True)
    run_tests(dir_path, START, END, args)
