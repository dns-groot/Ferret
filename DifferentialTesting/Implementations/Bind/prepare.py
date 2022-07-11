"""
Script copies the input zone file and the necessary configuration file "named.conf"
into an existing or a new Bind container and starts the DNS server on container
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
                        '--name=' + cname, 'bind' + tag],
                       stdout=subprocess.PIPE, check=False)
    else:
        # Kill the running server instance inside the container
        subprocess.run(
            ['docker', 'exec', cname, 'pkill', 'named'], check=False)
    # Copy the new zone file into the container
    subprocess.run(['docker', 'cp', str(zone_file), cname +
                    ':/usr/local/etc'], stdout=subprocess.PIPE, check=False)
    # Create the Bind-specific configuration file
    named = f'''
    options{{
    recursion no;
    }};

    zone "{zone_domain}" {{
        type master;
        check-names ignore;
        file "{"/usr/local/etc/"+ zone_file.name}";
    }};
    '''
    with open('named_'+cname+'.conf', 'w') as file_pointer:
        file_pointer.write(named)
    # Copy the configuration file into the container as "named.conf"
    subprocess.run(['docker', 'cp', 'named_'+cname+'.conf', cname +
                    ':/usr/local/etc/named.conf'], stdout=subprocess.PIPE, check=False)
    pathlib.Path('named_'+cname+'.conf').unlink()
    # Start the server - When 'named' is run, Bind first reads the "named.conf" file to know
    #                   the settings and where the zone files are
    subprocess.run(['docker', 'exec', cname, 'named'],
                   stdout=subprocess.PIPE, check=False)
    subprocess.run(['docker', 'exec', cname, 'rndc', 'flush'],
                   stdout=subprocess.PIPE, check=False)
