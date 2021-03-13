#!/usr/bin/env python3

import pathlib
import subprocess

# Zone file has to have a new line at the end for NSD to accept it without any issues.


def run(zone_file, zone_domain, cname, port, restart, tag):

    if restart:
        subprocess.run(['docker', 'container', 'rm', cname, '-f'],
                       stdout=subprocess.PIPE)
        subprocess.run(['docker', 'run', '-dp', str(port)+':53/udp',
                        '--name=' + cname, 'nsd'+ tag], stdout=subprocess.PIPE)
    else:
        subprocess.run(
            ['docker', 'exec', cname, 'nsd-control', 'stop'], stdout=subprocess.PIPE)

    subprocess.run(['docker', 'cp', zone_file,
                    cname + ':/etc/nsd/zones'], stdout=subprocess.PIPE)
    nsd_conf = f'''
server:

    server-count: 1
    ip4-only: yes
    zonesdir: "/etc/nsd/zones/"
    pidfile: "/var/run/nsd.pid"
    logfile: "/var/log/nsd.log"
    verbosity: 3
    username: root

remote-control:
        control-enable: yes

zone:
    name: {zone_domain}
    zonefile: {zone_file.name}
    '''
    with open('nsd_'+cname+'.conf', 'w') as tmp:
        tmp.write(nsd_conf)
    subprocess.run(['docker', 'cp', 'nsd_'+cname+'.conf',
                    cname + ':/etc/nsd/nsd.conf'], stdout=subprocess.PIPE)
    pathlib.Path('nsd_'+cname+'.conf').unlink()
    subprocess.run(['docker', 'exec', cname, 'nsd-control', 'start'], stdout=subprocess.PIPE)
