#!/usr/bin/env python3

import pathlib
import subprocess


def run(zone_file, zone_domain, cname, port, restart, tag):

    if restart:
        subprocess.run(['docker', 'container', 'rm', cname, '-f'],
                       stdout=subprocess.PIPE)
        subprocess.run(['docker', 'run', '-dp', str(port)+':53/udp',
                        '--name=' + cname, 'knot' + tag], stdout=subprocess.PIPE)
    else:
        subprocess.run(
            ['docker', 'exec', cname, 'knotc',
             '-c', '/usr/local/etc/knot/knot.conf', 'stop'], stdout=subprocess.PIPE)

    subprocess.run(['docker', 'cp', zone_file,
                    cname + ':/usr/local/var/lib/knot/'], stdout=subprocess.PIPE)

    knotConf = f'server:\n    listen: 0.0.0.0@53\n    listen: ::@53\n    rundir: "/usr/local/var/run/knot"\n\n'
    knotConf += f'zone:\n  - domain: {zone_domain}\n    storage: /usr/local/var/lib/knot/\n    file: {zone_file.name}\n\n'
    knotConf += f'log:\n  - target: /var/log/knot.log\n    any: debug'
    with open('knot_'+cname+'.conf', 'w') as f:
        f.write(knotConf)
    subprocess.run(['docker', 'cp', 'knot_'+cname+'.conf',
                    cname + ':/usr/local/etc/knot/knot.conf'], stdout=subprocess.PIPE)
    pathlib.Path('knot_'+cname+'.conf').unlink()
    subprocess.run(['docker', 'exec', cname, 'dos2unix',
                    '/usr/local/var/lib/knot/' + zone_file.name], stdout=subprocess.PIPE)
    subprocess.run(['docker', 'exec', cname, 'knotd',
                    '-d', '-c', '/usr/local/etc/knot/knot.conf'], stdout=subprocess.PIPE)
