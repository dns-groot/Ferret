FROM ubuntu:bionic

LABEL maintainer="sivakesava@cs.ucla.edu"

RUN apt-get update 

RUN apt-get install -y \
    libtool \
    autoconf \
    automake \
    make \
    pkg-config \
    liburcu-dev \
    libgnutls28-dev \
    libedit-dev \
    liblmdb-dev \
    git \
    vim \
    dnsutils \
    dos2unix \
    rsyslog 

RUN git clone https://gitlab.nic.cz/knot/knot-dns.git

ARG latest=false

RUN if [ "$latest" = "false" ] ; then cd knot-dns && git reset --hard 563fcdd886b5d5c52bceeb8fda3c4bda59ece73e ; fi

RUN cd knot-dns && \
    autoreconf -if && \
    ./configure && \
    make && \
    make install && \
    ldconfig

# Copy configuration files

COPY Knot/knot.conf /usr/local/etc/knot/
COPY db.campus.edu /usr/local/var/lib/knot/

# Convert CRLF to LF - Knot does not load a zone if it has CRLF by giving the following fatal error -- `unsupported CRLF newline, remove CR bytes.` 
RUN dos2unix /usr/local/var/lib/knot/db.campus.edu

# Run eternal loop
CMD ["/bin/bash", "-c", "while :; do sleep 10; done"]