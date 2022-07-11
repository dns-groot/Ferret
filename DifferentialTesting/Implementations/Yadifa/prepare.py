"""
Script copies the input zone file and the necessary configuration file "yadifad.conf"
into an existing or a new Yadifa container and starts the DNS server on container
port 53, which is mapped to a host port.
"""

#!/usr/bin/env python3

import pathlib
import subprocess
import time


YADIFAD = '''
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
                        '--name=' + cname, 'yadifa' + tag], stdout=subprocess.PIPE, check=False)
    else:
        # Stop the running server instance inside the container
        output = subprocess.run(['docker', 'exec', cname, 'yadifa', 'ctrl', '-y',
                                 'controller-key:ControlDaemonKey', 'shutdown'],
                                stdout=subprocess.PIPE, check=False)
        # Yadifa sometimes does not stop the server and might require sending the stop command again
        if output.returncode != 0:
            time.sleep(2)
            subprocess.run(['docker', 'exec', cname, 'yadifa', 'ctrl', '-y',
                            'controller-key:ControlDaemonKey', 'shutdown'],
                           stdout=subprocess.PIPE, check=False)
    # Copy the new zone file into the container
    subprocess.run(['docker', 'cp', str(zone_file),
                    cname + ':/usr/local/var/zones/masters/'], stdout=subprocess.PIPE, check=False)
    # Create the Yadifa-specific configuration file
    with open('yadifad_'+cname+'.conf', 'w') as tmp:
        tmp.write(YADIFAD.format(zone_domain, zone_file.name))
    # Copy the configuration file into the container as "yadifad.conf"
    subprocess.run(['docker', 'cp', 'yadifad_'+cname+'.conf',
                    cname + ':/usr/local/etc/yadifad.conf'], stdout=subprocess.PIPE, check=False)
    pathlib.Path('yadifad_'+cname+'.conf').unlink()
    # Start the server
    server_start = subprocess.run(
        ['docker', 'exec', cname, 'yadifad', '-d'], stdout=subprocess.PIPE, check=False)
    if server_start.returncode != 0:
        time.sleep(2)
        subprocess.run(['docker', 'exec', cname,
                        'yadifad', '-d'], stdout=subprocess.PIPE, check=False)
