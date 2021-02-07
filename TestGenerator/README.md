## Installation  

### Native Installation
0. [Install `dotnet-sdk-5.0` for your OS.](https://docs.microsoft.com/en-us/dotnet/core/install/windows?tabs=net50)
1. Build the project using<sup>[#](#note_1)</sup> (from `TestGenerator` directory):
    ```bash
    ~/TestGenerator$ dotnet build --configuration Release
    ```
<a name="note_1"><sup>#</sup></a> Alternatively, you could open the solution in Visual Studio in Windows and build using it.

### Using `docker`

_**Note:** The docker image may consume  ~&hairsp;2&hairsp;GB of disk space._

If you have trouble with native installation, then using docker is  recommend as they have negligible performance overhead.
(See [this report](http://domino.research.ibm.com/library/cyberdig.nsf/papers/0929052195DD819C85257D2300681E7B/$File/rc25482.pdf))

0. [Get `docker` for your OS](https://docs.docker.com/install).

1. Build the docker image locally (from `TestGenerator` directory): 
    ```bash
    ~/TestGenerator$ docker build -t ferrettestgen .
   ```
2. Run a container over the image using: `docker run -it --name=testgen  ferrettestgen`.<br>
   This would give you a `bash` shell within `TestGenerator` directory.

## Generation of Tests  

1. If a docker container will be used for the test generation, either
    - Copy the `Results` folder from the docker container after running the tool to the host system using `docker cp testgen:/home/ferret/Ferret/TestGenerator/Results .` from the host terminal.
    - Or first create a `Results` folder in the host system and [bind mount](https://docs.docker.com/storage/bind-mounts) it while running the container:
        ```bash
        docker run -v ~/TestGenerator/Results:/home/ferret/Ferret/TestGenerator/Results -it --name=testgen ferrettestgen
        ```
3. Run using:
     ```bash
    ~/TestGenerator$ dotnet run --configuration Release --project Samples
    ```
    <details>
    <summary><kbd>CLICK</kbd> to show all command-line options</summary>
    
    ```
        -o, --outputDir    (Default: Results/) The path to the folder to output the generated tests.

        -f, --function     (Default: QueryLookup) Generate tests for either 'QueryLookup' (1) or 'InvalidZones' (2).

        -l, --length       (Default: 4) The maximum number of records in a zone and the maximum length of a domain.

        --help             Display this help screen.

        --version          Display version information.
    ```
    - Pass the option using `dotnet run  --configuration Release --project Samples -- -l 3`.
    - The `QueryLookup` function generates tests which are a pair of zone and query.
    - The `InvalidZones` function generates invalid zone files by negating one validity constraint at a time while keeping the others true. For each negated constraint, the tool tries to generates 100 zone files. 

    </details>
   
4. _Est. Time:_ Ferret takes approximately 6 hours for `QueryLookup` with maximum length 4 to generate 12,673 tests.
