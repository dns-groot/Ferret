FROM ubuntu:bionic

LABEL maintainer="sivakesava@cs.ucla.edu"

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install sudo

RUN apt-get install -y \
    apt-transport-https \
    software-properties-common \
    wget \
    vim

RUN apt-add-repository ppa:git-core/ppa && \
    apt-get update && \
    apt-get install -y git

ENV HOME /home/ferret/

RUN adduser --disabled-password --home $HOME --shell /bin/bash --gecos '' ferret && \
    echo 'ferret ALL=(ALL) NOPASSWD:ALL' >>/etc/sudoers && \
    su ferret

USER ferret

WORKDIR $HOME

RUN wget https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb

RUN sudo dpkg -i packages-microsoft-prod.deb

RUN sudo apt-get update 

RUN sudo apt-get install -y dotnet-sdk-5.0

RUN rm packages-microsoft-prod.deb

# https://stackoverflow.com/questions/600079/how-do-i-clone-a-subdirectory-only-of-a-git-repository/52269934#52269934

RUN git clone --depth 1 --filter=blob:none --sparse https://github.com/dns-groot/Ferret.git 
RUN cd Ferret && \
    git sparse-checkout init --cone && \
    git sparse-checkout set TestGenerator

WORKDIR $HOME/Ferret/TestGenerator/

# RUN cd TestGenerator/Tests && sudo dotnet add package coverlet.msbuild

RUN dotnet build --configuration Release 

# RUN sudo chown -R ferret:ferret /tmp/NuGetScratch/
# Run eternal loop
# CMD ["/bin/bash", "-c", "while :; do sleep 10; done"]