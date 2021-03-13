#!/usr/bin/env python3

import os
import platform
import subprocess
import time
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from multiprocessing import Manager, Process


def build_docker_images(cmd, latest):
    image_name = cmd.split(' ')[3]
    if latest:
        image_name += ':latest'
        run_cmd = ['docker', 'build', '-t', image_name, '-f',
                   cmd.split(' ')[5], '--no-cache', '--build-arg', 'latest=true', '.']
    else:
        image_name += ':oct'
        run_cmd = ['docker', 'build', '-t',
                   image_name, '-f', cmd.split(' ')[5], '.']
    print(f'Building image for {image_name}.')
    start = time.time()
    if platform.system() == 'Linux':
        my_env = os.environ.copy()
        my_env['DOCKER_BUILDKIT'] = '1'
        cmd_output = subprocess.run(
            run_cmd, env=my_env, stdout=subprocess.PIPE, cwd='Implementations/')
    else:
        cmd_output = subprocess.run(
            run_cmd, stdout=subprocess.PIPE, cwd='Implementations/')
    if cmd_output.returncode != 0:
        print(f'Error in building image for {image_name}.')
    else:
        print(
            f'Time taken to build image for {image_name}: {time.time()-start}s')


if __name__ == '__main__':
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter,
                            description='Builds docker images for the implementations.')
    parser.add_argument(
        '-l', '--latest', help='Build the images using latest code.', action="store_true")
    parser.add_argument('-b',  help='Disable Bind.', action="store_true")
    parser.add_argument('-n',  help='Disable Nsd.', action="store_true")
    parser.add_argument('-k',  help='Disable Knot.', action="store_true")
    parser.add_argument('-p',  help='Disable PowerDns.', action="store_true")
    parser.add_argument('-c',  help='Disable CoreDns.', action="store_true")
    parser.add_argument('-y',  help='Disable Yadifa.', action="store_true")
    parser.add_argument('-m',  help='Disable MaraDns.', action="store_true")
    parser.add_argument('-t',  help='Disable TrustDns.', action="store_true")
    args = parser.parse_args()
    cmds = []
    if not args.b:
        cmds.append("docker build -t bind -f Bind/Dockerfile .")
    if not args.k:
        cmds.append("docker build -t knot -f Knot/Dockerfile .")
    if not args.n:
        cmds.append("docker build -t nsd -f Nsd/Dockerfile .")
    if not args.p:
        cmds.append("docker build -t powerdns -f Powerdns/Dockerfile .")
    if not args.c:
        cmds.append("docker build -t coredns -f Coredns/Dockerfile .")
    if not args.y:
        cmds.append("docker build -t yadifa -f Yadifa/Dockerfile .")
    if not args.m:
        cmds.append("docker build -t maradns -f Maradns/Dockerfile .")
    if not args.t:
        cmds.append("docker build -t trustdns -f Trustdns/Dockerfile .")
    processPool = []
    i = 0
    jobs = len(cmds)
    start = time.time()
    while jobs:
        processPool.append(
            Process(target=build_docker_images, args=(cmds[i], args.latest)))
        i = i+1
        jobs = jobs - 1
    for t in processPool:
        t.start()
    for t in processPool:
        t.join()
    print(f'Time taken to build all images: {time.time()-start}s')
