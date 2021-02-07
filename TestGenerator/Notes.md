## Notes

* Ran into errors using the mcr.microsoft.com/dotnet/sdk containers
    - `dotnet build` runs successfully without any errors.
    - `./TestGenerator//Samples/bin/Debug/netcoreapp3.1/Samples` throws the following exception:
        ```
        Unable to load shared library 'libz3' or one of its dependencies. In order to help diagnose loading problems, consider setting the LD_DEBUG environment variable: ...
        ```
        as mentioned here - https://github.com/ClosedXML/ClosedXML/issues/1056
    - The above issue points to [Unable to load shared library 'libz3' #4780](https://github.com/Z3Prover/z3/issues/4780) on z3 GitHub.
    - Following the suggestion mentioned in the above issue, installed `libz3` using
        ```
         apt-get install -y --allow-unauthenticated libz3-dev
        ```
    - Then the following error is thrown:
        ```
        System.EntryPointNotFoundException: Unable to find an entry point named 'Z3_mk_string_sort' in shared library 'libz3'.
        ```
