import numpy as np
import pandas as pd
import re
from collections import defaultdict
import json
import os
import argparse
import pickle
    
######################step 0: get all the dictionary #######################################################
### load clinical data dic {study: clinical study path}
with open('./Reference/clin_input_dic.json', 'r') as json_file:
    clin_input_dic = json.load(json_file)

### load mri data dic {study : mri study path}
with open('./Reference/mri_input_dic.json', 'r') as json_file:
    mri_input_dic = json.load(json_file)

### current name is not matched
mri_input_dic['ADNI'] = mri_input_dic['ADNI-ADSP']
mri_input_dic['NACC'] = mri_input_dic['NACC-ADSP']
mri_input_dic['WRAP'] = mri_input_dic['WRAP-ADSP']

### load diagnosis_naming_dic {study: {diangosis: diagnosis name, congitive: cognitive name}}
with open('./Reference/diagnosis_naming_dic.json', 'r') as json_file:
    diagnosis_naming_dic = json.load(json_file)

### diagnosis mapping   
with open('./Reference/diagnosis_value_mapping.json', 'r') as json_file:
    diagnosis_value_mapping = json.load(json_file)
    
######################step 1: clean clinical dataset and reformulate column names ###########################

def clean_clin_data(study, 
                    clin_input_dic, 
                    Diagnosis,
                    diagnosis_naming_dic):
    '''
    return 
        1) a clean dataframe with naming matching with MRI data 
            - contains column: [ID, MRID, Date, Visit Code, Diagnosis / Cognitive]
        2) a flag indicate whether the diagnosis exist or not(True: Not exist, False: Exist)
      
    inputs:  
        study               : Study name
        clin_input_dic      : a dictionary for clinical {study name: clinical study path}
        Diagnosis           : Diagnosis / Cognitive
        diagnosis_naming_dic: a dictionary contains diagnosis name mapping
    '''
    
    flag = False 
    
    ### columns we want to merge MRI data
    desire_output_col = ['ID','MRID', 'Date', 'Visit_Code', Diagnosis]
    
    ### for UKBB, ADNI and AIBL, use low_memory to save space
    if study == 'UKBB':
        if Diagnosis not in diagnosis_naming_dic[study].keys() or diagnosis_naming_dic[study][Diagnosis] == '':
            ukbb_col = ['MRI_ID','eid','Date','Visit_Code']
        else:
            ukbb_col = ['MRI_ID','eid','Date','Visit_Code', diagnosis_naming_dic[study][Diagnosis]]
        df = pd.read_csv(clin_input_dic[study], usecols= ukbb_col, low_memory= False)
    elif study in ['ADNI' , 'AIBL']:
        df = pd.read_csv(clin_input_dic[study], low_memory= False)
    else:
        df = pd.read_csv(clin_input_dic[study])
    
    ### if diganosis don't exist, put Nan value to the diagnosis column
    if Diagnosis not in diagnosis_naming_dic[study].keys() or diagnosis_naming_dic[study][Diagnosis] == '':
        df[Diagnosis] = np.nan 
        flag = True 
    else:
        df.rename(columns = {diagnosis_naming_dic[study][Diagnosis]: Diagnosis}, inplace = True)
    
    ### if any desire column not exist in dataframe, create an empty column for it
    for col_name in desire_output_col:
        if col_name not in df.columns:
            df[col_name] = np.nan 
    
    ##########################################################################################
    # rules defined for each specific study, this need to be done manually
    
    ####### For BLSA ##########
    if study == 'BLSA':
        df['MRID'] = df['IDMATCH'].apply(lambda x: 'BLSA_' + '{:04d}'.format(int(x.split('_')[0])) + '_' + x.split('_')[1])
        # need to done later since we don't have scan date in clinical data

    ####### For GSP OR HCP-YA ###########
    elif study == 'GSP' or study == 'HCP-YA':
        df['MRID'] = df['ID']

    ####### For HABS ##########
    elif study == 'HABS':
        df['MRID'] = df['ID'] + '_' + df['Date'] + '_' + df['Visit_Code']
        
    ####### For HCP-Aging #####
    elif study == 'HCP-Aging':
        df['MRID'] = df['ID'] + '_V1_MR'
         
    ######## For ADNI ##########
    elif study == 'ADNI':
        df['MRID'] = df['ID'] + '_' + df['Date']
        
    ######## For UKBB ##########
    elif study == 'UKBB':
        df['ID'] = df['eid']
        df['MRID'] = df['MRI_ID']
    
    ####### For AIBL #############
    elif study == 'AIBL':
        df['MRID'] = df['MRI_ID']
        
    ####### For WRAP #############
    ### NEED TO DEAL WITH THE MRID type issue
        
        
    ### use only desire output columns and drop all nan values for Diagnosis
    df = df[desire_output_col].dropna(subset = [Diagnosis]).reset_index(drop = True)
    return df, flag



######################step 2: Combine MRI data with Clinical Data ###########################
def combined_mri_clin(study, 
                      mri_input_dic, 
                      clin_input_dic, 
                      Diagnosis, 
                      diagnosis_naming_dic):
    '''
    combined mri and clin data based on MRID, if we don't have MRID, do xxxxx
    input: 
        study:              a study for example "OASIS3", "ADNI", etc
        mri_input_dic:      a dictionary with key-value (study : study-mri-path)
        clin_input_dic:     a dictionary with key-value (study : study-clinical-path)
        clin_rename_dic:    a dictionary with key-value (study: renaming map)
        Diagnosis:          Diagnosis column
        json_file_path:     json file path to store the information for 
        
    output: 
        A merged csv file with least information, flag (indicate True: diagnosis not exist, False: exist)
    '''
    
    ### a flag indicate whether diagnosis exist or not 
    flag = False
    
    if study == 'UKBB':
        df_mri =  pd.read_csv(mri_input_dic[study], low_memory=False)
        df_clin, flag = clean_clin_data(study, clin_input_dic, Diagnosis, diagnosis_naming_dic)
    else:    
        df_mri =  pd.read_csv(mri_input_dic[study])
        df_clin, flag = clean_clin_data(study, clin_input_dic,  Diagnosis, diagnosis_naming_dic)
        
    
    if study == 'HABS':
        df_mri['ScanDate'] = df_mri['MRID'].apply(lambda x: x.split('_')[2])
        
    if study == 'AIBL':
        df_mri['PID'] = df_mri['PTID']

    
    ################################# define three additional column ##############################################
    # diagnosis_IM: diagnosis is missing or not?
    # diagnosis_extrapolate_2.0: extrapolation within 2 years range
    # diagnosis: name matching
    diagnosis_missing_col = '{}_IM'.format(Diagnosis)
    diagnosis_extrapolate_col = '{}_extrapolate'.format(Diagnosis)
    ###############################################################################################################
    
    ### reduce redundant columns
    
    df_total = pd.merge(df_mri, df_clin, on = 'MRID', how = 'left')
    df_total[diagnosis_missing_col] = df_total[Diagnosis].isna()
    df_total[diagnosis_extrapolate_col] = np.nan
    df_total['Study'] = study 
    
    for i in ['ScanDate','VisCode']:
        if i not in df_total:
            df_total[i] = np.nan 
            
    final_col_use = ['Study','MRID','PID','ScanDate','VisCode',Diagnosis,diagnosis_missing_col,diagnosis_extrapolate_col ]
    return df_total[final_col_use], flag, df_clin




######################step 3: Diagnosis Column extrapolation ###########################
def find_closest_value_visit_code(row, df2, diagnosis): 
    
    '''
    when Date is not avaiable, chose visit code instead
    input:
        row: a row for each MRI data
        df2: a cleaned clinical data contains diagnosis, PID, VisitCode 
        diagnosis: diagnosis 
    
    output:
        a panda series with two values [diagnosis, how much close (0 means the value is already there, 1 means the data is extrapolate with the nearest 1 day)
    '''
     
    if not pd.isna(row[diagnosis]):
        return pd.Series([row[diagnosis],0])
    
    id = row['PID']
    vs = row['VisCode']
    
    filtered_df2 = df2[(df2['ID'] == id)] ## Same Subject 
   
    
    filtered_df2 = filtered_df2[[diagnosis,'Visit_Code']].dropna()
    
    if filtered_df2.empty:
        return None
    
    else:
        filtered_df2['date-diff'] = filtered_df2['Visit_Code'].apply(lambda x: abs(int(x) - int(vs)))
        min_diff = filtered_df2['date-diff'].min()
        closest_row = filtered_df2[filtered_df2['date-diff'] == min_diff]
        result = closest_row[diagnosis].iloc[0]
        return pd.Series([result, min_diff])
        
    
def find_closest_value_date(row, df2, diagnosis):    
    
    '''
    use date as the main part
    input:
        row: a row for each MRI data
        df2: a cleaned clinical data contains diagnosis, PID, Date
        diagnosis: diagnosis 
    
    output:
        a panda series with two values [diagnosis, how much close (0 means the value is already there, 1 means the data is extrapolate with the nearest 1 day)
    '''
    
    if not pd.isna(row[diagnosis]):
        return pd.Series([row[diagnosis],0])
    
    id = row['PID']
    date = row['ScanDate']
    
    if pd.isna(date):
        return pd.Series([np.nan, np.nan])
    
    filtered_df2 = df2[df2['ID'] == id]
    filtered_df2 = filtered_df2[[diagnosis,'Date']].dropna()
    
    if filtered_df2.empty:
        return pd.Series([np.nan, np.nan])
    
    else:
        filtered_df2['date-diff'] = filtered_df2['Date'].apply(lambda x: abs(x - date))
        min_diff = filtered_df2['date-diff'].min()
        closest_row = filtered_df2[filtered_df2['date-diff'] == min_diff ]
        result = closest_row[diagnosis].iloc[0]
        return pd.Series([result, min_diff.days])
        
    
def extrapolation(combined_df_,
                  clin_df, 
                  Diagnosis,  
                  flag = False):
    
    '''
    Perform extrapolation on the dataset, return a new dataframe with extrapolated values
    
    Input: 
        combined_df:     combined dataframe from step 1 (the combination of clinical and mri data)
        clin_df:         a cleaned version of clinical data
        Diagnosis:       Diagnosis
        flag:            True if clin_input_dic doesn't contain Diagnosis 
    '''
    
    combined_df = combined_df_
    diagnosis_missing_col = '{}_IM'.format(Diagnosis)
    diagnosis_extrapolate_col = '{}_extrapolate'.format(Diagnosis)
    
    if Diagnosis not in combined_df.columns:
        combined_df[Diagnosis] = np.nan 
        
    if diagnosis_missing_col not in combined_df.columns:
        combined_df[diagnosis_missing_col] = True 
    
    if diagnosis_extrapolate_col not in combined_df.columns:
        combined_df[diagnosis_extrapolate_col] = np.nan 
        
        
    final_col = ['Study','MRID','PID',Diagnosis, diagnosis_missing_col, diagnosis_extrapolate_col, 'Delta']
    
    #### directly return combined df if diagnosis doesn't exist
    if flag: 
        combined_df['Delta'] = np.nan
        return combined_df[final_col]
    
    #####
    study = combined_df['Study'].unique()[0]
     
    df_clin = clin_df 
    df_total = combined_df
    df_total['Delta'] = np.nan
        
    if 'Date' in df_clin.columns and df_clin['Date'].isna().sum() != len(df_clin): ### if Date exist 
        df_clin['Date'] = pd.to_datetime(df_clin['Date'])
        df_total['ScanDate'] = pd.to_datetime(df_total['ScanDate'])
        
        df_total[[diagnosis_extrapolate_col, 'Delta']] = df_total.apply(lambda row: find_closest_value_date(row, df_clin, Diagnosis), axis = 1)
        
    elif df_clin['Visit_Code'].isna().sum() != len(df_clin): ### if Visit_Code exist
        df_clin = df_clin[~df_clin['Visit_Code'].isin(['dNA','NA'])]
        df_clin['Visit_Code']=df_clin['Visit_Code'].apply(lambda x: int(x[1:]))
        df_total['VisCode']= df_total['VisCode'].apply(lambda x: int(x[1:]))  
    
        df_total[[diagnosis_extrapolate_col,'Delta']] = df_total.apply(lambda row: find_closest_value_visit_code(row, df_clin, Diagnosis), axis = 1)
            
    return df_total[final_col]


######################step 4: column name conversion + value grouping ###########################
def col_name_conversion(df, diagnosis, diagnosis_value_mapping, var_type = 'DX'):
    '''
    maping: diganosis to user-defined name
    format: 
        {}_{Diagnosis}_NC
        {}_{Diagnosis_IM}_NC
        {}_{Diagnosis_extrapolate}_NC
        {}_{Diagnosis}_delta_NC
    '''
    
    diagnosis_conversion_dic = {
        'Diagnosis': 'AD'
    }
    
    ### based on Liz Code for Diagnosis Mapping (other than AD-Diagnosis)
    clin_map = {0 : 'Negative/absent',
                1 : 'Positive/present',
                2 : 'Remote/inactive',
                5 : 'Pre-Diabetes',
                8 : 'Unknown'
    }
    
    prefix = var_type
    
    if diagnosis not in diagnosis_conversion_dic.keys():
        conversion_name = diagnosis
    else:
        conversion_name = diagnosis_conversion_dic[diagnosis]
    
    #-----------------------------------------------------------
    study = df.loc[0, 'Study']
    df['{}_{}_is_imputation_NC'.format(prefix, conversion_name)] = False
    
    if study and study == 'UKBB':
        df['{}_{}_is_imputation_NC'.format(prefix, conversion_name)] = df[diagnosis].isna()
        df['{}_extrapolate'.format(diagnosis)] = df['{}_extrapolate'.format(diagnosis)].fillna('CN')
    
    #------------------------------------------------------------
    
    diganosis_col_name = '{}_{}_original_NC'.format(prefix, conversion_name)
    diganosis_missing_col_name = '{}_{}_IM_NC'.format(prefix, conversion_name)
    diagnosis_extrapolate_col_name = '{}_{}_Multi_Class_NC'.format(prefix, conversion_name)
    diagnosis_delta_col_name = '{}_{}_delta_NC'.format(prefix, conversion_name)
    
    df = df.rename(columns = {diagnosis:diganosis_col_name ,
                         '{}_IM'.format(diagnosis): diganosis_missing_col_name,
                         '{}_extrapolate'.format(diagnosis):diagnosis_extrapolate_col_name,
                         'Delta' : diagnosis_delta_col_name})
    
    if diagnosis == 'Diangosis':
        df['{}_{}_NC'.format(prefix, conversion_name)] = df[diagnosis_extrapolate_col_name].replace(diagnosis_value_mapping)
    elif prefix == 'DX':
        df['{}_{}_NC'.format(prefix, conversion_name)] = df[diagnosis_extrapolate_col_name].replace(clin_map)
    elif prefix == 'CO':
        df['{}_{}_NC'.format(prefix, conversion_name)] = df[diagnosis_extrapolate_col_name]
    else:
        ### current do nothing, will add more functionalities later...
        pass

    return df


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description = 'Process the Diagnosis from MRI and Clinical data!')
    parser.add_argument('-d','--diagnosis', type = str, help = 'Diagnosis input', default = None)
    parser.add_argument('-s','--study', type = str, help = 'Study input', default = None)
    parser.add_argument('-p','--path', type = str, help = 'Path input', default = None)
    parser.add_argument('-vt','--var_type', type = str, help = 'variable type', default = 'DX' , choices=['DX', 'CO'])

    args = parser.parse_args()
    Diagnosis = args.diagnosis
    study     = args.study
    path      = args.path
    var_type  = args.var_type
    
    print('Study: ', study)
    print('Diagnosis: ', Diagnosis)
    print('path: ', path)
    print('var type: ', var_type)
    
    if var_type not in ['CO','DX']:
        raise Exception('Currently only support var type in CO or DX')
    
    if study not in mri_input_dic.keys() or study not in clin_input_dic.keys():
        raise Exception('Study {} not included in either mri data or clinical data, please check'.format(study))
        
    
    ### if the clinical data cleaning and mri combining is done, skip step 1 and step 2
    
    if os.path.exists('./Studies/{}/intermediate/{}_mri_clinical_combined.csv'.format(study, study)):
        print('clinical data cleaning and MRI data merging is done, skip step 1 and step 2...')
        
        df_combined = pd.read_csv('./Studies/{}/intermediate/{}_{}_mri_clinical_combined.csv'.format(study, study, Diagnosis))
        with open('./Studies/{}/intermediate/{}_{}.pkl'.format(study,study, Diagnosis), 'rb') as f:
            flag = pickle.load(f)
        df_clin = pd.read_csv('./Studies/{}/intermediate/{}_{}_cleaned_clinical.csv'.format(study,study, Diagnosis))
                              
    else:

        ### step 1 and step 2: clean the clinical data and combine them
        df_combined, flag, df_clin = combined_mri_clin( study = study, 
                                                        mri_input_dic = mri_input_dic, 
                                                        clin_input_dic = clin_input_dic,
                                                        Diagnosis = Diagnosis,
                                                        diagnosis_naming_dic = diagnosis_naming_dic)

        out_int_dir = os.path.join('.', 'Studies', study, 'intermediate')
        os.makedirs(out_int_dir, exist_ok=True)
            
        df_combined.to_csv(os.path.join(out_int_dir, study + '_' + Diagnosis + '_mri_clinical_combined.csv'), index = False)
        df_clin.to_csv(os.path.join(out_int_dir, study + '_' + Diagnosis + '_cleaned_clinical.csv'), index = False)

        with open(os.path.join(out_int_dir, study + '-' + Diagnosis + '.pkl'), 'wb') as f:
            pickle.dump(flag, f)
    
    ### step 3: diagnosis column with extrapolation
    data = extrapolation(combined_df_ = df_combined,
                         clin_df = df_clin, 
                         Diagnosis = Diagnosis,  
                         flag = flag)
    
    ##  step 4: conversion the name 
    data = col_name_conversion(data, Diagnosis, diagnosis_value_mapping , var_type = var_type)
    
    ## Make dir for out file
    parent_dir = os.path.dirname(path)
    os.makedirs(parent_dir, exist_ok=True)
    
    data.to_csv(path, index = False)
    
    print('File has successfully stored at: ', path)  
