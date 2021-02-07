#!/usr/bin/env python3

import pathlib
import subprocess


def run(zone_file, zone_domain, cname, port, restart):

    if restart:
        subprocess.run(['docker', 'container', 'rm', cname, '-f'],
                       stdout=subprocess.PIPE)
        subprocess.run(['docker', 'run', '-dp', str(port)+':53/udp',
                        '--name=' + cname, 'trustdns'], stdout=subprocess.PIPE)
    else:
        subprocess.run(
            ['docker', 'exec', cname, 'pkill', 'named'], stdout=subprocess.PIPE)

    subprocess.run(['docker', 'cp', zone_file,
                    cname + ':trust-dns/tests/test-data/named_test_configs/'], stdout=subprocess.PIPE)

    config = f'[[zones]]\nzone = "{zone_domain}"\nzone_type = "Primary"\nfile = "{zone_file.name}"'
    with open(cname + '_config.toml', 'w') as f:
        f.write(config)
    subprocess.run(['docker', 'cp', cname + '_config.toml',
                    cname + ':trust-dns/tests/test-data/named_test_configs/config.toml'], stdout=subprocess.PIPE)
    pathlib.Path(cname + '_config.toml').unlink()
    subprocess.run(['docker', 'exec', '-d', cname, '/trust-dns/target/release/named', '-c',
                    '/trust-dns/tests/test-data/named_test_configs/config.toml', '-z', '/trust-dns/tests/test-data/named_test_configs'], stdout=subprocess.PIPE)
