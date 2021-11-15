FROM ubuntu:bionic

LABEL maintainer="sivakesava@cs.ucla.edu"

RUN apt-get update 
RUN apt-get install -y \
    curl \
    openssl \
    libssl-dev \
    pkg-config \
    git \
    vim 

RUN  curl https://sh.rustup.rs -sSf | sh -s -- -y

RUN git clone https://github.com/bluejekyll/trust-dns.git

ARG latest=false

RUN if [ "$latest" = "false" ] ; then cd trust-dns && git reset --hard 7d9b186121fb5cb331cf2ec6baa47846b83de8fc ; fi

RUN cd trust-dns && \
    /root/.cargo/bin/cargo build --release -p trust-dns

COPY db.campus.edu trust-dns/tests/test-data/named_test_configs/
COPY Trustdns/config.toml trust-dns/tests/test-data/named_test_configs/

# Run eternal loop
CMD ["/bin/bash", "-c", "while :; do sleep 10; done"]