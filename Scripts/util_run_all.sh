#!/bin/bash

root='THE ROOT DIR FOR THE FOLDER'

# run AD
for subfolder in ${root}/Studies/*/; do
    study=$(basename ${subfolder})
    qsub -wd ${root} ${root}/Studies/${study}/scripts/${study}_DX_AD.sh 
done

## run diagnosis
for diagnosis in Diabetes Hypertension; do 
    for subfolder in ${root}/Studies/*/; do
        study=$(basename ${subfolder})
        qsub -wd ${root} ${root}/Studies/${study}/scripts/${study}_DX_${diagnosis}.sh 
    done
done

## run cognitive
for cognitive in DSST MMSE MOCA; do 
    for subfolder in ${root}/Studies/*/; do
        study=$(basename ${subfolder})
        qsub -wd ${root} ${root}/Studies/${study}/scripts/${study}_CO_${cognitive}.sh 
    done
done