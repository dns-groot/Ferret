## Installation  

### Native Installation
0. [Install `dotnet-sdk-5.0` for your OS.](https://docs.microsoft.com/en-us/dotnet/core/install/windows?tabs=net50)
1. Build the project using<sup>[#](#note_1)</sup> (from `TestGenerator` directory):
    ```console
    ~/TestGenerator$ dotnet build --configuration Release
    ```
<a name="note_1"><sup>#</sup></a> Alternatively, you could open the solution in Visual Studio in Windows and build using it.

### Using `docker`

_**Note:** The docker image may consume  ~&hairsp;2&hairsp;GB of disk space._

If you have trouble with native installation, then using docker is  recommend as they have negligible performance overhead.
(See [this report](http://domino.research.ibm.com/library/cyberdig.nsf/papers/0929052195DD819C85257D2300681E7B/$File/rc25482.pdf))

0. [Get `docker` for your OS](https://docs.docker.com/install).

1. Build the docker image locally (from `TestGenerator` directory): 
    ```console
    ~/TestGenerator$ docker build -t ferrettestgen .
   ```
2. Run a container over the image using: `docker run -it --name=testgen  ferrettestgen`.<br>
   This would give you a `bash` shell within the container's `TestGenerator` directory.

## Generation of Tests  

1. If a docker container will be used for the test generation, either
    - Copy the `Results` folder from the docker container to the host system after running the tool using the following command from the **host** terminal.
        ```console
        ~/TestGenerator$ docker cp testgen:/home/ferret/Ferret/TestGenerator/Results .
        ```
    - Or first create a `Results` folder in the host system and [bind mount](https://docs.docker.com/storage/bind-mounts) it while running the container:
        ```bash
        ~/TestGenerator$ docker run -v ${PWD}/Results:/home/ferret/Ferret/TestGenerator/Results -it --name=testgen ferrettestgen
        ```
        This would give you a `bash` shell within the container's `TestGenerator` directory.
3. Run using:
     ```console
    ~/TestGenerator$ dotnet run --configuration Release --project Samples
    ```
    <details>
    <summary><kbd>CLICK</kbd> to show all command-line options</summary>
    
    ```
        -o, --outputDir    (Default: Results/) The path to the folder to output the generated tests.

        -f, --function     (Default: RRLookup) Generate tests for either 'RRLookup' (1) or generate invalid zone files 'InvalidZoneFiles' (2).

        -l, --length       (Default: 4) The maximum number of records in a zone and the maximum length of a domain.

        --help             Display this help screen.

        --version          Display version information.
    ```
    - Pass the option using `dotnet run  --configuration Release --project Samples -- -l 3`.
    - The `RRLookup` function generates tests which are a pair of zone and query.
    - The `InvalidZoneFiles` function generates invalid zone files by negating one validity constraint at a time while keeping the others true. For each negated constraint, the tool tries to generates 100 zone files. 

    </details>
   
4. _Est. Time:_ 
    - Ferret takes approximately 6 hours for `RRLookup` with a maximum length 4 to generate 12,673 tests. Each test consists of a well-formed zone file and a query that together causes execution to explore a particular RFC behavior.
    - Ferret takes approximately 20 minutes for `InvalidZoneFiles` generation to generate 900 ill-formed zone files, 100 violating each of the validity conditions.

