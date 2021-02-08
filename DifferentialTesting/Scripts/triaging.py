
import json
import pathlib
import sys
from argparse import ArgumentParser
from collections import defaultdict


def cluster_tests(path):

    vectors = defaultdict(set)
    tags = set()
    for zone in (path / "Differences").iterdir():
        with open(zone, 'r') as f:
            data = json.load(f)
        groups = data["Groups"]
        with open(path / "QueryResponses" / zone.name, 'r') as q:
            qr = json.load(q)
            response_tag = qr["Response"]["Tag"]
            tags.add(response_tag)
        sets = []
        for group in groups:
            servers = set(group["Server/s"].strip().split())
            if len(servers):
                sets.append(frozenset(servers))
        if len(sets) > 1:
            vectors[(response_tag, frozenset(sets))].add(zone.stem)
    json_data = defaultdict(list)
    summary = []
    for tag in tags:
        for k, v in vectors.items():
            if k[0] == tag:
                groups = sorted(k[1], key=lambda x: len(x), reverse=True)
                json_groups = []
                groups_summary = ''
                for s in groups:
                    groups_summary += f' {{{",".join(s)}}} '
                    json_groups.append(list(s))
                summary.append(f'{tag} {len(v)} {groups_summary}')
                json_data[tag].append(
                    {'Groups': json_groups, 'Count': len(v), 'Zones': list(v)})
    output = {}
    output["Summary"] = summary
    output["Details"] = json_data
    with open(path / 'Clusters.json', 'w') as j:
        json.dump(output, j, indent=2)


if __name__ == '__main__':
    parser = ArgumentParser(
        description='Clusters the tests based on the model case as well as the unique implementations in each group from the responses')
    parser.add_argument('-path', metavar='DIRECTORY_PATH',
                        help='The path to the directory containing QueryResponses and Differences directories. (default: Results/)')
    args = parser.parse_args()
    if "path" in args:
        directory_path = pathlib.Path(args.path)
    else:
        directory_path = pathlib.Path("Results/")
    if not (directory_path / "Differences").exists() or not (directory_path / "QueryResponses").exists():
        sys.exit(
            f'The directory {directory_path} does not have QueryResponses and Differences folders.')
    cluster_tests(directory_path)
