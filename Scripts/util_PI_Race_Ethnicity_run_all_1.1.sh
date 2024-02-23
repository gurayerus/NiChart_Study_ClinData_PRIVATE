#!/bin/bash

for STUDY in ACCORD AIBL BLSA FITBIR HABS HCP-Aging lookAHEAD OASIS3 PENN SHIP UKBB WRAP ADNI BIOCARD CARDIA GSP HANDLS HCP-YA MESA OASIS4 PreventAD SPRINT WHIMS
do
python3 util_PI_Race_Ethnicity.py -s ${STUDY} \
-i ../Studies/${STUDY}/input/${STUDY}_ISTAGING_Clin.csv \
-d ../Reference/PI_Mapping_Race_Ethnicity.json \
-o ../Studies/${STUDY}/output/${STUDY}_PI_Race_Ethnicity.csv
done