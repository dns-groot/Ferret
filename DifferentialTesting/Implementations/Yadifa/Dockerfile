FROM ubuntu:bionic

LABEL maintainer="sivakesava@cs.ucla.edu"

RUN apt-get update 

RUN apt-get install -y \
    automake \
    autotools-dev \
    autoconf \
    build-essential \
    libssl-dev \
    git \
    make \
    vim

RUN ln -sf /usr/bin/aclocal /usr/bin/aclocal-1.13
RUN ln -sf /usr/bin/automake /usr/bin/automake-1.13

RUN git clone https://github.com/yadifa/yadifa.git

ARG latest=false

RUN if [ "$latest" = "false" ] ; then cd yadifa && git reset --hard dc5bed2fb8ec204af9b65eeb91934c2c85098cbb ; fi

RUN cd yadifa && \
  ./configure --enable-full-ascii7 && \
  make && \
  make install

COPY Yadifa/yadifad.conf /usr/local/etc/
COPY db.campus.edu /usr/local/var/zones/masters/

# Run eternal loop
CMD ["/bin/bash", "-c", "while :; do sleep 10; done"]