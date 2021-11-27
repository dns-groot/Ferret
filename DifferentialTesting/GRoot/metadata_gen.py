"""
Small script to generate the required metadata.json for GRoot
to generate the query equivalence classes.
https://github.com/dns-groot/groot#packaging-zone-files-data
"""

import json
import sys

metadata = {}
metadata["TopNameServers"] = ["ns1.campus.edu."]
metadata["ZoneFiles"] = [
    {"FileName": sys.argv[1], "NameServer": "ns1.campus.edu."}]
with open('/home/groot/groot/build/bin/zonefile/metadata.json', 'w') as f:
    json.dump(metadata, f)
