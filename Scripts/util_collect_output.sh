#!/bin/bash

root=$(realpath `pwd`/..)

indir=${root}/Studies
outdir=${root}/output

mkdir -pv $outdir

for std in `ls -1 ${root}/Studies | cut -d/ -f1`; do
    echo "Copy out data for:  $std"
    
    outstd=${outdir}/${std}
    instd=${indir}/${std}/output
    
    if [ ! -d $instd ]; then
        echo "Study output data not found, skip: $instd"
        continue;
    fi
    
    if [ -e $outstd ]; then
        echo "Output for study exists, skip. Remove the folder and rerun to update it: $outstd"
    else
        echo "Copying data for study to output: $std"
        cp -r $instd $outstd
    fi
        
done
