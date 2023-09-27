FROM ubuntu:lunar

LABEL maintainer="sivakakarla@microsoft.com"

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update 

RUN  apt-get install -y \
    curl \
    dnsutils \
    git \
    software-properties-common \
    dotnet-sdk-7.0

RUN git clone --depth 1 https://github.com/TechnitiumSoftware/TechnitiumLibrary.git TechnitiumLibrary

RUN  git clone --depth 1 https://github.com/TechnitiumSoftware/DnsServer.git DnsServer

RUN dotnet build TechnitiumLibrary/TechnitiumLibrary.ByteTree/TechnitiumLibrary.ByteTree.csproj -c Release 

RUN dotnet build TechnitiumLibrary/TechnitiumLibrary.Net/TechnitiumLibrary.Net.csproj -c Release

RUN dotnet publish DnsServer/DnsServerApp/DnsServerApp.csproj -c Release

CMD ["/bin/bash" "-c" "while :; do sleep 10; done"]