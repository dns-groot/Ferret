"""
Builds docker images for the implementations.
Creates and prints logs to the image_generation_log.txt file.

usage: generate_docker_images.py [-h] [-l] [-b] [-n] [-k] [-p] [-c] [-y] [-m] [-t]

optional arguments:
  -h, --help    show this help message and exit
  -l, --latest  Build the images using latest code for all implementations. (default: False)
  -b            Disable Bind. (default: False)
  -n            Disable Nsd. (default: False)
  -k            Disable Knot. (default: False)
  -p            Disable PowerDns. (default: False)
  -c            Disable CoreDns. (default: False)
  -y            Disable Yadifa. (default: False)
  -m            Disable MaraDns. (default: False)
  -t            Disable TrustDns. (default: False)
"""
#!/usr/bin/env python3

import os
import platform
import subprocess
import time
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from multiprocessing import Process
from typing import TextIO
from datetime import datetime

def build_docker_images(implementation: str, latest: bool, log_fp: TextIO) -> None:
    """
    Builds the docker image for the input implementation.
    Expects a directory with the implementation name (first letter capitalized) in the
    "Implementations" directory with a Dockerfile in the directory.

    :param cmd: The name of the implementation to the build the image for.
    :param latest: Whether to build the image using latest code.
    :param log_fp: Log file pointer.
    """
    if latest:
        implementation += ':latest'
        run_cmd = ['docker', 'build', '-t', implementation + ":latest", '-f',
                   implementation.capitalize() + "/Dockerfile", '--no-cache',
                   '--build-arg', 'latest=true', '.']
    else:
        run_cmd = ['docker', 'build', '-t',
                   implementation + ":oct", '-f', implementation.capitalize() + "/Dockerfile", '.']
    log_fp.write(f'{datetime.now()}\tBuilding image for {implementation}.\n')
    begin_time = time.time()
    if platform.system() == 'Linux':
        my_env = os.environ.copy()
        my_env['DOCKER_BUILDKIT'] = '1'
        cmd_output = subprocess.run(
            run_cmd, env=my_env, stdout=subprocess.PIPE, cwd='Implementations/', check=True)
    else:
        cmd_output = subprocess.run(
            run_cmd, stdout=subprocess.PIPE, cwd='Implementations/', check=True)
    if cmd_output.returncode != 0:
        log_fp.write(f'{datetime.now()}\tError in building image for {implementation}.\n')
    else:
        log_fp.write(
            f'{datetime.now()}\tTime to build {implementation} image: {time.time()-begin_time}s\n')


if __name__ == '__main__':
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter,
                            description='Builds docker images for the implementations.'
                            ' (check image_generation_log.txt for logs)')
    parser.add_argument(
        '-l', '--latest', help='Build the images using latest code.', action="store_true")
    parser.add_argument('-b', help='Disable Bind.', action="store_true")
    parser.add_argument('-n', help='Disable Nsd.', action="store_true")
    parser.add_argument('-k', help='Disable Knot.', action="store_true")
    parser.add_argument('-p', help='Disable PowerDns.', action="store_true")
    parser.add_argument('-c', help='Disable CoreDns.', action="store_true")
    parser.add_argument('-y', help='Disable Yadifa.', action="store_true")
    parser.add_argument('-m', help='Disable MaraDns.', action="store_true")
    parser.add_argument('-t', help='Disable TrustDns.', action="store_true")
    args = parser.parse_args()
    cmds = []
    if not args.b:
        cmds.append("bind")
    if not args.k:
        cmds.append("knot")
    if not args.n:
        cmds.append("nsd")
    if not args.p:
        cmds.append("powerdns")
    if not args.c:
        cmds.append("coredns")
    if not args.y:
        cmds.append("yadifa")
    if not args.m:
        cmds.append("maradns")
    if not args.t:
        cmds.append("trustdns")
    processPool = []
    i = 0
    j = len(cmds)
    start = time.time()
    with open('image_generation_log.txt', 'w', 1) as log:
        while j:
            processPool.append(
                Process(target=build_docker_images, args=(cmds[i], args.latest, log)))
            i = i+1
            j = j - 1
        for t in processPool:
            t.start()
        for t in processPool:
            t.join()
        log.write(f'{datetime.now()}\tTime taken to build all images: {time.time()-start}s\n')
