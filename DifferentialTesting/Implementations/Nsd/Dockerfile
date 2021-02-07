FROM ubuntu:bionic

LABEL maintainer="sivakesava@cs.ucla.edu"

RUN apt-get update 

RUN apt-get install -y \
    automake \
    bison \
    dnsutils \
    flex \
    gcc \
    git \
    libevent-dev \
    libssl-dev \
    make \
    openssl \
    vim 

RUN git clone https://github.com/NLnetLabs/nsd.git

ARG latest=false

RUN if [ "$latest" = "false" ] ; then cd nsd && git reset --hard 4043a5ab7be7abaec969011e48e4d0d60a0056a6 ; fi

RUN cd nsd && \
    aclocal && \
    autoconf && \
    autoheader && \
    ./configure && \
    make && \
    make install && \
    ldconfig

# Copy configuration files
COPY Nsd/nsd.conf /etc/nsd/
COPY db.campus.edu /etc/nsd/zones/

RUN nsd-control-setup

# Run eternal loop
CMD ["/bin/bash", "-c", "while :; do sleep 10; done"]