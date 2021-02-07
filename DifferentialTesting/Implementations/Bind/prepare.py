#!/usr/bin/env python3

import pathlib
import subprocess


def run(zone_file, zone_domain, cname, port, restart):
    if restart:
        subprocess.run(['docker', 'container', 'rm', cname, '-f'],
                       stdout=subprocess.PIPE)
        subprocess.run(['docker', 'run', '-dp', str(port)+':53/udp',
                        '--name=' + cname, 'bind'],
                       stdout=subprocess.PIPE)
    else:
        subprocess.run(
            ['docker', 'exec', cname, 'pkill', 'named'])

    subprocess.run(['docker', 'cp', zone_file,
                    cname + ':/usr/local/etc'], stdout=subprocess.PIPE)
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
    with open('named_'+cname+'.conf', 'w') as f:
        f.write(named)
    subprocess.run(['docker', 'cp', 'named_'+cname+'.conf',
                    cname + ':/usr/local/etc/named.conf'], stdout=subprocess.PIPE)
    pathlib.Path('named_'+cname+'.conf').unlink()
    subprocess.run(['docker', 'exec', cname, 'named'], stdout=subprocess.PIPE)
    subprocess.run(['docker', 'exec', cname, 'rndc',
                    'flush'], stdout=subprocess.PIPE)
