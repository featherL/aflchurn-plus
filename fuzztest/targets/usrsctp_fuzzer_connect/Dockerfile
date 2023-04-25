FROM fuzztest/base

ARG B_SRC
ARG B_OUT

ENV SRC=$B_SRC
ENV OUT=$B_OUT

RUN apt-get update && apt-get install -y make cmake pkg-config zip
RUN git clone --branch oss-fuzz https://github.com/weinrank/usrsctp usrsctp

COPY build.sh /

ENV FUZZ_TARGET=fuzzer_connect
