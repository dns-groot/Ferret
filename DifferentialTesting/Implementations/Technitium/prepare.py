"""
Script use Technitium HTTP API to create a new zone and add records. It also deletes all the zones except the default ones.
The DNS server is started on the container port 53, which is mapped to a host port.
"""

#!/usr/bin/env python3

import copy
import pathlib
import subprocess
import time
from subprocess import DEVNULL

import requests

import dns.zone
from dns.rdatatype import RdataType


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
        subprocess.run(['docker', 'run', '-dp', str(port) + ':53/udp', '-p', f'{str(port + 1)}:5380/tcp',
                        '--name=' + cname, "technitium" + tag], check=True)
    else:
        # Stop the running server instance inside the container
        subprocess.run(['docker', 'exec', cname, 'pkill', '-9', '-f', 'DnsServerApp.dll'],
                       stdout=subprocess.PIPE, check=False)
    # Start the server
    subprocess.Popen(['docker', 'exec', cname, 'dotnet',
                     'DnsServer/DnsServerApp/bin/Release/publish/DnsServerApp.dll'], stdout=DEVNULL, stderr=DEVNULL)
    time.sleep(2)

    login_url = f'http://localhost:{str(port + 1)}/api/user/login'
    login_data = {"user": "admin", "pass": "admin"}

    response = requests.post(login_url, data=login_data)
    if response.status_code == 200 and response.json()['status'] != "error":
        token = response.json()['token']
        default_zones = ["0.in-addr.arpa", "1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.ip6.arpa",
                         "127.in-addr.arpa", "255.in-addr.arpa", "localhost", "ntp.org"]
        zones_list_url = f'http://localhost:{str(port + 1)}/api/zones/list'
        zones_list_data = {"token": token}
        response = requests.post(zones_list_url, data=zones_list_data)
        if response.status_code == 200 and response.json()['status'] != "error":
            zones_list = response.json()['response']['zones']
            delete_zones = []
            for zone in zones_list:
                if zone["name"] not in default_zones:
                    delete_zones.append(zone["name"])
            for delete_zone in delete_zones:
                zones_delete_url = f'http://localhost:{str(port + 1)}/api/zones/delete'
                zones_delete_data = {"token": token, "zone": delete_zone}
                response = requests.post(
                    zones_delete_url, data=zones_delete_data)
                if response.status_code != 200 or response.json()['status'] == "error":
                    print(
                        f"Zones delete request for {delete_zone} failed with status code {response.status_code} and response {response.json()}")
            zones_add_url = f'http://localhost:{str(port + 1)}/api/zones/create'
            zones_add_data = {"token": token, "zone": zone_domain}
            response = requests.post(zones_add_url, data=zones_add_data)
            if response.status_code == 200 and response.json()['status'] != "error":
                # read the input zone file
                try:
                    zone = dns.zone.from_file(
                        str(zone_file), relativize=False, origin=zone_domain)
                    soa_rdict = {}
                    ns_count = 0
                    for name, node in zone.nodes.items():
                        rdatasets = node.rdatasets
                        for rdataset in rdatasets:
                            for rdata in rdataset:
                                rdata_dict = {"type": dns.rdatatype.to_text(rdata.rdtype),
                                              "ttl": rdataset.ttl,
                                              "zone": zone_domain,
                                              "domain": name.to_text(),
                                              "token": token}
                                if rdata.rdtype == RdataType.SOA:
                                    rdata_dict.update({
                                        "primaryNameServer": rdata.mname.to_text(),
                                        "responsiblePerson": rdata.rname.to_text(),
                                        "serial": rdata.serial,
                                        "refresh": rdata.refresh,
                                        "retry": rdata.retry,
                                        "expire": rdata.expire,
                                        "minimum": rdata.minimum,
                                    })
                                    soa_rdict = copy.deepcopy(rdata_dict)
                                else:
                                    add_url = f'http://localhost:{str(port + 1)}/api/zones/records/add'
                                    if rdata.rdtype == RdataType.A or rdata.rdtype == RdataType.AAAA:
                                        rdata_dict.update({
                                            "ipAddress": rdata.address,
                                        })
                                    elif rdata.rdtype == RdataType.CNAME:
                                        rdata_dict.update({
                                            "cname": rdata.target.to_text(),
                                        })
                                    elif rdata.rdtype == RdataType.DNAME:
                                        rdata_dict.update({
                                            "dname": rdata.target.to_text(),
                                        })
                                    elif rdata.rdtype == RdataType.TXT:
                                        rdata_dict.update({
                                            "text": rdata.strings[0].decode(),
                                        })
                                    elif rdata.rdtype == RdataType.NS:
                                        rdata_dict.update({
                                            "nameServer": rdata.target.to_text(),
                                        })
                                        if name.to_text() == zone_domain:
                                            if ns_count == 0:
                                                rdata_dict.update({
                                                    "overwrite": True,
                                                })
                                            ns_count += 1
                                    response = requests.post(
                                        add_url, data=rdata_dict)
                                    if response.status_code != 200 or response.json()['status'] == "error":
                                        print(
                                            f"Add record for zone {zone_file.stem} failed with status code {response.status_code} and response {response.json()}")
                    #  update SOA record in the end to avoid incrementing the serial number
                    update_url = f'http://localhost:{str(port + 1)}/api/zones/records/update'
                    soa_rdict["serial"] = 10
                    response = requests.post(update_url, data=soa_rdict)
                    if response.status_code != 200 or response.json()['status'] == "error":
                        print(
                            f"Zones update request for zone {zone_file.stem} for SOA failed with status code {response.status_code} and response {response.json()}")
                except Exception as e:
                    print(
                        f"An error occurred while reading the zone file ({zone_file.stem}): {e}")
            else:
                print(
                    f"Zones add request failed with status code {response.status_code} for zone {zone_file.stem} and response {response.json()}")
        else:
            print(
                f"Zones list request failed with status code {response.status_code} for zone {zone_file.stem} and response {response.json()}")
    else:
        print(
            f"Login request failed with status code {response.status_code} for zone {zone_file.stem} and response {response.json()}")
