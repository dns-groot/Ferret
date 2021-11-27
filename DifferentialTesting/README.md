## Installation  

1. [Get `docker` for your OS](https://docs.docker.com/install).
2. Install [`python3`.](https://www.python.org/downloads/)
3. Install [`dnspython`.](https://pypi.org/project/dnspython/)
4. Install [`named-compilezone`.](https://command-not-found.com/named-compilezone)
    - In windows, download the latest `BIND` software [BIND9.x.zip-win 64-bit](https://www.isc.org/download/) and unzip it. The unzipped directory should have `named-compilezone.exe` executable. 
    - For other OSes, too, if it can not be installed successfully, download the [BIND9.x.tar.xz](https://www.isc.org/download/) and decompress it. 

## Running Tests

**Please note:**
- All commands mentioned in this file must be run from the `DifferentialTesting` directory and not from the repository root.
- At least _16&hairsp;GB_ of RAM is recommended for testing all the eight implementations using Docker.

### 1. Docker Image Generator
Generate Docker images for the implementations using:

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
- Without the `-l` flag, the built images will have the `:oct` as the image tag; for example, the built Bind image would be `bind:oct`. If the `-l` flag was used to build the images, the tag would be `latest`.
- _**Note:** Each Docker image consumes  ~&hairsp;1-2&hairsp;GB of disk space._
- _Est. Time:_ ~&thinsp;20 mins.
- _Expected Output_: Docker images for the implementations.

### 2. Tests Organization
Use either Zen generated tests or custom tests to test implementations.<br>

#### Using Zen Tests

##### A. Using Pre-generated Tests from the [Ferret Dataset](https://github.com/dns-groot/FerretDataset)

- Clone the dataset repository as `Results` directory using
    ```bash
    git clone https://github.com/dns-groot/FerretDataset.git Results
    ```
- Proceed to [Step 3](#3-testing-implementations) to run the tests

##### B. Using Tests from Test Generation Module
- Move the generated tests (`Results` directory) from the `TestGenerator` directory to the `DifferentialTesting` directory 
- Translate Zen tests with integer labels to English labels
    - Translate valid zone file tests using either

        &nbsp; &rArr; &nbsp;installed <kbd>named-compilezone</kbd>
        ```bash
        python3 Scripts/translate_tests.py Results/ValidZoneFileTests
        ```
        &nbsp; &rArr; &nbsp;the executable of <kbd>named-compilezone</kbd>
        ```bash
        python3 Scripts/translate_tests.py Results/ValidZoneFileTests -c <path to the named-compilezone executable>
        ```
    - Translate invalid zone files using
        ```bash
        python3 Scripts/zone_translator.py Results/InValidZoneFileTests
        ```
-   _Est. Time:_ ~&thinsp;15 mins.
-   _Expected Output_:
    - For valid zone file tests, the `translate_tests.py` script creates three directories in the `ValidZoneFileTests` directory.<br>
        &rdsh; `ZoneFiles` directory with all the zone files translated to English labels and formatted with `named-compilezone`.<br>
        &rdsh; `Queries` directory contains the queries corresponding to each zone file.<br>
        &rdsh; `TestsTotalInfo` directory contains all the information regarding a test in a single JSON file, for easy debugging.
    - For invalid zone files, the `zone_translator.py` script creates a `ZoneFiles` directory in each of the subdirectories (`FalseCond_1`, `FalseCond_2`, ...).

#### Using Custom Tests
- Create a directory `CustomTests` (or `Results`) and a sub-directory `ZoneFiles` in that directory.
- Place the test zone files (`TXT` files in `Bind` format and FQDN) in `ZoneFiles` directory.
- If you don't have any specific queries to test on these zone files, then assume them as invalid zone files and proceed to Step 3 to follow the steps of testing using invalid zone files.
- If you have queries, then for each test zone file (_foo.txt_) in `ZoneFiles`, create a same named `json` file (_foo.json_) in `Queries` directory (sibling directory of `ZoneFiles` ) with queries.

    <details>
    <summary><kbd>CLICK</kbd> to reveal the queries format in <i>foo.json</i></summary>

    ```json5

    [
        {
            "Query": {
                "Name": "campus.edu.",
                "Type": "SOA"
            }
        },
        {
            "Query": {
                "Name": "host1.campus.edu.",
                "Type": "A"
            }
        }
    ]
    ```
    
    </details>

### 3. Testing Implementations

Test an implementation by comparing its response with the expected response from the [Ferret Dataset](https://github.com/dns-groot/FerretDataset) or compare mulitple implementations' responses in a differential testing set up.

#### Testing with Valid Zone Files

Run the testing script from the `DifferentialTesting` directory as a Python module using:
```
usage: python3 -m Scripts.test_with_valid_zone_files [-h] [-path DIRECTORY_PATH]
                                                     [-id {1,2,3,4,5}] [-r START END] [-b]
                                                     [-n] [-k] [-p] [-c] [-y] [-m] [-t] [-l]

Runs tests with valid zone files on different implementations.
Either compares responses from mulitple implementations with each other or uses a
expected response to flag differences (only when one implementation is passed for testing).

optional arguments:
  -h, --help            show this help message and exit
  -path DIRECTORY_PATH  The path to the directory containing ZoneFiles and either Queries or
                        ExpectedResponses directories.
                        (default: Results/ValidZoneFileTests/)
  -id {1,2,3,4,5}       Unique id for all the containers (useful when running comparison in
                        parallel). (default: 1)
  -r START END          The range of tests to compare. (default: All tests)
  -b                    Disable Bind. (default: False)
  -n                    Disable Nsd. (default: False)
  -k                    Disable Knot. (default: False)
  -p                    Disable PowerDns. (default: False)
  -c                    Disable CoreDns. (default: False)
  -y                    Disable Yadifa. (default: False)
  -m                    Disable MaraDns. (default: False)
  -t                    Disable TrustDns. (default: False)
  -l, --latest          Test using latest image tag. (default: False)
```
- Arguments `-r` and `-id` can be used to parallelize testing. 
    <details>

    <summary><kbd>CLICK</kbd> to reveal details</summary>

    - **Please note:** Parallelize with caution as each run can deal with eight containers. Do not parallelize if the RAM is less than _64&hairsp;GB_ when testing all eight implementations.
    - If there are `12,700` tests, then they can be split three-way as:
        ```
       python3 -m Scripts.test_with_valid_zone_files -id 1 -r 0    4000
        python3 -m Scripts.test_with_valid_zone_files -id 2 -r 4000 8000
        python3 -m Scripts.test_with_valid_zone_files -id 3 -r 8000 13000
        ```
    </details>
- The default host ports used for testing are: `[8000, 8100, ... 8700]*id`, which can be changed by modifying the [`get_ports`](Scripts/test_with_valid_zone_files.py#L66) function in the python script before running it.
- _Est Time:_ ~&thinsp;36 hours (&#x1F61E;) with no parallelization for the Zen generated <kbd>12,673</kbd> tests.
- _Expected Output_: Creates a directory `Differences` in the input directory to store responses for each query if there are different responses from the implementations.

#### Testing with invalid zone files

- Only four implementations &mdash; Bind, Nsd, Knot, PowerDNS &mdash; are supported as these have a
mature zone-file preprocessor available.
- Run the script `preprocessor_checks.py` to first check all the zone fils with each implementation's preprocessor.
    ```bash
    python3 Scripts/preprocessor_checks.py
    ```
    <details>
    <summary><kbd>CLICK</kbd> to show all command-line options</summary>

    ```
    usage: preprocessor_checks.py [-h] [-path DIRECTORY_PATH] [-id {1,2,3,4,5}]
                                  [-b] [-n] [-k] [-p] [-l]

    optional arguments:
    -h, --help            show this help message and exit
    -path DIRECTORY_PATH  The path to the directory containing ZoneFiles; looks for ZoneFiles
                          directory recursively. (default: Results/InValidZoneFileTests/)
    -id {1,2,3,4,5}       Unique id for all the containers (default: 1)
    -b                    Disable Bind. (default: False)
    -n                    Disable Nsd. (default: False)
    -k                    Disable Knot. (default: False)
    -p                    Disable PowerDns. (default: False)
    -l, --latest          Test using latest image tag. (default: False)
    ```
    </details>

    Creates a directory `PreprocessorOutputs` and outputs whether each preprocessor accepts or rejects the zone files along with the explanation for rejection.

- Run the testing script from the `DifferentialTesting` directory as a Python module using:
    ```bash
    python3 -m Scripts.test_with_invalid_zone_files
    ```
    <details>
    <summary><kbd>CLICK</kbd> to show all command-line options</summary>

    ```
    usage: python3 -m Scripts.test_with_invalid_zone_files [-h] [-path DIRECTORY_PATH]
                                                           [-id {1,2,3,4,5}] [-b] [-n] [-k] [-p] [-l]

    Runs tests with invalid zone files on different implementations.
    Generates queries using GRoot equivalence classes.
    Either compares responses from mulitple implementations with each other or uses a expected
    response to flag differences (only when one implementation is passed for testing).

    optional arguments:
    -h, --help            show this help message and exit
    -path DIRECTORY_PATH  The path to the directory containing ZoneFiles and PreprocessorOutputs
                          directories; looks for those two directories recursively
                          (default: Results/InValidZoneFileTests/)
    -id {1,2,3,4,5}       Unique id for all the containers (default: 1)
    -b                    Disable Bind. (default: False)
    -n                    Disable Nsd. (default: False)
    -k                    Disable Knot. (default: False)
    -p                    Disable PowerDns. (default: False)
    -l, --latest          Test using latest image tag. (default: False)
    ```
    </details>

- _Est Time:_ ~&thinsp;3.5 hours for the Zen generated <kbd>900</kbd> invalid zones for a maximum length of $4$.
- _Expected Output_: Creates two directories <br>
    &rdsh; `EquivalenceClassNames` directory to store the query equivalence class names generated from GRoot for each of the test zone files in `ZoneFiles` directory.<br>
    &rdsh; `Differences` directory to store responses for each query if there are different responses from the implementations.

### 4. Triaging
Since there are often many more test failures than there
are bugs (e.g., a bug can cause multiple tests to fail), we triage
the tests in `Differences` directory by creating a _hybrid fingerprint_ for each test, which combines information from the test's path in the Zen model (if available) with the results of differential testing, and then groups tests by fingerprint for user inspection.

Fingerprint and group the tests using `python3 Scripts/triaging.py`
<details>
<summary><kbd>CLICK</kbd> to show all command-line options</summary>

```
usage: triaging.py [-h] [-path DIRECTORY_PATH]

Fingerprint and group the tests that resulted in differences based on the model case (for valid zone
files) as well as the unique implementations in each group from the responses.
For invalid zone files, they are already separated into different directories based on the condition
violated. Therefore, only the unique implementations in each group is used.

optional arguments:
  -h, --help            show this help message and exit
  -path DIRECTORY_PATH  The path to the directory containing Differences directory.
                        Searches recursively (default: Results/)
```
</details>

- _Est Time:_ ~&thinsp;2 mins.
- _Expected Output_: Creates a `Fingerprints.json` file in each of the directories with the `Differences` directory. `Fingerprints.json` has a <kbd>Summary</kbd> section which lists for each group how many tests are in that group and a <kbd>Details</kbd> section which lists the tests for each group.