ARG parent_image
FROM $parent_image

RUN git clone https://github.com/aflchurn/aflchurn.git /afl && \
    cd /afl && \
    AFL_NO_X86=1 make && \
    INITIAL_CXXFLAGS=$CXXFLAGS && \
    INITIAL_CFLAGS=$CFLAGS && \
    unset CFLAGS CXXFLAGS && \
    cd llvm_mode && \
    make && \
    CXXFLAGS=$INITIAL_CXXFLAGS && \
    CFLAGS=$INITIAL_CFLAGS


RUN wget https://raw.githubusercontent.com/llvm/llvm-project/5feb80e748924606531ba28c97fe65145c65372e/compiler-rt/lib/fuzzer/afl/afl_driver.cpp -O /afl/afl_driver.cpp && \
    clang++ -stdlib=libc++ -std=c++11 -O2 -c /afl/afl_driver.cpp && \
    ar r /libAFL.a *.o

WORKDIR /
COPY ./fuzz.py fuzz.py
RUN python3 fuzz.py build
CMD ["python3", "fuzz.py", "run"]