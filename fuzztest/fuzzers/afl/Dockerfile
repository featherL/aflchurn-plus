ARG parent_image
FROM $parent_image

RUN git clone https://github.com/google/AFL.git /afl && \
    cd /afl && \
    git checkout 82b5e359463238d790cadbe2dd494d6a4928bff3 && \
    AFL_NO_X86=1 make

RUN wget https://raw.githubusercontent.com/llvm/llvm-project/5feb80e748924606531ba28c97fe65145c65372e/compiler-rt/lib/fuzzer/afl/afl_driver.cpp -O /afl/afl_driver.cpp && \
    clang -Wno-pointer-sign -c /afl/llvm_mode/afl-llvm-rt.o.c -I/afl && \
    clang++ -stdlib=libc++ -std=c++11 -O2 -c /afl/afl_driver.cpp && \
    ar r /libAFL.a *.o

WORKDIR /
COPY ./fuzz.py fuzz.py
RUN python3 fuzz.py build
CMD ["python3", "fuzz.py", "run"]