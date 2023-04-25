#!/bin/python3

import subprocess
import os


def build_baseimag(quiet=False):
    print('[+] Building base image')
    build_base_cmd = [
        'docker',
        'build',
        '--tag',
        'fuzztest/base',
        '--build-arg', 
        'BUILDKIT_INLINE_CACHE=1',
        '--cache-from',
        'fuzztest/base',
        '.'
    ]

    if quiet:
        subprocess.check_call(build_base_cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    else:
        subprocess.check_call(build_base_cmd)

    print('[+] Done: base image')


def build_target(target, quiet=False):
    target_tag = os.path.join('fuzztest', 'target', target) 

    print('[+] Building target: {}'.format(target_tag))

    build_target_cmd = [
        'docker', 
        'build', 
        '--tag', 
        target_tag, 
        '--build-arg', 
        'BUILDKIT_INLINE_CACHE=1',
        '--cache-from',
        target_tag,
        '--file',
        os.path.join('targets', target, 'Dockerfile'),
        os.path.join('targets', target)
        ]

    if quiet:
        subprocess.check_call(build_target_cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    else:
        subprocess.check_call(build_target_cmd)
    print('[+] Done: target: {}'.format(target_tag))
    

def build_fuzzer(fuzzer, target, quiet=False):
    target_tag = os.path.join('fuzztest', 'target', target) 
    fuzzer_tag = os.path.join(target_tag, fuzzer)

    print('[+] Building fuzzer: {}'.format(fuzzer_tag))
    
    build_fuzzer_cmd = [
        'docker',
        'build',
        '--tag',
        fuzzer_tag,
        '--build-arg', 
        'BUILDKIT_INLINE_CACHE=1',
        '--build-arg',
        'parent_image={}'.format(target_tag),
        '--cache-from',
        fuzzer_tag,
        '--file',
        os.path.join('fuzzers', fuzzer, 'Dockerfile'),
        os.path.join('fuzzers', fuzzer)
    ]

    if quiet:
        subprocess.check_call(build_fuzzer_cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    else:
        subprocess.check_call(build_fuzzer_cmd)
    print('[+] Done: fuzzer: {}'.format(fuzzer_tag))


def run_fuzzer(fuzzer, target, trial_id, timeout, data_dir, quiet=False):
    target_tag = os.path.join('fuzztest', 'target', target) 
    fuzzer_tag = os.path.join(target_tag, fuzzer)

    name = 'fuzztest_{}_{}_{}'.format(fuzzer, target, trial_id)
    result_dir = os.path.join(data_dir, name)

    os.makedirs(result_dir, exist_ok=True)
    os.makedirs(os.path.join(result_dir, 'input'), exist_ok=True)
    os.makedirs(os.path.join(result_dir, 'output'), exist_ok=True)

    run_fuzzer_cmd = 'docker run -e FUZZ_TIMEOUT={} --rm --cpus=1 -v {}:/data --name {} {} 2>&1 | tee {}/fuzz.log'.format(timeout, result_dir, name, fuzzer_tag, result_dir)
    
    print('[+] Running fuzzer: {}'.format(run_fuzzer_cmd))
    if quiet:
        subprocess.check_call(run_fuzzer_cmd, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    else:
        subprocess.check_call(run_fuzzer_cmd, shell=True)
    print('[+] Done: target: {}, fuzzer: {}, trial: {}'.format(target, fuzzer, trial_id))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Run fuzzing')
    parser.add_argument('-b', '--build', action='store_true', help='build all images')
    parser.add_argument('-r', '--run', action='store_true', help='run all fuzzing')
    parser.add_argument('-f', '--fuzzers', nargs='+', help='fuzzers to select')
    parser.add_argument('-t', '--targets', nargs='+', help='targets to fuzz')
    parser.add_argument('-c', '--count', type=int, help='trial count', default=1)
    parser.add_argument('-mt', '--max_time', type=float, help='max time for each trial', default=10 * 60)
    parser.add_argument('-pr', '--parallel-run', type=int, help='parallel count of runners', default=0)
    parser.add_argument('-pb', '--parallel-build', type=int, help='parallel count of builders', default=0)
    parser.add_argument('--data-dir', type=str, help='directory to store results', default='./results')

    args = parser.parse_args()
    args.data_dir = os.path.abspath(args.data_dir)

    fuzzers = args.fuzzers
    targets = args.targets

    if args.build:
        build_baseimag()

        if args.parallel_build > 0:
            from multiprocessing import Pool
            pool = Pool(args.parallel_build)

            try:
                for target in targets:
                    pool.apply_async(build_target, args=(target,), kwds={'quiet': True})
                pool.close()
                pool.join()
            except KeyboardInterrupt:
                pool.terminate()
                pool.join()
                exit()

            pool = Pool(args.parallel_build)
            try:
                for target in targets:
                    for fuzzer in fuzzers:
                        pool.apply_async(build_fuzzer, args=(fuzzer, target), kwds={'quiet': True})
                pool.close()
                pool.join()
            except KeyboardInterrupt:
                pool.terminate()
                pool.join()
                exit()
        else:
            for target in targets:
                build_target(target)
            for target in targets:
                for fuzzer in fuzzers:
                    build_fuzzer(fuzzer, target)


    if args.run:
        if args.parallel_run > 0:
            from multiprocessing import Pool
            pool = Pool(args.parallel_run)

            try:
                for trail_id in range(args.count):
                    for target in targets:
                        for fuzzer in fuzzers:
                            pool.apply_async(run_fuzzer, args=(fuzzer, target, trail_id, args.max_time, args.data_dir), kwds={'quiet': True})
                pool.close()
                pool.join()
            except KeyboardInterrupt:
                pool.terminate()
                pool.join()

        else:
            try:
                for trail_id in range(args.count):
                    for target in targets:
                        for fuzzer in fuzzers:
                            run_fuzzer(fuzzer, target, trail_id, args.max_time, args.data_dir)
            except KeyboardInterrupt:
                pass