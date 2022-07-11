"""
Script copies the input zone file and the necessary configuration file "nsd.conf"
into an existing or a new NSD container and starts the DNS server on container
port 53, which is mapped to a host port.
"""

#!/usr/bin/env python3

import pathlib
import subprocess

# Zone file has to have a new line at the end for NSD to accept it without any issues.


def run(zone_file: pathlib.Path, zone_domain: str, cname: str, port: int, restart: bool, tag: str) -> None:
    """
    :param zone_file: Path to the Bind-style zone file
    :param zone_domain: The domain name of the zone
    :param cname: Container name
    :param port: The host port which is mapped to the port 53 of the container
    :param restart: Whether to load the input zone file in a new container
                        or reuse the existing container
    :param tag: The image tag to be used if restarting the container
    """
    if restart:
        subprocess.run(['docker', 'container', 'rm', cname, '-f'],
                       stdout=subprocess.PIPE, check=False)
        subprocess.run(['docker', 'run', '-dp', str(port)+':53/udp',
                        '--name=' + cname, 'nsd' + tag], stdout=subprocess.PIPE, check=False)
    else:
        # Stop the running server instance inside the container
        subprocess.run(
            ['docker', 'exec', cname, 'nsd-control', 'stop'], stdout=subprocess.PIPE, check=False)
    # Copy the new zone file into the container
    subprocess.run(['docker', 'cp', str(zone_file),
                    cname + ':/etc/nsd/zones'], stdout=subprocess.PIPE, check=False)
    # Create the NSD-specific configuration file
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
    # Copy the configuration file into the container as "nsd.conf"
    subprocess.run(['docker', 'cp', 'nsd_'+cname+'.conf',
                    cname + ':/etc/nsd/nsd.conf'], stdout=subprocess.PIPE, check=False)
    pathlib.Path('nsd_'+cname+'.conf').unlink()
    # Start the server
    subprocess.run(['docker', 'exec', cname, 'nsd-control',
                    'start'], stdout=subprocess.PIPE, check=False)
