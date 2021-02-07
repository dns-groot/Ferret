FROM ubuntu:bionic

LABEL maintainer="sivakesava@cs.ucla.edu"

# ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update 
# RUN apt-get install -y \
#   pdns-server \
#   dnsutils \
#   dos2unix \
#   rsyslog \
#   vim 

RUN apt install -y \
    libcurl4-openssl-dev \
    luajit \
    lua-yaml-dev \
    libyaml-cpp-dev \
    libtolua-dev \
    lua5.3 \
    autoconf \
    automake \
    ragel \
    bison \
    flex \
    g++ \
    git \
    libboost-all-dev \
    libtool \
    make \
    pkg-config \
    libssl-dev \
    lua-yaml-dev \
    libyaml-cpp-dev \
    libluajit-5.1-dev \
    libcurl4 \
    gawk \
    libsqlite3-dev \
    python3-venv \
    dos2unix \
    virtualenv

RUN git clone https://github.com/PowerDNS/pdns.git

ARG latest=false

RUN if [ "$latest" = "false" ] ; then cd pdns && git reset --hard a03aaad7554483ee6efe72a81eda00a9d1a94fe5 ; fi

RUN cd pdns && \
    autoreconf -vi && \
    ./configure --with-modules="bind" --disable-lua-records && \
    make && \
    make install

COPY Powerdns/bindbackend.conf /usr/local/etc/
COPY Powerdns/pdns.conf /usr/local/etc/
COPY db.campus.edu /usr/local/etc/

# Required
RUN dos2unix /usr/local/etc/bindbackend.conf

# Run eternal loop
CMD ["/bin/bash", "-c", "while :; do sleep 10; done"]