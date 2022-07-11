"""
Script copies the input zone file and the necessary configuration file "bindbackend.conf"
into an existing or a new PowerDNS container and starts the DNS server on container
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
        subprocess.run(['docker', 'run', '-dp', str(port)+':53/udp',
                        '--name=' + cname, 'powerdns' + tag], stdout=subprocess.PIPE, check=False)
    else:
        # Kill the running server instance inside the container
        subprocess.run(['docker', 'exec', cname, 'pkill',
                        'pdns_server'], stdout=subprocess.PIPE, check=False)
    # Copy the new zone file into the container
    subprocess.run(['docker', 'cp', str(zone_file), cname +
                    ':/usr/local/etc'], stdout=subprocess.PIPE, check=False)
    # Create the PowerDNS-specific configuration file
    bindbackend = f'zone "{zone_domain}" {{\n  file "/usr/local/etc/{zone_file.name}";\n  type master;\n}};'
    with open('bindbackend_'+cname+'.conf', 'w') as file_pointer:
        file_pointer.write(bindbackend)
    # Copy the configuration file into the container as "bindbackend.conf"
    subprocess.run(['docker', 'cp', 'bindbackend_'+cname+'.conf',
                    cname + ':/usr/local/etc/bindbackend.conf'], stdout=subprocess.PIPE, check=False)
    pathlib.Path('bindbackend_'+cname+'.conf').unlink()
    # "bindbackend.conf" has to be in UNIX style otherwise this error is thrown --
    # Caught an exception instantiating a backend: Error in bind
    # configuration '..bindbackend.conf' on line 2: syntax error
    subprocess.run(['docker', 'exec', cname, 'dos2unix',
                    '/usr/local/etc/bindbackend.conf'], stdout=subprocess.PIPE, check=False)
    subprocess.run(['docker', 'exec', cname,
                    'pdns_server', '--daemon'], stdout=subprocess.PIPE, check=False)
