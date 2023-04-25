FROM fuzztest/base

ARG B_SRC
ARG B_OUT

ENV SRC=$B_SRC
ENV OUT=$B_OUT

RUN apt-get update && apt-get install -y make autoconf automake libtool zlib1g-dev liblzma-dev zip

RUN git clone https://github.com/OISF/libhtp.git libhtp

COPY ./build.sh /

ENV FUZZ_TARGET=fuzz_htp

