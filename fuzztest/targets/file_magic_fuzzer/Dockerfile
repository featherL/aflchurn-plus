FROM fuzztest/base

ARG B_SRC
ARG B_OUT

ENV SRC=$B_SRC
ENV OUT=$B_OUT

RUN apt-get update && \
    apt-get install -y make autoconf automake libtool shtool pkg-config 

RUN git clone https://github.com/file/file.git
COPY ./build.sh ./magic_fuzzer.cc /

ENV FUZZ_TARGET=magic_fuzzer
