#!/usr/bin/env python3

import pathlib
import subprocess
import time


yadifad = '''
<main>
        network-model               "single"
        logpath                     "/usr/local/var/log/yadifa"
        pidfile                     "/usr/local/var/run/yadifad.pid"
        datapath                    "/usr/local/var/zones/masters"
        keyspath                    "/usr/local/var/zones/keys"
        xfrpath                     "/usr/local/var/zones/xfr"
        group                        root
        listen                      0.0.0.0
        allow-notify                none
        allow-control              yadifa-controller
</main>

<channels>
#       name        stream-name     arguments
        database    database.log    0644
        dnssec      dnssec.log      0644
        server      server.log      0644
        statistics  statistics.log  0644
        system      system.log      0644
        zone        zone.log        0644
        queries     queries.log     0644
        all         all.log         0644
        syslog      syslog          USER,CRON,PID
        stderr      STDERR
        stdout      STDOUT
</channels>

<acl>
        yadifa-controller key controller-key
</acl>

<key>
        name            controller-key
        algorithm       hmac-md5
        secret          ControlDaemonKey
</key>

<loggers>
        #   bundle          debuglevel                          channels
        database        ALL                                 database,all
        dnssec          warning                             dnssec,all
        server          INFO,WARNING,ERR,CRIT,ALERT,EMERG   server,all
        statistics      *                                   statistics
        system          *                                   system,all
        queries         *                                   queries
        zone            *                                   zone,all
</loggers>

<key>
        name        master-slave
        algorithm   hmac-md5
        secret      MasterAndSlavesTSIGKey==
</key>


<zone>
        type                    master
        domain                  {}
        file                    {}
</zone>
'''


def run(zone_file, zone_domain, cname, port, restart, tag):

    if restart:
        subprocess.run(['docker', 'container', 'rm', cname, '-f'],
                       stdout=subprocess.PIPE)
        subprocess.run(['docker', 'run', '-dp', str(port)+':53/udp',
                        '--name=' + cname, 'yadifa' + tag], stdout=subprocess.PIPE)
    else:
        output = subprocess.run(['docker', 'exec', cname, 'yadifa',
                                 'ctrl', '-y', 'controller-key:ControlDaemonKey', 'shutdown'], stdout=subprocess.PIPE)
        if output.returncode != 0:
            time.sleep(3)
            subprocess.run(['docker', 'exec', cname, 'yadifa',
                            'ctrl', '-y', 'controller-key:ControlDaemonKey', 'shutdown'], stdout=subprocess.PIPE)

    subprocess.run(['docker', 'cp', zone_file,
                    cname + ':/usr/local/var/zones/masters/'], stdout=subprocess.PIPE)

    with open('yadifad_'+cname+'.conf', 'w') as tmp:
        tmp.write(yadifad.format(zone_domain, zone_file.name))
    subprocess.run(['docker', 'cp', 'yadifad_'+cname+'.conf',
                    cname + ':/usr/local/etc/yadifad.conf'], stdout=subprocess.PIPE)
    pathlib.Path('yadifad_'+cname+'.conf').unlink()
    server_start = subprocess.run(
        ['docker', 'exec', cname, 'yadifad', '-d'], stdout=subprocess.PIPE)
    if server_start.returncode != 0:
        time.sleep(3)
        subprocess.run(['docker', 'exec', cname,
                        'yadifad', '-d'], stdout=subprocess.PIPE)
