## Serving a Zone File with an Implementation

1. Build the image of the required implementation using:
    ```bash
    docker build -t <image_name>:oct -f <directory_name>/Dockerfile .
    ```
    where, the `image_name` would be `bind` and `directory_name` would be `Bind` to build a Bind image.<br>
    **Please note:**
    - Use the `image_name` same as the `directory_name` but in lowercase.
    - _Each Docker image consumes  ~&hairsp;1-2&hairsp;GB of disk space._
    - Technitium implementation does not have the corresponding Oct, 2020 version, and only the latest commit is used for any build.

    By default, the image built uses the code around October 1<sup>st</sup>, 2020. The links to the exact `commit` used are as follows:
    
    [Bind](https://gitlab.isc.org/isc-projects/bind9/-/tree/dbcf683c1a57f49876e329fca183cb39d20ca3a4) &nbsp;&middot;&nbsp;
    [Nsd](https://github.com/NLnetLabs/nsd/tree/4043a5ab7be7abaec969011e48e4d0d60a0056a6) &nbsp;&middot;&nbsp;
    [Knot](https://gitlab.nic.cz/knot/knot-dns/-/tree/563fcdd886b5d5c52bceeb8fda3c4bda59ece73e) &nbsp;&middot;&nbsp;
    [PowerDns](https://github.com/PowerDNS/pdns/tree/a03aaad7554483ee6efe72a81eda00a9d1a94fe5) &nbsp;&middot;&nbsp;
    [CoreDns](https://github.com/coredns/coredns/tree/6edc8fe7f6c2f57844c8ee7f7f5deef71085ebe8) &nbsp;&middot;&nbsp;
    [Yadifa](https://github.com/yadifa/yadifa/tree/dc5bed2fb8ec204af9b65eeb91934c2c85098cbb) &nbsp;&middot;&nbsp;
    [MaraDns](https://github.com/samboy/MaraDNS/tree/3ec477f227b2bf6947be8fbe8fd0ab73130227d0) &nbsp;&middot;&nbsp;
    [TrustDns](https://github.com/bluejekyll/trust-dns/tree/7d9b186121fb5cb331cf2ec6baa47846b83de8fc) 

    To build the image using the latest main branch, pass `true` to the build argument `latest`<sup>[:warning:](#note_1)</sup>:
    ```bash
    docker build -t <image_name>:latest -f <directory_name>/Dockerfile --build-arg latest=true .
    ```

2. Serve a zone file with an implementation using `python3 main.py`.

    <pre>
    usage: main.py [-h] [-z ZONE_FILE_PATH] [-c CONTAINER_NAME]  [-p UNUSED_PORT] [-i {bind, nsd, knot, powerdns, coredns, yadifa, maradns, trustdns}] [-l] [-e]

    Gets an implementation to serve the input or default zone file.
    Specify an image name and a port to start a new container (also container name if you want to assign a name)
      or only the name of an existing container to reuse it.

    optional arguments:
    -h, --help                              Show this help message and exit.
    -z ZONE_FILE_PATH                       The path to the zone file to be served. (default: <a href="db.campus.edu" title="default zone file">db.campus.edu</a>)
    -i {bind, nsd, knot, powerdns,
        coredns, yadifa, maradns, trustdns} The docker image name of the implementation to start a container.
    -p UNUSED_PORT                          An unused host port to map to port 53 of the container.
    -c CONTAINER_NAME                       A name for the container. (default: Random Docker generated name)
    -l, --latest                            Serve using the latest image tag.
    -e                    Whether the implementation is Technitium. (default: False)
    </pre>

3. Query from the host machine using:
    ```bash
    dig @127.0.0.1 -p <PORT> +norecurse <QUERY>
    ```
    where `PORT` is the port number used in the previous step to start a container.

<a name="note_1"><sup>:warning:</sup></a> The image may not build with the latest code if dependecies or other things are updated after Oct 1<sup>st</sup>, 2020.
