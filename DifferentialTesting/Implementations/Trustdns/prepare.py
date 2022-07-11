"""
Script copies the input zone file and the necessary configuration file "config.toml"
into an existing or a new TrustDNS container and starts the DNS server on container
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
                        '--name=' + cname, 'trustdns' + tag], stdout=subprocess.PIPE, check=False)
    else:
        # Kill the running server instance inside the container
        subprocess.run(
            ['docker', 'exec', cname, 'pkill', 'named'], stdout=subprocess.PIPE, check=False)
    # Copy the new zone file into the container
    subprocess.run(['docker', 'cp', str(zone_file), cname +
                    ':trust-dns/tests/test-data/named_test_configs/'],
                   stdout=subprocess.PIPE, check=False)
    # Create the TrustDNS-specific configuration file
    config = f'[[zones]]\nzone = "{zone_domain}"\nzone_type = "Primary"\nfile = "{zone_file.name}"'
    with open(cname + '_config.toml', 'w') as file_pointer:
        file_pointer.write(config)
    # Copy the configuration file into the container as "config.toml"
    subprocess.run(['docker', 'cp', cname + '_config.toml', cname +
                    ':trust-dns/tests/test-data/named_test_configs/config.toml'],
                   stdout=subprocess.PIPE, check=False)
    pathlib.Path(cname + '_config.toml').unlink()
    # Start the server
    subprocess.run(['docker', 'exec', '-d', cname, '/trust-dns/target/release/named', '-c',
                    '/trust-dns/tests/test-data/named_test_configs/config.toml',
                    '-z', '/trust-dns/tests/test-data/named_test_configs'],
                   stdout=subprocess.PIPE, check=False)
