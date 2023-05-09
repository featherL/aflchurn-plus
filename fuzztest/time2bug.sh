#!/bin/bash

if [ $# -ne 1 ]; then
    echo "Usage: $0 <results dir>" >&2
    exit 1
fi

if [ ! -d $1 ]; then
    echo "Error: $1 is not a directory" >&2
    exit 1
fi


echo "trial,target,fuzzer,tte,total_crashes"


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
            
            
            # Get the time to first bug           
            tte=$(expr '-1')
            start_time=$(cat "$fuzzer_dir/output/fuzzer_stats" | grep start_time)
            if [ -z "$start_time" ]; then
                echo "      [-] fuzzer_stats empty!" >&2
                start_time=$(expr $(cat "$fuzzer_dir/output/plot_data" | sed -n '2p' | cut -d ',' -f 1))
            else
                start_time=$(expr $(echo $start_time | cut -d ':' -f 2))
            fi

            while read -r line
            do
                if [ $(echo $line | cut -c 1) == '#' ]; then
                    continue
                fi

                unix_time=$(expr $(echo $line | cut -d ',' -f 1))
                unique_crashes=$(expr $(echo $line | cut -d ',' -f 8))
                if [ $unique_crashes -gt 0 ]; then
                    tte=$(expr $unix_time - $start_time)
                    echo "      [+] Time to first bug: $tte" >&2
                    break
                fi
            done < "$fuzzer_dir/output/plot_data"

            # get total crashes
            total_crashes=$(expr $(tail -n 1 "$fuzzer_dir/output/plot_data" | cut -d ',' -f 8))
            echo "      [+] Total crashes: $total_crashes" >&2

            echo "$trial,$target,$fuzzer,$tte,$total_crashes"

            echo "    [+] Done fuzzer: $fuzzer" >&2
        done
        echo "  [+] Done target: $target" >&2
    done
    echo "[+] Done trial: $trial" >&2
done