#!/bin/bash -eu
# Copyright 2020 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
################################################################################

cd /grok && git checkout c007abeb226caef9c23bd786a36614b94703ff87
mkdir build
cd build
cmake ..
make clean -s
make -j$(nproc) -s
cd ..

./tests/fuzzers/build_google_oss_fuzzers.sh
./tests/fuzzers/build_seed_corpus.sh


