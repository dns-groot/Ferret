#!/usr/bin/env python3

import pathlib
import subprocess

# Maradns seems to work easily on Centos compared to Ubuntu as mentioned on the website.
# Start MaraDNS from the terminal inside the container using `maradns` to see the logs on stdout.


def run(zone_file, zone_domain, cname, port, restart):

    if restart:
        subprocess.run(['docker', 'container', 'rm', cname, '-f'],
                       stdout=subprocess.PIPE)
        subprocess.run(['docker', 'run', '-dp', str(port)+':53/udp',
                        '--name=' + cname, 'maradns'], stdout=subprocess.PIPE)
    else:
        subprocess.run(['docker', 'exec', cname,
                        '/etc/init.d/maradns', 'stop'], stdout=subprocess.PIPE)

    subprocess.run(['docker', 'cp', zone_file,
                    cname + ':/etc/maradns'], stdout=subprocess.PIPE)

    mararc = f'ipaddr=\\"$(hostname -i)\\"\necho "ipv4_bind_addresses = $ipaddr"\n'
    mararc += f'echo \'chroot_dir = "/etc/maradns"\'\necho \'csv2 = {{}}\'\n'
    mararc += f'echo \'csv2["{zone_domain}"] = "{zone_file.name + ".csv2"}"\''

    with open(cname + '_mararc.sh', 'w') as f:
        f.write(mararc)
    subprocess.run(['docker', 'cp', cname + '_mararc.sh',
                    cname + ':/etc/mararc.sh'])
    pathlib.Path(cname + '_mararc.sh').unlink()
    subprocess.run(['docker', 'exec', cname,
                    'chmod', '+x', '/etc/mararc.sh'], stdout=subprocess.PIPE)
    subprocess.run(['docker', 'exec', cname, 'python3',
                    'tocsv2.py', f'/etc/maradns/{zone_file.name}'], stdout=subprocess.PIPE)
    subprocess.run(['docker', 'exec', cname, 'sh',
                    '-c', './etc/mararc.sh > /etc/mararc'], stdout=subprocess.PIPE)
    subprocess.run(['docker', 'exec', cname,
                    '/etc/init.d/maradns', 'start'], stdout=subprocess.PIPE)
