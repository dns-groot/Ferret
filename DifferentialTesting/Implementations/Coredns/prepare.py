#!/usr/bin/env python3

import pathlib
import subprocess


def run(zone_file, zone_domain, cname, port, restart):

    if restart:
        subprocess.run(['docker', 'container', 'rm', cname, '-f'],
                       stdout=subprocess.PIPE)
        subprocess.run(['docker', 'run', '-dp', str(port)+':53/udp',
                        '--name=' + cname, 'coredns'], stdout=subprocess.PIPE)
    else:
        subprocess.run(
            ['docker', 'exec', cname, 'pkill', 'coredns'], stdout=subprocess.PIPE)

    subprocess.run(['docker', 'cp', zone_file,
                    cname + ':/go/coredns'], stdout=subprocess.PIPE)

    corefile = f'{zone_domain}:53 {{\n\tfile {zone_file.name}\n\tlog\n\terrors\n}}'
    with open('Corefile_' + cname, 'w') as f:
        f.write(corefile)
    subprocess.run(['docker', 'cp', 'Corefile_' + cname,
                    cname + ':/go/coredns/Corefile'], stdout=subprocess.PIPE)
    pathlib.Path('Corefile_' + cname).unlink()
    subprocess.run(['docker', 'exec', '-d', cname,
                    './coredns'], stdout=subprocess.PIPE)
