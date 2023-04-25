FROM fuzztest/base

RUN apt-get update && \
    apt-get install -y make autoconf automake libtool shtool pkg-config 

RUN git clone https://github.com/file/file.git
COPY ./build.sh ./magic_fuzzer.cc /

