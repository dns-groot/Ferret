"""
Script copies the input zone file and the necessary configuration file "knot.conf"
into an existing or a new Knot container and starts the DNS server on container
port 53, which is mapped to a host port.
"""

#!/usr/bin/env python3

import pathlib
import subprocess


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
        subprocess.run(['docker', 'run', '-dp', str(port)+':53/udp', '--name=' +
                        cname, 'knot' + tag], stdout=subprocess.PIPE, check=False)
    else:
        # Stop the running server instance inside the container
        subprocess.run(['docker', 'exec', cname, 'knotc', '-c',
                        '/usr/local/etc/knot/knot.conf', 'stop'],
                       stdout=subprocess.PIPE, check=False)
    # Copy the new zone file into the container
    subprocess.run(['docker', 'cp', zone_file, cname +
                    ':/usr/local/var/lib/knot/'], stdout=subprocess.PIPE, check=False)
    # Create the Knot-specific configuration file
    knot_conf = 'server:\n    listen: 0.0.0.0@53\n    listen: ::@53\n    rundir: "/usr/local/var/run/knot"\n\n'
    knot_conf += f'zone:\n  - domain: {zone_domain}\n    storage: /usr/local/var/lib/knot/\n    file: {zone_file.name}\n\n'
    knot_conf += 'log:\n  - target: /var/log/knot.log\n    any: debug'
    with open('knot_'+cname+'.conf', 'w') as file_pointer:
        file_pointer.write(knot_conf)
    # Copy the configuration file into the container as "knot.conf"
    subprocess.run(['docker', 'cp', 'knot_'+cname+'.conf',
                    cname + ':/usr/local/etc/knot/knot.conf'], stdout=subprocess.PIPE, check=False)
    pathlib.Path('knot_'+cname+'.conf').unlink()
    # Convert the zone file to Unix style (CRLF to LF)
    subprocess.run(['docker', 'exec', cname, 'dos2unix', '/usr/local/var/lib/knot/' +
                    zone_file.name], stdout=subprocess.PIPE, check=False)
    # Start the server
    subprocess.run(['docker', 'exec', cname, 'knotd', '-d', '-c',
                    '/usr/local/etc/knot/knot.conf'], stdout=subprocess.PIPE, check=False)
