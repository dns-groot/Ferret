"""
Runs tests with invalid zone files on different implementations.
Generates queries using GRoot equivalence classes.
Either compares responses from mulitple implementations with each other or uses a expected
response to flag differences (only when one implementation is passed for testing).

usage: test_with_invalid_zone_files.py [-h] [-path DIRECTORY_PATH]
                                       [-id {1,2,3,4,5}] [-b] [-n] [-k] [-p] [-l]

optional arguments:
  -h, --help            show this help message and exit
  -path DIRECTORY_PATH  The path to the directory containing ZoneFiles and PreprocessorOutputs
                         directories; looks for those two directories recursively
                         (default: Results/InvalidZoneFileTests/)
  -id {1,2,3,4,5}       Unique id for all the containers (default: 1)
  -b                    Disable Bind. (default: False)
  -n                    Disable Nsd. (default: False)
  -k                    Disable Knot. (default: False)
  -p                    Disable PowerDns. (default: False)
  -l, --latest          Test using latest image tag. (default: False)
"""
#!/usr/bin/env python3

import json
import os
import pathlib
import platform
import subprocess
import sys
import time
from argparse import (SUPPRESS, ArgumentDefaultsHelpFormatter, ArgumentParser,
                      Namespace)
from datetime import datetime
from typing import Any, Dict, List, TextIO, Tuple

import dns.query
import dns.rdataclass
import dns.rdatatype
import dns.resolver

from Scripts.preprocessor_checks import PREPROCESSOR_DIRECTORY
from Scripts.test_with_valid_zone_files import (DIFFERENCES, QUERY_RESPONSES,
                                                ZONE_FILES, group_responses,
                                                groups_to_json,
                                                prepare_containers, querier,
                                                start_containers)

EQUIVALENCE_CLASSES_DIR = "EquivalenceClassNames/"


def get_ports_for_invalid_zones(input_args: Namespace) -> Dict[str, Tuple[bool, int]]:
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
    return implementations


def generate_groot_image(logger: TextIO) -> None:
    """
    Generates the GRoot image required for generation of queries using equivalence classes.
    Exits the program if the image generation is not successful.

    :param logger: The log file pointer
    """
    run_cmd = ['docker', 'build', '-t',
               "groot:ferret", '-f', "GRoot/Dockerfile", '.']
    logger.write(f'{datetime.now()}\tBuilding GRoot image..\n')
    if platform.system() == 'Linux':
        my_env = os.environ.copy()
        my_env['DOCKER_BUILDKIT'] = '1'
        cmd_output = subprocess.run(
            run_cmd, env=my_env, stdout=subprocess.PIPE, check=True)
    else:
        cmd_output = subprocess.run(
            run_cmd, stdout=subprocess.PIPE, check=True)
    if cmd_output.returncode != 0:
        sys.exit('Error in building image for GRoot.\n')
    logger.write(f'{datetime.now()}\tFinished building GRoot image..\n')


def generate_ecs(parent_dir: pathlib.Path, zoneid: str) -> None:
    """
    Generates equivalence class domain names for the input zone file.
    Uses GRoot container to generate the names by copying in the zone file
        and copying out the generated file.

    :param dir: The parent directory to the directory containing zone files
    :param zoneid: The zone to consider
    """
    if (parent_dir / EQUIVALENCE_CLASSES_DIR / (zoneid + '.txt')).exists():
        return
    subprocess.run(['docker', 'cp', parent_dir / ZONE_FILES / (zoneid + '.txt'),
                    'groot_server:/home/groot/groot/build/bin/zonefile/'],
                   stdout=subprocess.PIPE, check=False)
    subprocess.run(['docker', 'exec', 'groot_server', 'sudo',
                    'python3', '/home/groot/groot/metadata_gen.py', zoneid + '.txt'], check=False)
    subprocess.run(['docker', 'exec', 'groot_server',
                    'build/bin/groot', 'build/bin/zonefile/', '-le'],
                   stdout=subprocess.PIPE, check=False)
    subprocess.run(['docker', 'cp', 'groot_server:/home/groot/groot/ECs.txt', parent_dir /
                    EQUIVALENCE_CLASSES_DIR / (zoneid + '.txt')],
                   stdout=subprocess.PIPE, check=False)


def get_queries_invalid_zones(zoneid: str,
                              num_implemetations: int,
                              parent_dir: pathlib.Path,
                              zone_domain: str,
                              logger: TextIO) -> List[Dict[str, Any]]:
    """
    Returns a list of queries to test againt the zone file with zoneid.
    If num_implementations is 1, then it looks for ExpectedResponses directory; otherwise
    use EquivalenceClassNames directory to generate the queries.

    :param zoneid: The unique zone identifier
    :param num_implementations: The number of implementations being tested
    :param parent_dir: The path to the directory containing zone files and queries
    :param zone_domain: The zone origin
    :param log_fp: The log file pointer
    """
    if num_implemetations == 1:
        if not (parent_dir / QUERY_RESPONSES / (zoneid + '.json')).exists():
            logger.write(f'{datetime.now()}\tThere is no {zoneid}.json expected responses file in'
                         f' {QUERY_RESPONSES} directory\n')
            return []
        with open(parent_dir / QUERY_RESPONSES / (zoneid + '.json'), 'r') as query_resp_fp:
            return json.load(query_resp_fp)
    else:
        if not (parent_dir / EQUIVALENCE_CLASSES_DIR).exists():
            logger.write(
                f'{datetime.now()}\tThere is no {EQUIVALENCE_CLASSES_DIR} directory\n')
            return []
        if not (parent_dir / EQUIVALENCE_CLASSES_DIR / (zoneid + '.txt')).exists():
            logger.write(
                f'{datetime.now()}\tThere is no {zoneid}.json queries file in '
                f'{EQUIVALENCE_CLASSES_DIR} directory\n')
            return []
        with open(parent_dir / EQUIVALENCE_CLASSES_DIR / (zoneid + '.txt'), 'r') as ecf:
            ecs = ecf.readlines()
            if len(ecs) > 200:
                logger.write(f'{datetime.now()}\tSkipping zone {zoneid} in {parent_dir}'
                             f' with {len(ecs)} as there are too many ECs\n')
                return []
            queries = []
            for ec_name in ecs:
                qname = ec_name[:-1]
                if not qname.endswith(zone_domain):
                    continue
                for qtype in ['A', 'NS', 'SOA', 'CNAME', 'DNAME', 'TXT']:
                    tmp = {}  # type: Dict[str, Dict[str, str]]
                    tmp["Query"] = {}
                    tmp["Query"]["Name"] = qname
                    tmp["Query"]["Type"] = qtype
                    queries.append(tmp)
            return queries


def run_test(input_args: Namespace,
             parent_dir: pathlib.Path,
             zoneid: str,
             cid: int,
             tag: str,
             logger: TextIO) -> None:
    """
    Run the tests on the input zone file.
    """
    zone_domain = ''
    with open(parent_dir / ZONE_FILES / (zoneid + '.txt'), 'r') as zone_fp:
        for line in zone_fp:
            if 'SOA' in line:
                zone_domain = line.split('\t')[0]
                if ' ' in zone_domain:
                    zone_domain = line.split()[0]
    if not zone_domain:
        logger.write(
            f'{datetime.now()}\tNot checking zone {zoneid} as SOA not found\n')
        return
    implementations = get_ports_for_invalid_zones(input_args)
    with open(parent_dir / PREPROCESSOR_DIRECTORY / (zoneid + ".json"), 'r') as outf:
        output = json.load(outf)
        # Check an implementation if the zone file is accepted by the preprocessor and
        # requested by the user.
        implementations['bind'] = (not bool(
            output['Bind']['Code']) and implementations['bind'][0], implementations['bind'][1])
        implementations['nsd'] = (not bool(
            output['Nsd']['Code']) and implementations['nsd'][0], implementations['nsd'][1])
        implementations['knot'] = (not bool(
            output['Knot']['Code']) and implementations['knot'][0], implementations['knot'][1])
        implementations['powerdns'] = (not bool(
            output['Powerdns']['Code']) and implementations['powerdns'][0],
                                       implementations['powerdns'][1])
        total_impl_tested = sum(v[0] for v in implementations.values())
        if total_impl_tested == 0:
            logger.write(f'{datetime.now()}\tZone file {zoneid} in {parent_dir} can not be tested '
                         'as no implementation that accepts the zone file is selected\n')
            return
        if total_impl_tested == 1 and not (parent_dir / QUERY_RESPONSES).exists():
            logger.write(f'{datetime.now()}\tZone file {zoneid} in {parent_dir} can not be tested '
                         'as only one implementation is used and there is '
                         'no expected responses directory\n')
            return
    generate_ecs(parent_dir, zoneid)
    prepare_containers(parent_dir / ZONE_FILES / (zoneid + '.txt'),
                       zone_domain, cid, False, implementations, tag)
    queries = get_queries_invalid_zones(zoneid, total_impl_tested,
                                        parent_dir, zone_domain, logger)
    if not queries:
        return
    differences = []
    for query in queries:
        qname = query["Query"]["Name"]
        qtype = query["Query"]["Type"]
        responses = []
        for impl, (check, port) in implementations.items():
            if check:
                respo = querier(qname, qtype, port * int(cid))
                if not isinstance(respo, dns.message.Message):
                    single_impl = {}
                    single_impl[impl] = (True, port)
                    prepare_containers(parent_dir / ZONE_FILES / (zoneid + '.txt'),
                                       zone_domain, cid, True, implementations, tag)
                    logger.write(f'{datetime.now()}\tRestarted {impl}\'s container while'
                                 f' testing zone {zoneid}\n')
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
        with open(parent_dir / DIFFERENCES / (zoneid + '.json'), 'w') as difference_fp:
            json.dump(differences, difference_fp, indent=2)


def run_tests_helper(input_args: Namespace,
                     input_dir: pathlib.Path,
                     logger: TextIO) -> None:
    """
    Helper function to check (invalid) zone files with implementations' preprocessors.
    Iterates recursively over the input directory to find ZoneFiles directory and
    calls check_zone_with_preprocessors function to check a zone file.

    :param input_args: The input arguments
    :param input_dir: The path to the parent directory with ZoneFiles directory.
    :param logger: The log file pointer
    """
    # Exit if the inputted path does not exist or is not a directory.
    if not (input_dir.exists() or input_dir.is_dir()):
        return
    zone_files_dir = input_dir / ZONE_FILES
    preprocessor_output_dir = input_dir / PREPROCESSOR_DIRECTORY
    if zone_files_dir.exists() and zone_files_dir.is_dir() and \
            preprocessor_output_dir.exists() and preprocessor_output_dir.is_dir():
        #  Generate GRoot image required for generation of queries
        generate_groot_image(logger)
        # Start the container for the GRoot
        cmd = "docker start groot_server || docker run -d --name=groot_server groot:ferret"
        subprocess.run(cmd, shell=True, check=False)
        (input_dir / DIFFERENCES).mkdir(parents=True, exist_ok=True)
        (input_dir / EQUIVALENCE_CLASSES_DIR).mkdir(parents=True, exist_ok=True)
        implementations = get_ports_for_invalid_zones(input_args)
        tag = ':oct'
        if input_args.latest:
            tag = ':latest'
        start_containers(input_args.id, implementations, tag)
        logger.write(
            f'{datetime.now()}\tStarted checking the zone files in {zone_files_dir}\n')
        start = time.time()
        for zone_path in zone_files_dir.iterdir():
            if not zone_path.is_file():
                continue
            logger.write(f'{datetime.now()}\tChecking zone {zone_path.stem}\n')
            run_test(input_args, input_dir, zone_path.stem,
                     int(input_args.id), tag, logger)
        logger.write(f'{datetime.now()}\tFinished checking the zone files in '
                     f'{input_dir} in {time.time() - start}s\n')
    else:
        if input_dir.is_dir():
            for subdir in input_dir.iterdir():
                run_tests_helper(input_args, subdir, logger)


if __name__ == '__main__':
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter,
                            description='Runs tests with invalid zone files on different '
                            'implementations. Generates queries using GRoot equivalence classes. '
                            'Either compares responses from mulitple '
                            'implementations with each other or uses a '
                            'expected response to flag differences '
                            '(only when one implementation is passed for testing)')
    parser.add_argument('-path', metavar='DIRECTORY_PATH', default=SUPPRESS,
                        help='The path to the directory containing ZoneFiles and '
                        'PreprocessorOutputs directories; looks for those two directories '
                        'recursively (default: Results/InvalidZoneFileTests/)')
    parser.add_argument('-id', type=int, default=1, choices=range(1, 6),
                        help='Unique id for all the containers')
    parser.add_argument('-b', help='Disable Bind.', action="store_true")
    parser.add_argument('-n', help='Disable Nsd.', action="store_true")
    parser.add_argument('-k', help='Disable Knot.', action="store_true")
    parser.add_argument('-p', help='Disable PowerDns.', action="store_true")
    parser.add_argument(
        '-l', '--latest', help='Test using latest image tag.', action="store_true")
    args = parser.parse_args()
    if "path" in args:
        dir_path = pathlib.Path(args.path)
    else:
        dir_path = pathlib.Path("Results/InvalidZoneFileTests")
    if dir_path.exists():
        with open(dir_path / (str(args.id) + '_invalid_zone_files_checking_log.txt'), 'w', 1) as log_p:
            run_tests_helper(args, dir_path, log_p)
    else:
        print(f'The input path {dir_path} does not exist.')
