FROM fuzztest/base

RUN apt-get update && apt-get install -y make autoconf automake libtool zlib1g-dev liblzma-dev zip

RUN git clone https://github.com/OISF/libhtp.git libhtp

COPY ./build.sh /

