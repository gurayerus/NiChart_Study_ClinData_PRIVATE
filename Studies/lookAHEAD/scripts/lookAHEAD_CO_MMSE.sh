#!/bin/bash

######START OF EMBEDDED SGE COMMANDS ##########################
#$ -l h_vmem=30G
#$ -pe threaded 2
#$ -N sge_lookAHEAD_CO_MMSE
#$ -j y
#$ -o ./Logs/$JOB_NAME-$JOB_ID.log
############################## END OF DEFAULT EMBEDDED SGE COMMANDS #######################

python ./Scripts/util_DX.py -d MMSE -s lookAHEAD -p ./Studies/lookAHEAD/output/lookAHEAD_CO_MMSE.csv -vt CO
