FROM fuzztest/base

ARG B_SRC
ARG B_OUT

ENV SRC=$B_SRC
ENV OUT=$B_OUT

RUN apt-get update && apt-get install -y make zip
# Clone source
RUN git clone https://github.com/facebook/zstd

COPY build.sh /

ENV FUZZ_TARGET=stream_decompress