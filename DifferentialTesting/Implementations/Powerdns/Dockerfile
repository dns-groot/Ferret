FROM ubuntu:bionic

LABEL maintainer="sivakesava@cs.ucla.edu"

RUN apt-get update 

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
    sed -i 's/docutils!=0.15/docutils!=0.15,<0.18/g' docs/requirements.txt pdns/dnsdistdist/docs/requirements.txt pdns/recursordist/docs/requirements.txt && \
    autoreconf -vi && \
    ./configure --with-modules="bind" --disable-lua-records && \
    make && \
    make install

# ./configure --with-modules="bind gsqlite3" --disable-lua-records    
# cd /usr/local/etc && pdnsutil create-bind-db testsec
COPY Powerdns/bindbackend.conf /usr/local/etc/
COPY Powerdns/pdns.conf /usr/local/etc/
COPY db.campus.edu /usr/local/etc/

# Required
RUN dos2unix /usr/local/etc/bindbackend.conf

# Run eternal loop
CMD ["/bin/bash", "-c", "while :; do sleep 10; done"]
