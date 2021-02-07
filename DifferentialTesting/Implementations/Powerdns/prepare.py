#!/usr/bin/env python3

import pathlib
import subprocess


def run(zone_file, zone_domain, cname, port, restart):

    if restart:
        subprocess.run(['docker', 'container', 'rm', cname, '-f'],
                       stdout=subprocess.PIPE)
        subprocess.run(['docker', 'run', '-dp', str(port)+':53/udp',
                        '--name=' + cname, 'powerdns'], stdout=subprocess.PIPE)
    else:
        subprocess.run(
            ['docker', 'exec', cname, 'pkill', 'pdns_server'], stdout=subprocess.PIPE)

    subprocess.run(['docker', 'cp', zone_file,
                    cname + ':/usr/local/etc'], stdout=subprocess.PIPE)

    bindbackend = f'zone "{zone_domain}" {{\n  file "/usr/local/etc/{zone_file.name}";\n  type master;\n}};'
    with open('bindbackend_'+cname+'.conf', 'w') as f:
        f.write(bindbackend)
    subprocess.run(['docker', 'cp', 'bindbackend_'+cname+'.conf',
                    cname + ':/usr/local/etc/bindbackend.conf'], stdout=subprocess.PIPE)
    pathlib.Path('bindbackend_'+cname+'.conf').unlink()
    # `bindbackend.conf` has to be in UNIX style otherwise this error is thrown --
    # `Caught an exception instantiating a backend: Error in bind configuration '..bindbackend.conf' on line 2: syntax error`.
    subprocess.run(['docker', 'exec', cname,
                    'dos2unix', '/usr/local/etc/bindbackend.conf'], stdout=subprocess.PIPE)
    subprocess.run(['docker', 'exec', cname,
                    'pdns_server', '--daemon'], stdout=subprocess.PIPE)
