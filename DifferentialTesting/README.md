## Installation  

1. [Get `docker` for your OS](https://docs.docker.com/install).
2. Install [`python3`.](https://www.python.org/downloads/)
3. Install [`dnspython`.](https://pypi.org/project/dnspython/)
4. Install [`named-compilezone`.](https://command-not-found.com/named-compilezone)
    - In windows, download the latest `BIND` software [BIND9.x.zip-win 64-bit](https://www.isc.org/download/) and unzip it. The unzipped folder should have `named-compilezone.exe` executable. 
    - For other OSes too, if it can not be installed successfully, then download the [BIND9.x.tar.xz](https://www.isc.org/download/) and decompress it. 

## Running Tests

**Please note:**
- All commands mentioned in this file must be run from the `DifferentialTesting` folder and not from the root of the repository.
- Atleast _16&hairsp;GB_ RAM is recommended for testing all the eight implementations using Docker.


0. Copy the generated tests (`Results` folder) from the `Testgenerator` folder to the `DifferentialTesting` folder.
1. Generate Docker images for the implementations using:

    ```bash
    python3 Scripts/generate_docker_images.py 
    ```
    <details>
    <summary><kbd>CLICK</kbd> to show all command-line options</summary>

    ```
    usage: generate_docker_images.py [-h] [-l] [-b] [-n] [-k] [-p] [-c] [-y] [-m] [-t]

    optional arguments:
    -h, --help    show this help message and exit
    -l, --latest  Build the images using latest code. (default: False)
    -b            Disable Bind. (default: False)
    -n            Disable Nsd. (default: False)
    -k            Disable Knot. (default: False)
    -p            Disable PowerDns. (default: False)
    -c            Disable CoreDns. (default: False)
    -y            Disable Yadifa. (default: False)
    -m            Disable MaraDns. (default: False)
    -t            Disable TrustDns. (default: False)
    ```
    </details>

    - By default, the images are built using the implementations code as of around October 1<sup>st</sup>, 2020 (check [Readme](Implementations/README.md) for details). Pass the `-l` flag to use the latest code, but some images may not build if dependecies or other things are updated.
    - _**Note:** Each Docker image consumes  ~&hairsp;1-2&hairsp;GB of disk space._
    - _Est. Time:_ ~&thinsp;20 mins.
    - _Expected Output_: Docker images for the implementations.

2. Use either Zen generated tests or custom tests to test implementations<br>
    **Using Zen Tests**: Translate Zen generated tests into English labels using:
    -   installed `named-compilezone` 

        ```bash
        python3 Scripts/translate_tests.py  Results/
        ```
    -   the executable of `named-compilezone`

        ```bash
        python3 Scripts/translate_tests.py  Results/ -c <path to the named-compilezone executable>
        ```
    -   _Est. Time:_ ~&thinsp;15 mins.
    -   _Expected Output_: Creates three folders `TranslatedTests`, `FormattedTests`, and `QueryResponse` in the `Results` folder
        - `TranslatedTests` folder contains the zone files of the tests from `LookupTests` but with integer labels replaced by English labels.
        - `FormattedTests` folder has the zone files from `TranslatedTests`, but after passing through `named-compilezone` for proper formatting.
        - `QueryResponse` folder contains the query part of the tests from `LookupTests`. 

    **Using Custom Tests**:
    - Create a directory `CustomTests` (or `Results`) and two sub-directories `FormattedTests` and `QueryResponse` in it.
    - Place the test zone files (`TXT` files in `Bind` format and FQDN) in `FormattedTests` folder.
    - For each test zone file (_foo.txt_) in `FormattedTests`, create a same named `json` file (_foo.json_) in `QueryResponse` with queries.
    
        <details>
        <summary><kbd>CLICK</kbd> to reveal the query format</summary>
               
        ```json5
        {
            "Queries": [
                {
                    "Name": "campus.edu.",
                    "Type": "SOA"
                },
                {
                    "Name": "host1.campus.edu.",
                    "Type": "A"
                }
            ]          
        }
        ```
        
        </details>

3.  Test mulitple implementations using `python3 -m Scripts.test_implementations`
    ```
    usage: Scripts.test_implementations [-h] [-path DIRECTORY_PATH] [-id {1,2,3,4,5}] [-r START END] [-b] [-n] [-k] [-p] [-c] [-y] [-m] [-t]

    Compares implementations responses for the input tests.

    optional arguments:
    -h, --help            show this help message and exit
    -path DIRECTORY_PATH  The path to the directory containing FormattedZones and QueryResponses directories. (default: Results/)
    -id {1,2,3,4,5}       Unique id for all the containers (useful when running comparison in parallel). (default: 1)
    -r START END          The range of tests to compare. (default: All tests)
    -b                    Disable Bind. (default: False)
    -n                    Disable Nsd. (default: False)
    -k                    Disable Knot. (default: False)
    -p                    Disable PowerDns. (default: False)
    -c                    Disable CoreDns. (default: False)
    -y                    Disable Yadifa. (default: False)
    -m                    Disable MaraDns. (default: False)
    -t                    Disable TrustDns. (default: False)
    ```
    - Arguments `-r` and `-id` can be used to parallelize testing. 
        <details>

        <summary><kbd>CLICK</kbd> to reveal details</summary>

        - **Please note:** Parallelize with caution as each run can deal with eight containers. Do not parallelize if the RAM is less than _64&hairsp;GB_ when testing all eight implementations.
        - If there are `12,700` tests, then they can be split three-way as:
            ```
            python3 Scripts/test_implementations.py -id 1 -r 0    4000
            python3 Scripts/test_implementations.py -id 2 -r 4000 8000
            python3 Scripts/test_implementations.py -id 3 -r 8000 13000
            ```
        </details>
    - The default host ports used for testing are: `[8000, 8100, ... 8700]*id`, which can be changed by modifying the [`get_ports`](Scripts/test_implementations.py#L28) function in the python script before running it.
    - _Est Time:_ ~&thinsp;36 hours (&#x1F61E;) with no parallelization for the Zen generated `12,673 ` tests.
    -  _Expected Output_: Creates a folder `Differences` in the input directory to store responses for each query if they form more than one group.
