"""
Script copies the input zone file and the necessary configuration file "Corefile"
into an existing or a new CoreDNS container and starts the DNS server on container
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
                        cname, 'coredns' + tag], stdout=subprocess.PIPE, check=False)
    else:
        # Kill the running server instance inside the container
        subprocess.run(['docker', 'exec', cname, 'pkill',
                        'coredns'], stdout=subprocess.PIPE, check=False)
    # Copy the new zone file into the container
    subprocess.run(['docker', 'cp', str(zone_file), cname +
                    ':/go/coredns'], stdout=subprocess.PIPE, check=False)
    # Create the CoreDNS-specific configuration file
    corefile = f'{zone_domain}:53 {{\n\tfile {zone_file.name}\n\tlog\n\terrors\n}}'
    with open('Corefile_' + cname, 'w') as file_pointer:
        file_pointer.write(corefile)
    # Copy the configuration file into the container as "Corefile"
    subprocess.run(['docker', 'cp', 'Corefile_' + cname, cname +
                    ':/go/coredns/Corefile'], stdout=subprocess.PIPE, check=False)
    pathlib.Path('Corefile_' + cname).unlink()
    # Start the server
    subprocess.run(['docker', 'exec', '-d', cname, './coredns'],
                   stdout=subprocess.PIPE, check=False)
