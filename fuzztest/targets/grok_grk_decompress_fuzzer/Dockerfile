FROM fuzztest/base

ARG B_SRC
ARG B_OUT

ENV SRC=$B_SRC
ENV OUT=$B_OUT

RUN apt-get update && apt-get install -y cmake zip

RUN git clone https://github.com/GrokImageCompression/grok.git $SRC/grok
RUN git clone https://github.com/GrokImageCompression/grok-test-data.git $SRC/grok/data

COPY build.sh /

ENV FUZZ_TARGET=grk_decompress_fuzzer


