#!/bin/python3

# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# modify from https://github.com/google/fuzzbench


import subprocess
import os
import shutil
import zipfile
import hashlib
import signal
import configparser


INPUT_DIR = '/data/input'
OUTPUT_DIR = '/data/output'
CORPUS_ELEMENT_BYTES_LIMIT = 1 * 1024 * 1024

SANITIZER_FLAGS = [
    '-fsanitize=address',
    # Matches UBSan features enabled in OSS-Fuzz.
    # See https://github.com/google/oss-fuzz/blob/master/infra/base-images/base-builder/Dockerfile#L94
    '-fsanitize=array-bounds,bool,builtin,enum,float-divide-by-zero,function,'
    'integer-divide-by-zero,null,object-size,return,returns-nonnull-attribute,'
    'shift,signed-integer-overflow,unreachable,vla-bound,vptr',
]

BUGS_OPTIMIZATION_LEVEL = '-O1'


LIBCPLUSPLUS_FLAG = '-stdlib=libc++'

def append_flags(env_var, additional_flags, env=None):
    """Append |additional_flags| to those already set in the value of |env_var|
    and assign env_var to the result."""
    if env is None:
        env = os.environ

    env_var_value = env.get(env_var)
    flags = env_var_value.split(' ') if env_var_value else []
    flags.extend(additional_flags)
    env[env_var] = ' '.join(flags)


def set_compilation_flags(env=None):
    """Set compilation flags."""
    if env is None:
        env = os.environ

    env['CFLAGS'] = ''
    env['CXXFLAGS'] = ''

    append_flags('CFLAGS',
                    SANITIZER_FLAGS + [BUGS_OPTIMIZATION_LEVEL],
                    env=env)
    append_flags('CXXFLAGS',
                    SANITIZER_FLAGS +
                    [LIBCPLUSPLUS_FLAG, BUGS_OPTIMIZATION_LEVEL],
                    env=env)
    

def initialize_env(env=None):
    """Set initial flags before fuzzer.build() is called."""
    set_compilation_flags(env)

    for env_var in ['CFLAGS', 'CXXFLAGS']:
        print('[+] {env_var} = {env_value}'.format(env_var=env_var,
                                               env_value=os.getenv(env_var)))




def prepare_build_environment():
    cflags = [
        '-fsanitize-coverage=trace-pc-guard', '-fsanitize=address',
        '-fsanitize-address-use-after-scope'
    ]
    append_flags('CFLAGS', cflags)
    append_flags('CXXFLAGS', cflags)
    append_flags('ASAN_OPTIONS', ['abort_on_error=1', 'symbolize=0'])

    os.environ['CC'] = '/afl/afl-clang-fast'
    os.environ['CXX'] = '/afl/afl-clang-fast++'
    os.environ['FUZZER_LIB'] = '/libAFL.a'

    os.environ['AFLCHURN_DISABLE_FLIP'] = '1'


def build():
    prepare_build_environment()

    env = os.environ.copy()
    fuzzer_lib = env['FUZZER_LIB']
    env['LIB_FUZZING_ENGINE'] = fuzzer_lib
    if os.path.exists(fuzzer_lib):
        # Make /usr/lib/libFuzzingEngine.a point to our library for OSS-Fuzz
        # so we can build projects that are using -lFuzzingEngine.
        shutil.copy(fuzzer_lib, '/usr/lib/libFuzzingEngine.a')


    subprocess.check_call(['/bin/bash', '-ex', '/build.sh'], env=env)


def create_seed_file_for_empty_corpus(input_corpus):
    """Create a fake seed file in an empty corpus, skip otherwise."""
    if os.listdir(input_corpus):
        # Input corpus has some files, no need of a seed file. Bail out.
        return

    print('Creating a fake seed file in empty corpus directory.')
    default_seed_file = os.path.join(input_corpus, 'default_seed')
    with open(default_seed_file, 'w') as file_handle:
        file_handle.write('hi')


def prepare_seed(seed_dir):
    seed_corpus_dir = os.path.join(os.environ['OUT'], os.environ['FUZZ_TARGET'] + '_seed_corpus.zip')
    if os.path.exists(seed_corpus_dir):
        with zipfile.ZipFile(seed_corpus_dir) as zip_file:
            for seed_corpus_file in zip_file.infolist():
                if seed_corpus_file.filename.endswith('/'):
                    # Ignore directories.
                    continue

                # Allow callers to opt-out of unpacking large files.
                if seed_corpus_file.file_size > CORPUS_ELEMENT_BYTES_LIMIT:
                    continue

                chunk_size = 51200  # Read in 50 KB chunks.
                digest = hashlib.sha1()
                with zip_file.open(seed_corpus_file.filename, 'r') as file_handle:
                    chunk = file_handle.read(chunk_size)
                    while chunk:
                        digest.update(chunk)
                        chunk = file_handle.read(chunk_size)
                
                sha1sum = digest.hexdigest()
                dst_path = os.path.join(seed_dir, sha1sum)
                with zip_file.open(seed_corpus_file.filename, 'r') as src_file:
                    with open(dst_path, 'wb') as dst_file:
                        shutil.copyfileobj(src_file, dst_file)
    
    create_seed_file_for_empty_corpus(seed_dir)
      

def prepare_fuzz_environment(input_corpus):
    """Prepare to fuzz with AFL or another AFL-based fuzzer."""
    # Tell AFL to not use its terminal UI so we get usable logs.
    os.environ['AFL_NO_UI'] = '1'
    # Skip AFL's CPU frequency check (fails on Docker).
    os.environ['AFL_SKIP_CPUFREQ'] = '1'
    # No need to bind affinity to one core, Docker enforces 1 core usage.
    os.environ['AFL_NO_AFFINITY'] = '1'
    # AFL will abort on startup if the core pattern sends notifications to
    # external programs. We don't care about this.
    os.environ['AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES'] = '1'
    # Don't exit when crashes are found. This can happen when corpus from
    # OSS-Fuzz is used.
    os.environ['AFL_SKIP_CRASHES'] = '1'
    # Shuffle the queue
    os.environ['AFL_SHUFFLE_QUEUE'] = '1'
    os.environ['AFLCHURN_INST_RATIO'] = '80'

    # AFL needs at least one non-empty seed to start.
    prepare_seed(input_corpus)


def get_dictionary_path(target_binary):
    """Return dictionary path for a target binary."""
    # if get_env('NO_DICTIONARIES'):
    #     # Don't use dictionaries if experiment specifies not to.
    #     return None

    dictionary_path = target_binary + '.dict'
    if os.path.exists(dictionary_path):
        return dictionary_path

    options_file_path = target_binary + '.options'
    if not os.path.exists(options_file_path):
        return None

    config = configparser.ConfigParser()
    with open(options_file_path, 'r') as file_handle:
        try:
            config.read_file(file_handle)
        except configparser.Error as error:
            raise Exception('Failed to parse fuzzer options file: ' +
                            options_file_path) from error

    for section in config.sections():
        for key, value in config.items(section):
            if key == 'dict':
                dictionary_path = os.path.join(os.path.dirname(target_binary),
                                               value)
                if not os.path.exists(dictionary_path):
                    raise ValueError('Bad dictionary path in options file: ' +
                                     options_file_path)
                return dictionary_path
    return None


def run_fuzz():
    prepare_fuzz_environment(INPUT_DIR)
    target = os.environ['FUZZ_TARGET']
    target_binary = os.path.join(os.environ['OUT'], target)
    command = [
        '/afl/afl-fuzz',
        '-i',
        INPUT_DIR,
        '-o',
        OUTPUT_DIR,
        # Use no memory limit as ASAN doesn't play nicely with one.
        '-m',
        'none',
        '-t',
        '1000+',  # Use same default 1 sec timeout, but add '+' to skip hangs.
    ]
    # Use '-d' to skip deterministic mode, as long as it it compatible with
    # additional flags.
    dictionary_path = get_dictionary_path(target_binary)
    if dictionary_path:
        command.extend(['-x', dictionary_path])

    command += [
        '--',
        target_binary,
        # Pass INT_MAX to afl the maximize the number of persistent loops it
        # performs.
        '2147483647'
    ]
    print('[run_afl_fuzz] Running command: ' + ' '.join(command))
    timeout = float(os.environ.get('FUZZ_TIMEOUT'))

    try:
        p = subprocess.Popen(command, start_new_session=True)
        p.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(p.pid), signal.SIGTERM)


if __name__ == '__main__':
    import sys

    if len(sys.argv) == 2:
        if sys.argv[1] == 'run':
            run_fuzz()
        elif sys.argv[1] == 'build':
            initialize_env()
            build()


