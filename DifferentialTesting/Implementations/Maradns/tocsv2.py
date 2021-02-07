import sys
import os
import re
import string
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
        joined  = '\t'.join(parts)
        joined += ' ~\n'
        csv2.append(joined)
    with open(filePath.parent / (filePath.name + '.csv2'), 'w') as c:
        c.writelines(csv2)

