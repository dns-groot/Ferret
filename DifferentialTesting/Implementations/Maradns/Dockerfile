FROM centos:8

LABEL maintainer="sivakesava@cs.ucla.edu"

RUN cd /etc/yum.repos.d/ && sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-* && sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-*

RUN yum -y update
RUN yum -y install gcc \
  git \
  make \
  python3 \
  vim

RUN git clone  https://github.com/Samboy/MaraDNS/

ARG latest=false

RUN if [ "$latest" = "false" ] ; then cd MaraDNS && git reset --hard 3ec477f227b2bf6947be8fbe8fd0ab73130227d0 ; fi


RUN cd MaraDNS && \
  ./configure && \
  make && \
  make install

COPY db.campus.edu /etc/maradns/
COPY Maradns/mararc.sh /etc/
COPY Maradns/tocsv2.py .

RUN chmod +x /etc/mararc.sh
RUN python3 tocsv2.py /etc/maradns/db.campus.edu
# RUN python2 MaraDNS/tools/bind2csv2.py -c /etc/maradns/db.campus.edu

# Run eternal loop
CMD ["/bin/bash", "-c", "while :; do sleep 10; done"]