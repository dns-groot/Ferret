"""
Script copies the input zone file and a script "mararc.sh" which,
when run in the container, generates the necessary configuration file "mararc"
into an existing or a new MaraDNS container and starts the DNS server
on container port 53, which is mapped to a host port.
"""

#!/usr/bin/env python3

import pathlib
import subprocess

# Maradns seems to work easily on Centos compared to Ubuntu as mentioned on the website.
# Start MaraDNS from the terminal inside the container using `maradns` to see the logs on stdout.


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
                        '--name=' + cname, 'maradns' + tag], stdout=subprocess.PIPE, check=False)
    else:
        # Stop the running server instance inside the container
        subprocess.run(['docker', 'exec', cname,
                        '/etc/init.d/maradns', 'stop'], stdout=subprocess.PIPE, check=False)
    # Copy the new zone file into the container
    subprocess.run(['docker', 'cp', str(zone_file),
                    cname + ':/etc/maradns'], stdout=subprocess.PIPE, check=False)
    # Shell script to run inside the container to generate the "mararc" configuration file
    # It has to be run in the container to get the container interface IP to which the
    # DNS server has to bind.
    mararc = 'ipaddr=\\"$(hostname -i)\\"\necho "ipv4_bind_addresses = $ipaddr"\n'
    mararc += 'echo \'chroot_dir = "/etc/maradns"\'\necho \'csv2 = {}\'\n'
    mararc += f'echo \'csv2["{zone_domain}"] = "{zone_file.name + ".csv2"}"\''

    with open(cname + '_mararc.sh', 'w') as file_pointer:
        file_pointer.write(mararc)
    subprocess.run(['docker', 'cp', cname + '_mararc.sh',
                    cname + ':/etc/mararc.sh'], check=False)
    pathlib.Path(cname + '_mararc.sh').unlink()
    # Give executable permissions to the copied script
    subprocess.run(['docker', 'exec', cname,
                    'chmod', '+x', '/etc/mararc.sh'], stdout=subprocess.PIPE, check=False)
    # Covnert the zone file into CSV2 format using the python script
    subprocess.run(['docker', 'exec', cname, 'python3', 'tocsv2.py',
                    f'/etc/maradns/{zone_file.name}'], stdout=subprocess.PIPE, check=False)
    # Generate the configuration file using the shell script
    subprocess.run(['docker', 'exec', cname, 'sh',
                    '-c', './etc/mararc.sh > /etc/mararc'], stdout=subprocess.PIPE, check=False)
    # Start the server
    subprocess.run(['docker', 'exec', cname,
                    '/etc/init.d/maradns', 'start'], stdout=subprocess.PIPE, check=False)
