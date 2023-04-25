FROM ubuntu:focal

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Shanghai
RUN sed -i 's@//.*archive.ubuntu.com@//mirrors.ustc.edu.cn@g' /etc/apt/sources.list && \
    sed -i 's/security.ubuntu.com/mirrors.ustc.edu.cn/g' /etc/apt/sources.list && \
    apt-get clean && \
    apt-get update && \
    apt-get install -y build-essential python git software-properties-common wget lsb-release gnupg && \
    mkdir /out /data

COPY ./llvm.sh /llvm.sh
RUN chmod +x /llvm.sh && /llvm.sh 11 all

ENV PATH=/usr/lib/llvm-11/bin/:$PATH


