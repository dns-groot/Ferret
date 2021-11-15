"""
Serves a user input zone file (or default one) with the user input implementation by creating a
new container for that implementation image or by reusing an existing container and by copying
the zone file into the container. The module also generates the necessar
implementation-specific configuration files.

usage: main.py [-h] [-z ZONE_FILE_PATH] [-i {yadifa,powerdns,maradns,nsd,
                        trustdns,bind,knot,coredns}] [-p UNUSED_PORT] [-c CONTAINER_NAME] [-l]

Specify an image name and a port to start a fresh container (also container name if you want
to assign a name) or only the name of an existing container to reuse it.

optional arguments:
  -z ZONE_FILE_PATH     The path to the zone file to be served. (default: db.campus.edu.)
  -i {yadifa,powerdns,maradns,nsd,trustdns,bind,knot,coredns}
                        The docker image name of the implementation to start a container.
  -p UNUSED_PORT        An unused host port to map to port 53 of the container.
  -c CONTAINER_NAME     A name for the container. (default: Random Docker generated name)
  -l, --latest          Serve using the latest image. (default: Oct 2020 image)
"""

#!/usr/bin/env python3

import pathlib
import subprocess
import sys
from argparse import ArgumentParser, FileType, RawTextHelpFormatter

from Bind.prepare import run as bind
from Coredns.prepare import run as coredns
from Knot.prepare import run as knot
from Maradns.prepare import run as maradns
from Nsd.prepare import run as nsd
from Powerdns.prepare import run as powerdns
from Trustdns.prepare import run as trustdns
from Yadifa.prepare import run as yadifa


def load_and_serve_zone_file(zone_file, image, cname, port, latest):
    """
    :param zone_file: Path to the Bind-style zone file
    :param image: The image name of the implementation
    :param cname: Container name
    :param port: The host port which is mapped to the port 53 of the container
    :param latest: Whether to use tha latest tag
    """
    tag = ':oct'
    if latest:
        tag = ':latest'
    image += tag
    if image:
        # Check if the docker image exists.
        check_image = subprocess.run(
            ['docker', 'inspect', image], stdout=subprocess.PIPE, check=True)
        # Exit from the module if the user input implementation image name does not exist
        if check_image.returncode != 0:
            sys.exit(
                f'Error: No image exists with the input container name: {image}')

    # Retrieve the zone domain name from the input zone file.
    zone_domain = ''
    with open(zone_file, 'r') as zone_pointer:
        for line in zone_pointer:
            if 'SOA' in line:
                zone_domain = line.split('\t')[0]
    if not zone_domain:
        sys.exit(f'Error: SOA not found in {zone_file}')

    # Check if a container with the input name is running.
    check_status = subprocess.run(
        ['docker', 'ps', '--format', '"{{.Names}}"'], stdout=subprocess.PIPE, check=True)
    output = check_status.stdout.decode("utf-8")
    if check_status.returncode != 0:
        sys.exit(f'Error in executing Docker ps command: {output}')
    if image:
        if cname:
            if cname in output:
                sys.exit(
                    f'Error: Cannot start a container with name {cname} as it exists already')
            else:
                start_container = subprocess.run(['docker', 'run', '-dp', str(
                    port)+':53/udp', '--name=' + cname, image], stdout=subprocess.PIPE, check=True)
        else:
            start_container = subprocess.run(['docker', 'run', '-dp', str(port)+':53/udp',
                                              image], stdout=subprocess.PIPE, check=True)
        if start_container.returncode != 0:
            sys.exit(f'Unable to a start a container for {image}')
        cid = start_container.stdout.decode("utf-8").strip()
    else:
        if not cname or cname not in output:
            sys.exit(f'No container exists with the name: {cname}')
    # Get name of the container
    get_name = subprocess.run(['docker', 'inspect', '--format',
                               '"{{.Name}} {{.Config.Image}}"', cid],
                              stdout=subprocess.PIPE, check=True)
    if get_name.returncode != 0:
        sys.exit(
            f'Error: Docker inspect failed when getting name for the container with id: {cid}')
    cname, image_name = get_name.stdout.decode("utf-8").strip("/\n\"").split()
    globals()[image_name.split(":")[0]](
        zone_file, zone_domain, cname, port, "False", tag)


if __name__ == '__main__':

    parser = ArgumentParser(formatter_class=RawTextHelpFormatter,
                            description='Gets an implementation to serve the input or '
                            'default zone file.\nSpecify an image name and a port to '
                            'start a fresh container (also container name if you want to'
                            'assign a name) or only the name of an existing container to reuse it.')
    parser.add_argument('-z', metavar='ZONE_FILE_PATH', type=FileType('r'), default='db.campus.edu',
                        help='The path to the zone file to be served. (default: db.campus.edu.)')
    parser.add_argument('-i', type=str, choices={'bind', 'nsd', 'knot', 'powerdns', 'coredns',
                                                 'yadifa', 'maradns', 'trustdns'},
                        help='The docker image name of the implementation to start a container.')
    parser.add_argument('-p', metavar='UNUSED_PORT', type=int,
                        help='An unused host port to map to port 53 of the container.')
    parser.add_argument('-c', metavar='CONTAINER_NAME', type=str,
                        help='A name for the container. (default: Random Docker generated name)')
    parser.add_argument(
        '-l', '--latest', help='Serve using the latest image.', action="store_true")
    args = parser.parse_args()
    if (args.i and not args.p) or (not args.i and args.p):
        sys.exit('Error: Specify both the image and port arguments (not just one) to '
                 'start a fresh container.')
    if not args.i and not args.p and not args.c:
        sys.exit('Error: Specify either an image name and a port to start a fresh '
                 'container (also container name if you want to assign a name) or '
                 'only the name of an existing container to reuse it.')
    load_and_serve_zone_file(pathlib.Path(args.z.name),
                             args.i, args.c, args.p, args.latest)
