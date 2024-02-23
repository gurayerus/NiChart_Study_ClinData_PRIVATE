#!/bin/bash

##root=/cbica/projects/ISTAGING/NiChart/Pipelines/Data_Consolidation/NiChart_Study_ClinData_PRIVATE 
root=$(realpath `pwd`/..)

mkdir -pv ${root}/Logs

# run AD
for subfolder in ${root}/Studies/*/; do
    study=$(basename ${subfolder})
    qsub -wd ${root} ${root}/Studies/${study}/scripts/${study}_DX_AD.sh 
    

#     cd $root
#     echo ${root}/Studies/${study}/scripts/${study}_DX_AD.sh
#     ${root}/Studies/${study}/scripts/${study}_DX_AD.sh

#     read -p ee

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
