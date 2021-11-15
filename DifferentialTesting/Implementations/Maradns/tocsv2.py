"""
Script to convert Bind-style zone files to the MaraDNS CSV2 format
https://maradns.samiam.org/tutorial/man.csv2.html
"""
import sys
import pathlib

filePath = pathlib.Path(sys.argv[1])

with open(filePath, 'r') as f:
    csv2 = []
    for line in f:
        line = line[:-1]
        parts = line.split()
        parts[1] = '+' + parts[1]
        if parts[3] == 'TXT':
            parts[4] = parts[4][1:-1]
        JOINED = '\t'.join(parts)
        JOINED += ' ~\n'
        csv2.append(JOINED)
    with open(filePath.parent / (filePath.name + '.csv2'), 'w') as c:
        c.writelines(csv2)
