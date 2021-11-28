"""
Run zone preprocessors on (invalid) zone files

usage: preprocessor_checks.py [-h] [-path DIRECTORY_PATH] [-id {1,2,3,4,5}]
                              [-b] [-n] [-k] [-p] [-l]

optional arguments:
  -h, --help            show this help message and exit
  -path DIRECTORY_PATH  The path to the directory containing ZoneFiles; looks
                        for ZoneFiles directory recursively(default:
                        Results/InvalidZoneFileTests/)
  -id {1,2,3,4,5}       Unique id for all the containers (default: 1)
  -b                    Disable Bind. (default: False)
  -n                    Disable Nsd. (default: False)
  -k                    Disable Knot. (default: False)
  -p                    Disable PowerDns. (default: False)
  -l, --latest          Test using latest image tag. (default: False)
"""
#!/usr/bin/env python3

from datetime import datetime
import json
import pathlib
import subprocess
import time
import sys
from argparse import SUPPRESS, ArgumentDefaultsHelpFormatter, ArgumentParser, Namespace
from typing import Dict, Tuple

PREPROCESSOR_DIRECTORY = "PreprocessorOutputs/"


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
    return implementations


def delete_container(container_name: str) -> None:
    """Deletes a container if it is running"""
    cmd_status = subprocess.run(
        ['docker', 'ps', '-a', '--format', '"{{.Names}}"'], stdout=subprocess.PIPE, check=False)
    output = cmd_status.stdout.decode("utf-8")
    if cmd_status.returncode != 0:
        sys.exit(f'Error in executing Docker ps command: {output}')
    all_container_names = [name[1:-1] for name in output.strip().split("\n")]
    if container_name in all_container_names:
        subprocess.run(['docker', 'container', 'rm', '-f', container_name], shell=True, check=True)

def bind(zone_file: pathlib.Path,
         origin: str,
         cid: str,
         new: bool,
         port: int,
         tag: str) -> Tuple[int, str]:
    """
    Uses a Bind container to check the input zone file with Bind preprocessor named-checkzone.
    Returns the preprocessor return code and output.

    :param zone_file: The path to the zone file
    :param zone_domain: The zone origin
    :param cid: The unique id for the container
    :param new: Whether to load the input zone file in a new container
                        or reuse the existing container
    :param port: The host port to map to the container port 53
    :param tag: Tag of the image to use
    """
    if new:
        delete_container(f'{cid}_bind_server')
        subprocess.run(['docker', 'run', '-dp', str(port * int(cid))+':53/udp',
                        '--name=' + cid + '_bind_server', 'bind' + tag], check=False)
    subprocess.run(['docker', 'cp', zone_file, cid +
                    '_bind_server:.'], check=False)
    compilezone = subprocess.run(['docker', 'exec', cid + '_bind_server', 'named-checkzone', '-i',
                                  'local', '-k', 'ignore', origin, f'{zone_file.name}'],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    output = compilezone.stdout.decode("utf-8").strip().split('\n')
    return (compilezone.returncode, output)


def nsd(zone_file: pathlib.Path,
        origin: str,
        cid: str,
        new: bool,
        port: int,
        tag: str) -> Tuple[int, str]:
    """
    Uses a NSD container to check the input zone file with NSD preprocessor nsd-checkzone.
    Returns the preprocessor return code and output.

    :param zone_file: The path to the zone file
    :param zone_domain: The zone origin
    :param cid: The unique id for the container
    :param new: Whether to load the input zone file in a new container
                        or reuse the existing container
    :param port: The host port to map to the container port 53
    :param tag: Tag of the image to use
    """
    if new:
        delete_container(f'{cid}_nsd_server')
        subprocess.run(['docker', 'run', '-dp', str(port * int(cid))+':53/udp',
                        '--name=' + cid + '_nsd_server', 'nsd' + tag], check=False)
    subprocess.run(['docker', 'cp', zone_file, cid +
                    '_nsd_server:.'], check=False)
    compilezone = subprocess.run(['docker', 'exec', cid + '_nsd_server', 'nsd-checkzone',
                                  origin, f'{zone_file.name}'],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    output = compilezone.stdout.decode("utf-8").strip().split('\n')
    return (compilezone.returncode, output)


def knot(zone_file: pathlib.Path,
         origin: str,
         cid: str,
         new: bool,
         port: int,
         tag: str) -> Tuple[int, str]:
    """
    Uses a Knot container to check the input zone file with Knot preprocessor kcheckzone.
    Returns the preprocessor return code and output.

    :param zone_file: The path to the zone file
    :param zone_domain: The zone origin
    :param cid: The unique id for the container
    :param new: Whether to load the input zone file in a new container
                        or reuse the existing container
    :param port: The host port to map to the container port 53
    :param tag: Tag of the image to use
    """
    if new:
        delete_container(f'{cid}_knot_server')
        subprocess.run(['docker', 'run', '-dp', str(port * int(cid))+':53/udp',
                        '--name=' + cid + '_knot_server', 'knot' + tag], check=False)
    subprocess.run(['docker', 'cp', zone_file, cid +
                    '_knot_server:.'], check=False)
    compilezone = subprocess.run(['docker', 'exec', cid + '_knot_server', 'kzonecheck', '-v', '-o',
                                  origin, f'{zone_file.name}'],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    output = compilezone.stdout.decode("utf-8").strip().split('\n')
    return (compilezone.returncode, output)


def powerdns(zone_file: pathlib.Path,
             origin: str,
             cid: str,
             new: bool,
             port: int,
             tag: str) -> Tuple[int, str]:
    """
    Uses a Powerdns container to check the input zone file with PDNS preprocessor pdnsutil.
    Returns the preprocessor return code and output.

    :param zone_file: The path to the zone file
    :param zone_domain: The zone origin
    :param cid: The unique id for the container
    :param new: Whether to load the input zone file in a new container
                        or reuse the existing container
    :param port: The host port to map to the container port 53
    :param tag: Tag of the image to use
    """
    if new:
        delete_container(f'{cid}_powerdns_server')
        subprocess.run(['docker', 'run', '-dp', str(port * int(cid))+':53/udp',
                        '--name=' + cid + '_powerdns_server', 'powerdns' + tag], check=False)
    subprocess.run(['docker', 'cp', zone_file, cid +
                    '_powerdns_server:/usr/local/etc/' + origin], check=False)
    bindbackend = f'zone "{origin}" {{\n  file "/usr/local/etc/{origin}";\n  type master;\n}};'
    with open('bindbackend'+cid+'.conf', 'w') as file_pointer:
        file_pointer.write(bindbackend)
    subprocess.run(['docker', 'cp', 'bindbackend'+cid+'.conf',
                    cid + '_powerdns_server:/usr/local/etc/bindbackend.conf'], check=False)
    pathlib.Path('bindbackend'+cid+'.conf').unlink()
    subprocess.run(['docker', 'exec', cid + '_powerdns_server',
                    'dos2unix', '/usr/local/etc/bindbackend.conf'], check=False)
    compilezone = subprocess.run(['docker', 'exec', cid + '_powerdns_server', 'pdnsutil', '-v',
                                  'check-zone', f'{origin}'],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    output = compilezone.stdout.decode("utf-8").strip().split('\n')
    return (compilezone.returncode, output)


def check_zone_with_preprocessors(input_args: Namespace,
                                  directory: pathlib.Path,
                                  zone_path: pathlib.Path,
                                  cid: str,
                                  new: bool) -> bool:
    """
    Checks a zone file with different input implementations preprocessors.
    Returns if the checks were successful.

    :param input_args: The input arguments
    :param directory: The path to store the preprocessor outputs
    :param zone_path: The path to the zone file
    :param cid: The unique id for the container
    :param new: Whether to load the input zone file in a new container
                        or reuse the existing container
    """
    outputs = {}
    origin = ''
    tag = ':oct'
    if input_args.latest:
        tag = ':latest'
    with open(zone_path, 'r') as zone_fp:
        for line in zone_fp:
            if 'SOA' in line:
                origin = line.split('\t')[0]
                if ' ' in origin:
                    origin = line.split()[0]
    if not origin:
        print(f'{datetime.now()}\tSkipping {zone_path.stem} as no SOA is found')
        return False
    port_mappings = get_ports(input_args)
    for impl, (check, port) in port_mappings.items():
        if check:
            if impl == 'bind':
                outputs["Bind"] = {}
                outputs["Bind"]["Code"], outputs["Bind"]["Output"] = bind(
                    zone_path, origin, cid, new, port, tag)
            elif impl == 'nsd':
                outputs["Nsd"] = {}
                outputs["Nsd"]["Code"], outputs["Nsd"]["Output"] = nsd(
                    zone_path, origin, cid, new, port, tag)
            elif impl == 'knot':
                outputs["Knot"] = {}
                outputs["Knot"]["Code"], outputs["Knot"]["Output"] = knot(
                    zone_path, origin, cid, new, port, tag)
            elif impl == 'powerdns':
                outputs["Powerdns"] = {}
                outputs["Powerdns"]["Code"], outputs["Powerdns"]["Output"] = powerdns(
                    zone_path, origin, cid, new, port, tag)
    with open(directory / PREPROCESSOR_DIRECTORY / (zone_path.stem + '.json'), 'w') as output_fp:
        json.dump(outputs, output_fp, indent=2)
    return True


def preprocessor_check_helper(input_args: Namespace, input_dir: pathlib.Path) -> None:
    """
    Helper function to check (invalid) zone files with implementations' preprocessors.
    Iterates recursively over the input directory to find ZoneFiles directory and
    calls check_zone_with_preprocessors function to check a zone file.

    :param input_args: The input arguments
    :param input_dir: The path to the parent directory with ZoneFiles directory.
    """
    # Exit if the inputted path does not exist or is not a directory.
    if not (input_dir.exists() or input_dir.is_dir()):
        return
    input_zone_files_dir = input_dir / 'ZoneFiles/'
    output_zone_file_dir = input_dir / PREPROCESSOR_DIRECTORY
    if input_zone_files_dir.exists() and input_zone_files_dir.is_dir():
        output_zone_file_dir.mkdir(parents=True, exist_ok=True)
        new_container = False
        print(
            f'{datetime.now()}\tStarted checking the zone files in {input_zone_files_dir}')
        start = time.time()
        for zone_path in input_zone_files_dir.iterdir():
            if not zone_path.is_file():
                continue
            new_container = check_zone_with_preprocessors(
                input_args, input_dir, zone_path, str(input_args.id), not new_container)
        print(f'{datetime.now()}\tFinished checking the zone files in'
              f'{input_zone_files_dir} in {time.time() - start}')
    else:
        if input_dir.is_dir():
            for subdir in input_dir.iterdir():
                preprocessor_check_helper(input_args, subdir)


if __name__ == '__main__':
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter,
                            description='Run zone preprocessors on (invalid) zone files')
    parser.add_argument('-path', metavar='DIRECTORY_PATH', default=SUPPRESS,
                        help='The path to the directory containing ZoneFiles; '
                        'looks for ZoneFiles directory recursively'
                        '(default: Results/InvalidZoneFileTests/)')
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
        dir_path = pathlib.Path("Results/InvalidZoneFileTests/")
    if dir_path.exists():
        preprocessor_check_helper(args, dir_path)
    else:
        print(f'The input path {dir_path} does not exist.')
