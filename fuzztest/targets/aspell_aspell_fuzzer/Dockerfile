FROM fuzztest/base

ARG B_SRC
ARG B_OUT

ENV SRC=$B_SRC
ENV OUT=$B_OUT

RUN apt-get update && apt-get install -y pkg-config zip

RUN git clone https://github.com/gnuaspell/aspell.git $SRC/aspell
RUN git clone --depth 1 -b master https://github.com/gnuaspell/aspell-fuzz.git $SRC/aspell-fuzz

COPY build.sh /

ENV FUZZ_TARGET=aspell_fuzzer