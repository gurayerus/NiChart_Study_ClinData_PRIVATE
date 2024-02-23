import numpy as np
import pandas as pd
import os

# With mapping the race

# Format: Study | PID (ID) | Race | Ethnicity (Hispanic/non-Hispanic)

def clinical_extract_race_singleStudy(df_study, study, id_col, race_col, race_map, ethnicity_col, ethnicity_map):
    print("Processing: " + study)
    
    lst_cols = [id_col, race_col, ethnicity_col]
    
    df = df_study[[id_col]]
    df.loc[:,'Study'] = [study for i in range(len(df))]

    if(lst_cols != []):
        for col in lst_cols:
            if(str(col) not in [np.nan, 'nan', '', float('nan')]):
                df.loc[:,str(col)] = df_study[col].values
        
    if(str(race_col) not in [np.nan, 'nan', '', float('nan')]):
        df = df.rename(columns={race_col:'Race'})
        # map the race by dictionary
        df['Race_NC'] = df['Race'].map(race_map)
        df = df.dropna()
        df = df.drop_duplicates(ignore_index=True)
        df = df.reset_index(drop=True)
    else:
       df['Race'] = np.nan
       df['Race_NC'] = np.nan
   
    if(str(ethnicity_col) not in [np.nan, 'nan', '', float('nan')]):
        df = df.rename(columns={ethnicity_col:'Ethnicity'})
        # map the ethnicity by dictionary
        df['Ethnicity_NC'] = df['Ethnicity'].map(ethnicity_map)
    else:
        df['Ethnicity'] = np.nan
        df['Ethnicity_NC'] = np.nan
    
    
    df = df.rename(columns={id_col:'PID'})
    
    if('ID' in df.columns):
        df = df.drop('ID', axis=1)
    
    return df
    

if __name__ == "__main__":
    import numpy as np
    import pandas as pd
    import json
    import argparse

    import warnings
    warnings.filterwarnings("ignore")
    
    
    parser = argparse.ArgumentParser(description = 'To process the Race and Ethnicity from the Clinical data.')
    parser.add_argument('-s','--study', type = str, help = 'Name of the study.', default = None)
    parser.add_argument('-i','--input_path', type = str, help = 'Path of the input file.', default = None)
    parser.add_argument('-d','--dict_path', type = str, help = 'Path of the mapping dictionary file.', default = None)
    parser.add_argument('-o','--output_path', type = str, help = 'Path for the output file.', default = None)
    args = parser.parse_args()
    
    study_name = args.study
    input_path = args.input_path
    dict_path = args.dict_path
    output_path = args.output_path
    
    #print("Study name: %s" % study_name)
    print("File path: %s " % input_path)
    print("Mapping dictionary path: %s" % dict_path)

    # Load df
    dfs = pd.read_csv(input_path, low_memory=False)
    print("Loaded df: %s" % study_name)

    
    ### Use concatenated json
    # Load Clinical Race Ethnicity ColNames and Map
    with open(dict_path) as json_file:
        json_content = json_file.read()
    meta_dict = json.loads(json_content)
    meta_dict = meta_dict[study_name]
    print('Loaded mapping file')

    
    fout = clinical_extract_race_singleStudy(dfs, study_name, meta_dict['ID_Col'],
                                              meta_dict['Race_Col'], meta_dict['Race_Map'],
                                              meta_dict['Ethnicity_Col'], meta_dict['Ethnicity_Map'])
    
    fout.to_csv(output_path, index=False) # Save to a CSV file
    
    #fout.head(5)
    print("Race and Ethnicity for %s is extracted!\nOutput: %s\n" % (study_name, output_path))
