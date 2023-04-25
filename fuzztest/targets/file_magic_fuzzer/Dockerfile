# Copyright 2016 Google Inc.
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

FROM fuzztest/base

ARG B_SRC
ARG B_OUT

ENV SRC=$B_SRC
ENV OUT=$B_OUT

RUN apt-get update && \
    apt-get install -y make autoconf automake libtool shtool pkg-config 

RUN git clone https://github.com/file/file.git
COPY ./build.sh ./magic_fuzzer.cc /

ENV FUZZ_TARGET=magic_fuzzer
