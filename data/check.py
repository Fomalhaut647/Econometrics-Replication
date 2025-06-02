#!/usr/bin/env python3
"""
CHECK PROGRAM TO INPUT DATA AND CHECK
Python version of check.sas
INPUT FLAT DATA FILE OF NJ-PA DATA AND CHECK
"""

import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
from pathlib import Path

def read_data(file_path):
    """
    Read the flat data file with all the variables defined in the SAS program
    """
    # Define column names based on the SAS INPUT statement
    columns = [
        'SHEET', 'CHAINr', 'CO_OWNED', 'STATEr', 'SOUTHJ', 'CENTRALJ', 'NORTHJ',
        'PA1', 'PA2', 'SHORE', 'NCALLS', 'EMPFT', 'EMPPT', 'NMGRS', 'WAGE_ST',
        'INCTIME', 'FIRSTINC', 'BONUS', 'PCTAFF', 'MEAL', 'OPEN', 'HRSOPEN',
        'PSODA', 'PFRY', 'PENTREE', 'NREGS', 'NREGS11', 'TYPE2', 'STATUS2',
        'DATE2', 'NCALLS2', 'EMPFT2', 'EMPPT2', 'NMGRS2', 'WAGE_ST2', 'INCTIME2',
        'FIRSTIN2', 'SPECIAL2', 'MEALS2', 'OPEN2R', 'HRSOPEN2', 'PSODA2',
        'PFRY2', 'PENTREE2', 'NREGS2', 'NREGS112'
    ]
    
    try:
        # Try to read as space-separated values first
        df = pd.read_csv(file_path, sep=r'\s+', names=columns, header=None)
        
        # Convert to numeric where possible, replacing '.' with NaN
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    except:
        # If that fails, try comma-separated
        try:
            df = pd.read_csv(file_path, names=columns, header=None)
            
            # Convert to numeric where possible, replacing '.' with NaN
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
        except:
            print(f"Error reading file {file_path}")
            return None

def calculate_derived_variables(df):
    """
    Calculate derived variables as defined in the SAS program
    """
    # Employment totals
    df['EMPTOT'] = df['EMPPT'] * 0.5 + df['EMPFT'] + df['NMGRS']
    df['EMPTOT2'] = df['EMPPT2'] * 0.5 + df['EMPFT2'] + df['NMGRS2']
    df['DEMP'] = df['EMPTOT2'] - df['EMPTOT']
    
    # Percent change in employment
    df['PCHEMPC'] = 2 * (df['EMPTOT2'] - df['EMPTOT']) / (df['EMPTOT2'] + df['EMPTOT'])
    df.loc[df['EMPTOT2'] == 0, 'PCHEMPC'] = -1
    
    # Wage changes
    df['dwage'] = df['WAGE_ST2'] - df['WAGE_ST']
    df['PCHWAGE'] = (df['WAGE_ST2'] - df['WAGE_ST']) / df['WAGE_ST']
    
    # Gap calculation
    df['gap'] = 0.0
    mask_state = df['STATEr'] != 0
    mask_wage_high = df['WAGE_ST'] >= 5.05
    mask_wage_pos = df['WAGE_ST'] > 0
    
    df.loc[mask_state & ~mask_wage_high & mask_wage_pos, 'gap'] = (5.05 - df['WAGE_ST']) / df['WAGE_ST']
    df.loc[~mask_wage_pos, 'gap'] = np.nan
    
    # Create indicator variables
    df['nj'] = df['STATEr']
    df['bk'] = (df['CHAINr'] == 1).astype(int)
    df['kfc'] = (df['CHAINr'] == 2).astype(int)
    df['roys'] = (df['CHAINr'] == 3).astype(int)
    df['wendys'] = (df['CHAINr'] == 4).astype(int)
    
    # Meal prices
    df['PMEAL'] = df['PSODA'] + df['PFRY'] + df['PENTREE']
    df['PMEAL2'] = df['PSODA2'] + df['PFRY2'] + df['PENTREE2']
    df['DPMEAL'] = df['PMEAL2'] - df['PMEAL']
    
    # Store status
    df['CLOSED'] = (df['STATUS2'] == 3).astype(int)
    
    # Fraction full-time
    df['FRACFT'] = df['EMPFT'] / df['EMPTOT']
    df['FRACFT2'] = np.where(df['EMPTOT2'] > 0, df['EMPFT2'] / df['EMPTOT2'], np.nan)
    
    # Wage indicators
    df['ATMIN'] = (df['WAGE_ST'] == 4.25).astype(int)
    df['NEWMIN'] = (df['WAGE_ST2'] == 5.05).astype(int)
    
    # Create ICODE
    conditions = [
        df['nj'] == 0,
        (df['nj'] == 1) & (df['WAGE_ST'] == 4.25),
        (df['nj'] == 1) & (df['WAGE_ST'] >= 5.00),
        (df['nj'] == 1) & (df['WAGE_ST'] > 4.25) & (df['WAGE_ST'] < 5.00)
    ]
    choices = [
        'PA STORE          ',
        'NJ STORE, LOW-WAGE',
        'NJ STORE, HI-WAGE',
        'NJ STORE, MED-WAGE'
    ]
    df['ICODE'] = np.select(conditions, choices, default='NJ STORE, BAD WAGE')
    
    return df

def frequency_tables(df):
    """
    Generate frequency tables (equivalent to PROC FREQ)
    """
    print("=" * 80)
    print("FREQUENCY TABLES")
    print("=" * 80)
    
    freq_vars = ['CHAINr', 'STATEr', 'TYPE2', 'STATUS2', 'BONUS', 'SPECIAL2', 'CO_OWNED', 'MEAL', 'MEALS2']
    
    for var in freq_vars:
        if var in df.columns:
            print(f"\nFrequency table for {var}:")
            print(df[var].value_counts().sort_index())

def descriptive_statistics(df):
    """
    Generate descriptive statistics (equivalent to PROC MEANS)
    """
    print("\n" + "=" * 80)
    print("DESCRIPTIVE STATISTICS")
    print("=" * 80)
    
    # First set of variables
    vars1 = ['EMPFT', 'EMPPT', 'NMGRS', 'EMPFT2', 'EMPPT2', 'NMGRS2', 'WAGE_ST', 'WAGE_ST2',
             'PCTAFF', 'OPEN', 'OPEN2R', 'HRSOPEN', 'HRSOPEN2',
             'PSODA', 'PFRY', 'PENTREE', 'PSODA2', 'PFRY2', 'PENTREE2',
             'NREGS', 'NREGS11', 'NREGS2', 'NREGS112',
             'SOUTHJ', 'CENTRALJ', 'NORTHJ', 'PA1', 'PA2']
    
    print("\nBasic employment and operational variables:")
    available_vars1 = [var for var in vars1 if var in df.columns]
    if available_vars1:
        print(df[available_vars1].describe())
    
    # Second set of variables
    vars2 = ['EMPTOT', 'EMPTOT2', 'DEMP', 'PCHEMPC', 'gap', 'PMEAL', 'PMEAL2', 'DPMEAL']
    print(f"\nDerived employment and change variables:")
    available_vars2 = [var for var in vars2 if var in df.columns]
    if available_vars2:
        print(df[available_vars2].describe())
    
    # Third set of variables
    vars3 = ['bk', 'kfc', 'roys', 'wendys', 'CO_OWNED',
             'EMPTOT', 'FRACFT', 'WAGE_ST', 'ATMIN', 'NEWMIN', 'PMEAL', 'HRSOPEN', 'BONUS',
             'EMPTOT2', 'FRACFT2', 'WAGE_ST2', 'PMEAL2', 'HRSOPEN2', 'SPECIAL2']
    
    print(f"\nChain indicators and comprehensive variables:")
    available_vars3 = [var for var in vars3 if var in df.columns]
    if available_vars3:
        print(df[available_vars3].describe())

def statistics_by_group(df):
    """
    Generate statistics by NJ and ICODE groups
    """
    print("\n" + "=" * 80)
    print("TABLE 2 - STATISTICS BY NJ")
    print("=" * 80)
    
    vars_table2 = ['bk', 'kfc', 'roys', 'wendys', 'CO_OWNED',
                   'EMPTOT', 'FRACFT', 'WAGE_ST', 'ATMIN', 'NEWMIN', 'PMEAL', 'HRSOPEN', 'BONUS',
                   'EMPTOT2', 'FRACFT2', 'WAGE_ST2', 'PMEAL2', 'HRSOPEN2', 'SPECIAL2']
    
    available_vars_table2 = [var for var in vars_table2 if var in df.columns]
    if available_vars_table2:
        grouped_stats = df.groupby('nj')[available_vars_table2].describe()
        print(grouped_stats)
    
    print("\n" + "=" * 80)
    print("PART OF TABLE 3 - EMPLOYMENT CHANGES BY NJ")
    print("=" * 80)
    
    change_vars = ['EMPTOT', 'EMPTOT2', 'DEMP', 'PCHEMPC', 'gap', 'PMEAL', 'PMEAL2', 'DPMEAL']
    available_change_vars = [var for var in change_vars if var in df.columns]
    if available_change_vars:
        nj_stats = df.groupby('nj')[available_change_vars].describe()
        print(nj_stats)
    
    print("\n" + "=" * 80)
    print("PART OF TABLE 3 - EMPLOYMENT CHANGES BY ICODE")
    print("=" * 80)
    
    if available_change_vars:
        icode_stats = df.groupby('ICODE')[available_change_vars].describe()
        print(icode_stats)

def closed_stores_analysis(df):
    """
    Analysis of closed stores
    """
    print("\n" + "=" * 80)
    print("LISTING OF STORES THAT CLOSED")
    print("=" * 80)
    
    closed = df[df['CLOSED'] == 1]
    if not closed.empty:
        print(closed[['SHEET', 'EMPTOT', 'EMPTOT2', 'STATUS2']])
    else:
        print("No closed stores found")

def regression_analysis(df):
    """
    Perform regression analysis (equivalent to PROC REG)
    """
    print("\n" + "=" * 80)
    print("TABLE 4 - REGRESSION ANALYSIS")
    print("=" * 80)
    
    # Create subset for regression analysis
    c1 = df.copy()
    c1 = c1.dropna(subset=['DEMP'])
    c1 = c1[(c1['CLOSED'] == 1) | ((c1['CLOSED'] == 0) & c1['dwage'].notna())]
    
    print(f"Subset of stores with valid wages 2 waves (or closed W-2): {len(c1)} observations")
    
    if len(c1) == 0:
        print("No valid observations for regression analysis")
        return
    
    # Model 1: DEMP = GAP
    try:
        model1 = smf.ols('DEMP ~ gap', data=c1).fit()
        print("\nModel 1: DEMP = GAP")
        print(model1.summary())
    except Exception as e:
        print(f"Error in Model 1: {e}")
    
    # Model 2: DEMP = GAP + BK + KFC + ROYS + CO_OWNED
    try:
        model2 = smf.ols('DEMP ~ gap + bk + kfc + roys + CO_OWNED', data=c1).fit()
        print("\nModel 2: DEMP = GAP + BK + KFC + ROYS + CO_OWNED")
        print(model2.summary())
    except Exception as e:
        print(f"Error in Model 2: {e}")
    
    # Model 3: DEMP = GAP + BK + KFC + ROYS + CENTRALJ + SOUTHJ + PA1 + PA2
    try:
        model3 = smf.ols('DEMP ~ gap + bk + kfc + roys + CENTRALJ + SOUTHJ + PA1 + PA2', data=c1).fit()
        print("\nModel 3: DEMP = GAP + BK + KFC + ROYS + CENTRALJ + SOUTHJ + PA1 + PA2")
        print(model3.summary())
    except Exception as e:
        print(f"Error in Model 3: {e}")
    
    # Model 4: DEMP = NJ
    try:
        model4 = smf.ols('DEMP ~ nj', data=c1).fit()
        print("\nModel 4: DEMP = NJ")
        print(model4.summary())
    except Exception as e:
        print(f"Error in Model 4: {e}")
    
    # Model 5: DEMP = NJ + BK + KFC + ROYS + CO_OWNED
    try:
        model5 = smf.ols('DEMP ~ nj + bk + kfc + roys + CO_OWNED', data=c1).fit()
        print("\nModel 5: DEMP = NJ + BK + KFC + ROYS + CO_OWNED")
        print(model5.summary())
    except Exception as e:
        print(f"Error in Model 5: {e}")
    
    # Additional models using percent change in employment
    print("\n" + "=" * 80)
    print("MODELS NOT SHOWN IN TABLE 4 USING PERCENT CHG EMP")
    print("=" * 80)
    
    # Model 6: PCHEMPC = GAP
    try:
        model6 = smf.ols('PCHEMPC ~ gap', data=c1).fit()
        print("\nModel 6: PCHEMPC = GAP")
        print(model6.summary())
    except Exception as e:
        print(f"Error in Model 6: {e}")
    
    # Model 7: PCHEMPC = GAP + BK + KFC + ROYS + CO_OWNED
    try:
        model7 = smf.ols('PCHEMPC ~ gap + bk + kfc + roys + CO_OWNED', data=c1).fit()
        print("\nModel 7: PCHEMPC = GAP + BK + KFC + ROYS + CO_OWNED")
        print(model7.summary())
    except Exception as e:
        print(f"Error in Model 7: {e}")
    
    # Model 8: PCHEMPC = GAP + BK + KFC + ROYS + CO_OWNED + CENTRALJ + SOUTHJ + PA1 + PA2
    try:
        model8 = smf.ols('PCHEMPC ~ gap + bk + kfc + roys + CO_OWNED + CENTRALJ + SOUTHJ + PA1 + PA2', data=c1).fit()
        print("\nModel 8: PCHEMPC = GAP + BK + KFC + ROYS + CO_OWNED + CENTRALJ + SOUTHJ + PA1 + PA2")
        print(model8.summary())
    except Exception as e:
        print(f"Error in Model 8: {e}")
    
    # Model 9: PCHEMPC = NJ
    try:
        model9 = smf.ols('PCHEMPC ~ nj', data=c1).fit()
        print("\nModel 9: PCHEMPC = NJ")
        print(model9.summary())
    except Exception as e:
        print(f"Error in Model 9: {e}")
    
    # Model 10: PCHEMPC = NJ + BK + KFC + ROYS + CO_OWNED
    try:
        model10 = smf.ols('PCHEMPC ~ nj + bk + kfc + roys + CO_OWNED', data=c1).fit()
        print("\nModel 10: PCHEMPC = NJ + BK + KFC + ROYS + CO_OWNED")
        print(model10.summary())
    except Exception as e:
        print(f"Error in Model 10: {e}")

def main():
    """
    Main function to run the complete analysis
    """
    print("INPUT FLAT DATA FILE OF NJ-PA DATA AND CHECK")
    print("=" * 80)
    
    # Look for data file
    data_file = None
    possible_files = ['public.dat', 'FLAT', 'data.txt', 'njpa_data.txt', 'flat_data.txt']
    
    for filename in possible_files:
        if Path(filename).exists():
            data_file = filename
            break
    
    if data_file is None:
        print("Data file not found. Please ensure the flat data file is available.")
        print("Expected filenames: public.dat, FLAT, data.txt, njpa_data.txt, or flat_data.txt")
        return
    
    # Read and process data
    df = read_data(data_file)
    if df is None:
        return
    
    print(f"Data loaded successfully from {data_file}")
    print(f"Number of observations: {len(df)}")
    
    # Calculate derived variables
    df = calculate_derived_variables(df)
    
    # Perform all analyses
    frequency_tables(df)
    descriptive_statistics(df)
    statistics_by_group(df)
    closed_stores_analysis(df)
    regression_analysis(df)
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main() 