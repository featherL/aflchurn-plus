FROM fuzztest/base

RUN apt-get update && apt-get install -y pkg-config zip

ENV SRC=/
ENV OUT=/out

RUN git clone https://github.com/gnuaspell/aspell.git $SRC/aspell
RUN git clone --depth 1 -b master https://github.com/gnuaspell/aspell-fuzz.git $SRC/aspell-fuzz

COPY build.sh /
