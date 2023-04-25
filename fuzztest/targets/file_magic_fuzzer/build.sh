cd /file

git checkout 8305d1cc5ec466b2d50d1b6000e7b3c8c4b08853
autoreconf -i
./configure --enable-static --disable-shared --disable-libseccomp
make V=1 all

$CXX $CXXFLAGS -std=c++11 -Isrc/ \
     /magic_fuzzer.cc -o /out/target \
     -lFuzzingEngine ./src/.libs/libmagic.a -lc++

cp ./magic/magic.mgc /out/
