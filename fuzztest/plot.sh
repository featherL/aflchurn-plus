#!/bin/bash

if [ -z ${AFL_PLOT_PATH+x} ]; then
    echo "Error: AFL_PLOT_PATH is not set" >&2
    exit 1
fi

if [ ! -f $AFL_PLOT_PATH ]; then
    echo "Error: AFL_PLOT_PATH is not found" >&2
    exit 1
fi

if [ $# -ne 1 ]; then
    echo "Usage: $0 <results dir>" >&2
    exit 1
fi

if [ ! -d $1 ]; then
    echo "Error: $1 is not a directory" >&2
    exit 1
fi

for trial in $(ls $1)
do
    trial_dir="$1/$trial"
    echo "[+] Handling trial: $trial..." >&2
    for target in $(ls $trial_dir)
    do
        target_dir="$trial_dir/$target"
        echo "  [+] Handling target: $target..." >&2
        for fuzzer in $(ls $target_dir)
        do
            fuzzer_dir="$target_dir/$fuzzer"
            echo "    [+] Handling fuzzer: $fuzzer..." >&2
            
            mkdir -p "$fuzzer_dir/plot"
            $AFL_PLOT_PATH "$fuzzer_dir/output" "$fuzzer_dir/plot"

            echo "    [+] Done fuzzer: $fuzzer" >&2
        done
        echo "  [+] Done target: $target" >&2
    done
    echo "[+] Done trial: $trial" >&2
done