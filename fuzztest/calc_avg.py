import pandas as pd


if __name__ == '__main__':
    import sys

    if len(sys.argv) != 2:
        print('Usage: calc_tte.py <results.csv>')
        sys.exit(1)
    
    results = pd.read_csv(sys.argv[1])

    print('target,fuzzer,valuable_count,tte_avg,total_crashes_avg')
    targets = {}
    for index, row in results.iterrows():
        if row['target'] not in targets:
            targets[row['target']] = {}
        
        if row['fuzzer'] not in targets[row['target']]:
            targets[row['target']][row['fuzzer']] = [[], []]
        
        if row['tte'] != -1:
            targets[row['target']][row['fuzzer']][0].append(row['tte'])
        if row['total_crashes'] != 0:
            targets[row['target']][row['fuzzer']][1].append(row['total_crashes'])
    
    for target in targets:
        for fuzzer in targets[target]:
            if len(targets[target][fuzzer][0]) == 0:
                tte = None
            else:
                tte = sum(targets[target][fuzzer][0]) / len(targets[target][fuzzer][0])
            
            if len(targets[target][fuzzer][1]) == 0:
                crashes = None
            else:
                crashes = sum(targets[target][fuzzer][1]) / len(targets[target][fuzzer][1])
            print('{}, {}, {}, {},{}'.format(target, fuzzer, len(targets[target][fuzzer][0]), tte, crashes))
            
            