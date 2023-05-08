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
        '--build-arg', 
        'B_SRC=/',
        '--build-arg',
        'B_OUT=/out',
        '--cache-from',
        target_tag,
        '--file',
        os.path.join('targets', target, 'Dockerfile'),
        os.path.join('targets', target)
        ]

    try:
        if quiet:
            subprocess.check_call(build_target_cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        else:
            subprocess.check_call(build_target_cmd)
        print('[+] Done: target: {}'.format(target_tag))
    except Exception as e:
        print('[-] Falied to build target: {}'.format(target_tag))
        return False
    
    return True
    

def build_fuzzer(fuzzer, target, build_log_path=None, quiet=False):
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

    try:
        if quiet:
            with open(build_log_path, 'w') as f:
                subprocess.check_call(build_fuzzer_cmd, stderr=f, stdout=f)
        else:
            subprocess.check_call(build_fuzzer_cmd)
        print('[+] Done: fuzzer: {}'.format(fuzzer_tag))
    except Exception as e:
        print('[-] Falied to build fuzzer: {}'.format(fuzzer_tag))
        return False
    
    
    return True


def run_fuzzer(fuzzer, target, trial_id, timeout, fuzz_dir, quiet=False, cpu=0):
    target_tag = os.path.join('fuzztest', 'target', target) 
    fuzzer_tag = os.path.join(target_tag, fuzzer)

    name = '{}_{}_{}_{}'.format(os.urandom(4).hex(), target, fuzzer, trial_id)


    os.makedirs(os.path.join(fuzz_dir, 'input'), exist_ok=True)
    os.makedirs(os.path.join(fuzz_dir, 'output'), exist_ok=True)
    run_fuzzer_cmd = 'docker run -e FUZZ_TIMEOUT={} --rm --cpus=1 --cpuset-cpus={} -v {}:/data --name {} {} 2>&1 | tee {}/fuzz.log'.format(timeout, cpu, fuzz_dir, name, fuzzer_tag, fuzz_dir)
    
    print('[+] Running fuzzer: {}'.format(run_fuzzer_cmd))
    try:
        if quiet:
            subprocess.check_call(run_fuzzer_cmd, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        else:
            subprocess.check_call(run_fuzzer_cmd, shell=True)
        print('[+] Done: target: {}, fuzzer: {}, trial: {}'.format(target, fuzzer, trial_id))
    except Exception as e:
        print('[-] Falied to run fuzzing: target: {}, fuzzer: {}, trial: {}'.format(target, fuzzer, trial_id))
        return False
    
    return True
    


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
    parser.add_argument('--fuzzer-build-log-dir', type=str, help='directory to store fuzzer build logs', default='./fuzzer_build_logs')

    args = parser.parse_args()
    args.data_dir = os.path.abspath(args.data_dir)
    args.fuzzer_build_log_dir = os.path.abspath(args.fuzzer_build_log_dir)

    fuzzers = args.fuzzers
    targets = args.targets

    if args.build:
        os.makedirs(args.fuzzer_build_log_dir, exist_ok=True)
        build_baseimag()

        if args.parallel_build > 0:
            from multiprocessing import Pool

            pool = Pool(args.parallel_build)
            try:
                results = pool.starmap(build_target, [(target, True) for target in targets])

                if results.count(True) != len(results):
                    print('[-] Failed!')
                    exit(-1)
            except KeyboardInterrupt:
                pool.terminate()
                pool.join()
                exit()
            finally:
                pool.close()

            pool = Pool(args.parallel_build)
            try:
                results = pool.starmap(build_fuzzer, [(fuzzer, target, os.path.join(args.fuzzer_build_log_dir, '{}_{}.log'.format(target, fuzzer)), True) for target in targets for fuzzer in fuzzers])
                if results.count(True) != len(results):
                    print('[-] Failed!')
                    exit(-1)
            except KeyboardInterrupt:
                pool.terminate()
                pool.join()
                exit()
            finally:
                pool.close()
        else:
            for target in targets:
                build_target(target)
            for target in targets:
                for fuzzer in fuzzers:
                    build_fuzzer(fuzzer, target)


    if args.run:
        import psutil
        # get all core id
        cpu_ids = psutil.Process(1).cpu_affinity()
        os.makedirs(args.data_dir, exist_ok=True)
        if args.parallel_run > 0:
            from multiprocessing import Pool, cpu_count

            if args.parallel_run > cpu_count():
                raise ValueError('Parallel count must less than the number of total cpu cores ')

            pool = Pool(args.parallel_run)
            idx = 0


            try:
                for trial_id in range(args.count):
                    trial_dir = os.path.join(args.data_dir, 'trial_{}'.format(trial_id))
                    for target in targets:
                        for fuzzer in fuzzers:
                            fuzz_dir = os.path.join(trial_dir, target, fuzzer)
                            os.makedirs(fuzz_dir, exist_ok=True)
                            pool.apply_async(run_fuzzer, args=(fuzzer, target, trial_id, args.max_time, fuzz_dir), kwds={'quiet': True, 'cpu': cpu_ids[idx]})
                            idx = (idx + 1) % args.parallel_run
                pool.close()
                pool.join()
            except KeyboardInterrupt:
                pool.terminate()
                pool.join()

        else:
            try:
                for trial_id in range(args.count):
                    trial_dir = os.path.join(args.data_dir, 'trial_{}'.format(trial_id))
                    for target in targets:
                        for fuzzer in fuzzers:
                            fuzz_dir = os.path.join(trial_dir, target, fuzzer)
                            os.makedirs(fuzz_dir, exist_ok=True)
                            run_fuzzer(fuzzer, target, trial_id, args.max_time, fuzz_dir, cpu=cpu_ids[0])
            except KeyboardInterrupt:
                pass