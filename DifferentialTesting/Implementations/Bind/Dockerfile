FROM ubuntu:bionic

LABEL maintainer="sivakesava@cs.ucla.edu"

RUN apt-get update 

RUN apt-get install -y \
    autoconf \
    automake \
    dnsutils \
    gcc \
    git \
    libcap-dev \
    libnghttp2-dev \
    libtool \
    libtool-bin \
    libuv1-dev \
    libssl-dev \
    make \
    openssl \
    pkgconf \
    vim 

RUN git clone https://gitlab.isc.org/isc-projects/bind9.git

ARG latest=false

RUN if [ "$latest" = "false" ] ; then cd bind9 && git reset --hard dbcf683c1a57f49876e329fca183cb39d20ca3a4 ; fi

RUN cd bind9 && \
    autoreconf -fi && \
    ./configure && \
    make && \
    make install && \
    ldconfig -v

RUN cd /usr/local/etc && \
    rndc-confgen -a

# Copy configuration files
COPY Bind/named.conf /usr/local/etc/
COPY db.campus.edu /usr/local/etc/

# Run eternal loop
CMD ["/bin/bash", "-c", "while :; do sleep 10; done"]