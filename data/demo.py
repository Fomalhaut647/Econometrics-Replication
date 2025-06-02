#!/usr/bin/env python3
"""
Demo script showing key results from the NJ-PA minimum wage analysis
"""

import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from check import read_data, calculate_derived_variables

def main():
    print("=" * 60)
    print("NJ-PA MINIMUM WAGE STUDY - KEY RESULTS")
    print("=" * 60)
    
    # Load and process data
    df = read_data('public.dat')
    if df is None:
        print("Error: Could not load data file")
        return
    
    df = calculate_derived_variables(df)
    
    print(f"Total observations: {len(df)}")
    print(f"NJ stores: {df['nj'].sum()}")
    print(f"PA stores: {len(df) - df['nj'].sum()}")
    
    # Summary statistics by state
    print("\n" + "=" * 60)
    print("EMPLOYMENT CHANGES BY STATE")
    print("=" * 60)
    
    # Create subset for analysis (stores with valid employment data)
    analysis_df = df.copy()
    analysis_df = analysis_df.dropna(subset=['DEMP'])
    analysis_df = analysis_df[(analysis_df['CLOSED'] == 1) | 
                             ((analysis_df['CLOSED'] == 0) & analysis_df['dwage'].notna())]
    
    print(f"Analysis sample: {len(analysis_df)} stores")
    
    # Summary by state
    summary = analysis_df.groupby('nj')[['EMPTOT', 'EMPTOT2', 'DEMP', 'WAGE_ST', 'WAGE_ST2']].agg({
        'EMPTOT': ['count', 'mean'],
        'EMPTOT2': 'mean', 
        'DEMP': 'mean',
        'WAGE_ST': 'mean',
        'WAGE_ST2': 'mean'
    }).round(2)
    
    print("\nBy State (0=PA, 1=NJ):")
    print(summary)
    
    # Key regression results
    print("\n" + "=" * 60)
    print("KEY REGRESSION RESULTS")
    print("=" * 60)
    
    # Main difference-in-differences result
    try:
        model = smf.ols('DEMP ~ nj', data=analysis_df).fit()
        coeff = model.params['nj']
        pvalue = model.pvalues['nj']
        se = model.bse['nj']
        
        print(f"\nMain Result - Employment Change (NJ vs PA):")
        print(f"Coefficient: {coeff:.3f}")
        print(f"Standard Error: {se:.3f}")
        print(f"P-value: {pvalue:.3f}")
        print(f"95% Confidence Interval: [{coeff - 1.96*se:.3f}, {coeff + 1.96*se:.3f}]")
        
        if pvalue < 0.05:
            print("Result: Statistically significant at 5% level")
        else:
            print("Result: Not statistically significant at 5% level")
            
    except Exception as e:
        print(f"Error in regression: {e}")
    
    # Store closure analysis
    print("\n" + "=" * 60)
    print("STORE CLOSURES")
    print("=" * 60)
    
    closed_stores = df[df['CLOSED'] == 1]
    if not closed_stores.empty:
        print(f"Total stores that closed: {len(closed_stores)}")
        closure_by_state = closed_stores.groupby('nj').size()
        print("Closures by state:")
        for state, count in closure_by_state.items():
            state_name = "NJ" if state == 1 else "PA"
            print(f"  {state_name}: {count}")
    else:
        print("No store closures found in the data")
    
    # Chain distribution
    print("\n" + "=" * 60)
    print("SAMPLE COMPOSITION")
    print("=" * 60)
    
    chain_names = {1: 'Burger King', 2: 'KFC', 3: "Roy Rogers", 4: "Wendy's"}
    chain_counts = df['CHAINr'].value_counts().sort_index()
    
    print("Stores by chain:")
    for chain_id, count in chain_counts.items():
        if chain_id in chain_names:
            print(f"  {chain_names[chain_id]}: {count}")
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("Run 'python check.py' for the full detailed analysis")
    print("=" * 60)

if __name__ == "__main__":
    main() 