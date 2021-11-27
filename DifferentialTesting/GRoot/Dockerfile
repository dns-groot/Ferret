FROM dnsgt/groot:latest

RUN git pull

RUN git checkout differentialTesting

RUN cd build && \
    cmake .. && \
    cmake --build .

RUN mkdir build/bin/zonefile
COPY GRoot/metadata_gen.py /home/groot/groot/

# Run eternal loop
CMD ["/bin/bash", "-c", "while :; do sleep 10; done"]