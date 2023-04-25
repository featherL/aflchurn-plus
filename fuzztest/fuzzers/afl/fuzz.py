#!/bin/python3

import subprocess
import os
import shutil
import zipfile
import hashlib
import signal


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

    os.environ['CC'] = 'clang'
    os.environ['CXX'] = 'clang++'
    os.environ['FUZZER_LIB'] = '/libAFL.a'


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
    if os.path.exists('/out/seed_corpus.zip'):
        with zipfile.ZipFile('/out/seed_corpus.zip') as zip_file:
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

    # AFL needs at least one non-empty seed to start.
    prepare_seed(input_corpus)


def run_fuzz():
    prepare_fuzz_environment(INPUT_DIR)
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

    command += [
        '--',
        '/out/target',
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


