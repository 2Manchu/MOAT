#!/bin/sh

if [ "$#" -ne 3 ]; then
    echo "Args Found: $# // Usage: $0 <stress-ng-cmd> <num-loops> <run-type=[baseline/interference-type-num-cores]>"
    exit 1
fi

stress_cmd=$1
num_loops=$2
run_type=$3

current_secs=$(date +%s)
log_dir="/run/media/root-mmcblk0p2/$run_type-$current_secs"
mkdir $log_dir

iter=0
while [ "$iter" -lt $num_loops ]; do
    log_file="$log_dir/$run_type-$iter.yaml"
    $stress_cmd --quiet --metrics --yaml "$log_file"
    iter=$(( iter + 1 ))

    echo "Measurement $iter complete."
done

echo "TESTING COMPLETE"
