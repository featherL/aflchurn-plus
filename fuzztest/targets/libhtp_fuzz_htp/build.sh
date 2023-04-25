cd libhtp
git checkout 75cbbbd405695e97567931655fd5a441f86e5836
sh autogen.sh
./configure
make

$CC $CFLAGS -I. -c test/fuzz/fuzz_htp.c -o fuzz_htp.o
$CC $CFLAGS -I. -c test/test.c -o test.o
$CXX $CXXFLAGS fuzz_htp.o test.o -o /out/target ./htp/.libs/libhtp.a $LIB_FUZZING_ENGINE -lz -llzma -lc++

# builds corpus
zip -j /out/seed_corpus.zip test/files/*.t