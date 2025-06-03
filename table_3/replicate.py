#!/usr/bin/env python3
"""
Replication script for Table 3 from Card and Krueger (1994)
"Minimum Wages and Employment: A Case Study of the Fast-Food Industry in New Jersey and Pennsylvania"

This script reproduces Table 3: Average Employment per Store Before and After the Rise in New Jersey Minimum Wage
"""

import sys
import os

# 添加根目录到Python路径以导入utility模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utility as util
import pandas as pd
import numpy as np
from pathlib import Path

def calculate_fte_variants(df):
    """
    计算FTE就业的变体，处理临时关闭的商店
    """
    df = df.copy()
    
    # 基础FTE已经通过utility模块计算
    # 处理临时关闭商店的不同策略
    
    # 策略1: 临时关闭店铺设为缺失 (rows 1-4)
    df['FTE2_row1234'] = df['EMPTOT2'].copy()
    df.loc[df['STATUS2'] == 2, 'FTE2_row1234'] = np.nan
    
    # 策略2: 临时关闭店铺设为0 (row 5)
    df['FTE2_row5'] = df['EMPTOT2'].copy()
    df.loc[df['STATUS2'] == 2, 'FTE2_row5'] = 0
    
    return df

def calculate_difference_se(mean1, se1, mean2, se2):
    """
    计算两个独立均值差的标准误
    SE_diff = sqrt(SE1^2 + SE2^2)
    """
    if pd.isna(se1) or pd.isna(se2):
        return np.nan
    return np.sqrt(se1**2 + se2**2)

def calculate_balanced_sample(df):
    """
    识别平衡样本：两波都有有效就业数据的商店
    """
    df = df.copy()
    
    # 两波都有有效数据（排除临时关闭的情况）
    valid_wave1 = df['EMPTOT'].notna()
    valid_wave2_row1234 = df['FTE2_row1234'].notna()
    valid_wave2_row5 = df['FTE2_row5'].notna()
    
    df['balanced_sample_row1234'] = valid_wave1 & valid_wave2_row1234
    df['balanced_sample_row5'] = valid_wave1 & valid_wave2_row5
    
    return df

def generate_table3(df):
    """
    生成Table 3结果
    """
    results = {}
    
    # 定义组别过滤器
    groups = {
        'PA': df['nj'] == 0,
        'NJ': df['nj'] == 1,
        'NJ_wage_425': df['NJ_wage_425'] == 1,
        'NJ_wage_426_499': df['NJ_wage_426_499'] == 1,
        'NJ_wage_500plus': df['NJ_wage_500plus'] == 1
    }
    
    # Row 1: FTE employment before, all available observations
    row1 = {}
    for group_name, group_filter in groups.items():
        group_data = df[group_filter]
        mean_val, se_val, n = util.calculate_mean_and_se(group_data['EMPTOT'])
        row1[group_name] = {'mean': mean_val, 'se': se_val, 'n': n}
    
    # Row 2: FTE employment after, all available observations
    row2 = {}
    for group_name, group_filter in groups.items():
        group_data = df[group_filter]
        mean_val, se_val, n = util.calculate_mean_and_se(group_data['FTE2_row1234'])
        row2[group_name] = {'mean': mean_val, 'se': se_val, 'n': n}
    
    # Row 3: Change in mean FTE employment
    row3 = {}
    for group_name in groups.keys():
        mean_diff = row2[group_name]['mean'] - row1[group_name]['mean']
        se_diff = calculate_difference_se(row1[group_name]['se'], row2[group_name]['se'], 
                                         row1[group_name]['se'], row2[group_name]['se'])
        row3[group_name] = {'mean': mean_diff, 'se': se_diff}
    
    # Row 4: Change in mean FTE employment, balanced sample
    row4 = {}
    for group_name, group_filter in groups.items():
        balanced_data = df[group_filter & df['balanced_sample_row1234']]
        if len(balanced_data) > 0:
            change = balanced_data['FTE2_row1234'] - balanced_data['EMPTOT']
            mean_val, se_val, n = util.calculate_mean_and_se(change)
        else:
            mean_val, se_val, n = np.nan, np.nan, 0
        row4[group_name] = {'mean': mean_val, 'se': se_val, 'n': n}
    
    # Row 5: Change in mean FTE employment, setting FTE at temporarily closed stores to 0
    row5 = {}
    for group_name, group_filter in groups.items():
        balanced_data = df[group_filter & df['balanced_sample_row5']]
        if len(balanced_data) > 0:
            change = balanced_data['FTE2_row5'] - balanced_data['EMPTOT']
            mean_val, se_val, n = util.calculate_mean_and_se(change)
        else:
            mean_val, se_val, n = np.nan, np.nan, 0
        row5[group_name] = {'mean': mean_val, 'se': se_val, 'n': n}
    
    # 计算差异
    def calc_group_differences(row_data):
        # NJ - PA difference
        nj_pa_diff = row_data['NJ']['mean'] - row_data['PA']['mean']
        nj_pa_se = calculate_difference_se(row_data['NJ']['se'], row_data['PA']['se'],
                                          row_data['NJ']['se'], row_data['PA']['se'])
        
        # Low wage - High wage difference (NJ)
        low_high_diff = row_data['NJ_wage_425']['mean'] - row_data['NJ_wage_500plus']['mean']
        low_high_se = calculate_difference_se(row_data['NJ_wage_425']['se'], row_data['NJ_wage_500plus']['se'],
                                             row_data['NJ_wage_425']['se'], row_data['NJ_wage_500plus']['se'])
        
        # Mid wage - High wage difference (NJ)
        mid_high_diff = row_data['NJ_wage_426_499']['mean'] - row_data['NJ_wage_500plus']['mean']
        mid_high_se = calculate_difference_se(row_data['NJ_wage_426_499']['se'], row_data['NJ_wage_500plus']['se'],
                                             row_data['NJ_wage_426_499']['se'], row_data['NJ_wage_500plus']['se'])
        
        return {
            'nj_pa_diff': {'mean': nj_pa_diff, 'se': nj_pa_se},
            'low_high_diff': {'mean': low_high_diff, 'se': low_high_se},
            'mid_high_diff': {'mean': mid_high_diff, 'se': mid_high_se}
        }
    
    results = {
        'row1': row1,
        'row2': row2, 
        'row3': row3,
        'row4': row4,
        'row5': row5,
        'row1_diffs': calc_group_differences(row1),
        'row2_diffs': calc_group_differences(row2),
        'row3_diffs': calc_group_differences(row3),
        'row4_diffs': calc_group_differences(row4),
        'row5_diffs': calc_group_differences(row5)
    }
    
    return results

def format_cell(mean_val, se_val):
    """
    格式化表格单元格，显示均值和括号中的标准误
    """
    if pd.isna(mean_val) or pd.isna(se_val):
        return "."
    return f"{mean_val:.2f} ({se_val:.2f})"

def write_output(results):
    """
    写入结果到output.md文件
    """
    output_path = util.get_output_path(__file__)
    
    with open(output_path, 'w') as f:
        f.write("**TABLE 3-AVERAGE EMPLOYMENT PER STORE BEFORE AND AFTER THE RISE IN NEW JERSEY MINIMUM WAGE**\n\n")
        
        # 表格头部
        f.write("| Variable | PA (i) | NJ (ii) | Difference, NJ-PA (iii) | NJ Wage = $4.25 (iv) | NJ Wage = $4.26-$4.99 (v) | NJ Wage >= $5.00 (vi) | Diff Low-high (vii)<sup>b</sup> | Diff Midrange-high (viii)<sup>b</sup> |\n")
        f.write("| :----------------------------------------------------------------------- | :----------- | :----------- | :---------------------- | :------------------- | :------------------------ | :-------------------- | :-------------------------- | :---------------------------- |\n")
        
        # Row 1
        f.write("| 1. FTE employment before, all available observations<sup>a</sup> | ")
        f.write(f"{format_cell(results['row1']['PA']['mean'], results['row1']['PA']['se'])} | ")
        f.write(f"{format_cell(results['row1']['NJ']['mean'], results['row1']['NJ']['se'])} | ")
        f.write(f"{format_cell(results['row1_diffs']['nj_pa_diff']['mean'], results['row1_diffs']['nj_pa_diff']['se'])} | ")
        f.write(f"{format_cell(results['row1']['NJ_wage_425']['mean'], results['row1']['NJ_wage_425']['se'])} | ")
        f.write(f"{format_cell(results['row1']['NJ_wage_426_499']['mean'], results['row1']['NJ_wage_426_499']['se'])} | ")
        f.write(f"{format_cell(results['row1']['NJ_wage_500plus']['mean'], results['row1']['NJ_wage_500plus']['se'])} | ")
        f.write(f"{format_cell(results['row1_diffs']['low_high_diff']['mean'], results['row1_diffs']['low_high_diff']['se'])} | ")
        f.write(f"{format_cell(results['row1_diffs']['mid_high_diff']['mean'], results['row1_diffs']['mid_high_diff']['se'])} |\n")
        
        # Row 2
        f.write("| 2. FTE employment after, all available observations<sup>a</sup> | ")
        f.write(f"{format_cell(results['row2']['PA']['mean'], results['row2']['PA']['se'])} | ")
        f.write(f"{format_cell(results['row2']['NJ']['mean'], results['row2']['NJ']['se'])} | ")
        f.write(f"{format_cell(results['row2_diffs']['nj_pa_diff']['mean'], results['row2_diffs']['nj_pa_diff']['se'])} | ")
        f.write(f"{format_cell(results['row2']['NJ_wage_425']['mean'], results['row2']['NJ_wage_425']['se'])} | ")
        f.write(f"{format_cell(results['row2']['NJ_wage_426_499']['mean'], results['row2']['NJ_wage_426_499']['se'])} | ")
        f.write(f"{format_cell(results['row2']['NJ_wage_500plus']['mean'], results['row2']['NJ_wage_500plus']['se'])} | ")
        f.write(f"{format_cell(results['row2_diffs']['low_high_diff']['mean'], results['row2_diffs']['low_high_diff']['se'])} | ")
        f.write(f"{format_cell(results['row2_diffs']['mid_high_diff']['mean'], results['row2_diffs']['mid_high_diff']['se'])} |\n")
        
        # Row 3
        f.write("| 3. Change in mean FTE employment | ")
        f.write(f"{format_cell(results['row3']['PA']['mean'], results['row3']['PA']['se'])} | ")
        f.write(f"{format_cell(results['row3']['NJ']['mean'], results['row3']['NJ']['se'])} | ")
        f.write(f"{format_cell(results['row3_diffs']['nj_pa_diff']['mean'], results['row3_diffs']['nj_pa_diff']['se'])} | ")
        f.write(f"{format_cell(results['row3']['NJ_wage_425']['mean'], results['row3']['NJ_wage_425']['se'])} | ")
        f.write(f"{format_cell(results['row3']['NJ_wage_426_499']['mean'], results['row3']['NJ_wage_426_499']['se'])} | ")
        f.write(f"{format_cell(results['row3']['NJ_wage_500plus']['mean'], results['row3']['NJ_wage_500plus']['se'])} | ")
        f.write(f"{format_cell(results['row3_diffs']['low_high_diff']['mean'], results['row3_diffs']['low_high_diff']['se'])} | ")
        f.write(f"{format_cell(results['row3_diffs']['mid_high_diff']['mean'], results['row3_diffs']['mid_high_diff']['se'])} |\n")
        
        # Row 4
        f.write("| 4. Change in mean FTE employment, balanced sample of stores<sup>c</sup> | ")
        f.write(f"{format_cell(results['row4']['PA']['mean'], results['row4']['PA']['se'])} | ")
        f.write(f"{format_cell(results['row4']['NJ']['mean'], results['row4']['NJ']['se'])} | ")
        f.write(f"{format_cell(results['row4_diffs']['nj_pa_diff']['mean'], results['row4_diffs']['nj_pa_diff']['se'])} | ")
        f.write(f"{format_cell(results['row4']['NJ_wage_425']['mean'], results['row4']['NJ_wage_425']['se'])} | ")
        f.write(f"{format_cell(results['row4']['NJ_wage_426_499']['mean'], results['row4']['NJ_wage_426_499']['se'])} | ")
        f.write(f"{format_cell(results['row4']['NJ_wage_500plus']['mean'], results['row4']['NJ_wage_500plus']['se'])} | ")
        f.write(f"{format_cell(results['row4_diffs']['low_high_diff']['mean'], results['row4_diffs']['low_high_diff']['se'])} | ")
        f.write(f"{format_cell(results['row4_diffs']['mid_high_diff']['mean'], results['row4_diffs']['mid_high_diff']['se'])} |\n")
        
        # Row 5
        f.write("| 5. Change in mean FTE employment, setting FTE at temporarily closed stores to 0<sup>d</sup> | ")
        f.write(f"{format_cell(results['row5']['PA']['mean'], results['row5']['PA']['se'])} | ")
        f.write(f"{format_cell(results['row5']['NJ']['mean'], results['row5']['NJ']['se'])} | ")
        f.write(f"{format_cell(results['row5_diffs']['nj_pa_diff']['mean'], results['row5_diffs']['nj_pa_diff']['se'])} | ")
        f.write(f"{format_cell(results['row5']['NJ_wage_425']['mean'], results['row5']['NJ_wage_425']['se'])} | ")
        f.write(f"{format_cell(results['row5']['NJ_wage_426_499']['mean'], results['row5']['NJ_wage_426_499']['se'])} | ")
        f.write(f"{format_cell(results['row5']['NJ_wage_500plus']['mean'], results['row5']['NJ_wage_500plus']['se'])} | ")
        f.write(f"{format_cell(results['row5_diffs']['low_high_diff']['mean'], results['row5_diffs']['low_high_diff']['se'])} | ")
        f.write(f"{format_cell(results['row5_diffs']['mid_high_diff']['mean'], results['row5_diffs']['mid_high_diff']['se'])} |\n")
        
        # 注释
        f.write("\n")
        f.write("Notes: Standard errors are shown in parentheses. The sample consists of all stores with available data on employment.\n")
        f.write("<sup>a</sup> FTE (full-time-equivalent) employment counts each part-time worker as half a full-time worker. Employment at six closed stores is set to zero. Employment at four temporarily closed stores is treated as missing.\n")
        f.write("<sup>b</sup> Stores in New Jersey were classified by whether starting wage in wave 1 equals $4.25 per hour (N=101), is between $4.26 and $4.99 per hour (N=140), or is $5.00 per hour or higher (N=73). Difference in employment between low-wage ($4.25 per hour) and high-wage (>= $5.00 per hour) stores; and difference in employment between midrange ($4.26-$4.99 per hour) and high-wage stores.\n")
        f.write("<sup>c</sup> Subset of stores with available employment data in wave 1 and wave 2.\n")
        f.write("<sup>d</sup> In this row only, wave-2 employment at four temporarily closed stores is set to 0. Employment changes are based on the subset of stores with available employment data in wave 1 and wave 2.\n")

def main():
    """
    主函数运行Table 3复制
    """
    print("Starting Table 3 replication...")
    
    # 使用utility模块读取和处理数据
    print("Reading data...")
    df = util.read_data(method='fixed_width')  # table_3使用固定宽度格式
    print(f"Loaded {len(df)} observations")
    
    # 使用utility模块创建基本衍生变量
    print("Creating derived variables...")
    df = util.create_basic_derived_variables(df)
    
    # 计算FTE变体（处理临时关闭商店）
    print("Calculating FTE variants...")
    df = calculate_fte_variants(df)
    
    # 识别平衡样本
    print("Identifying balanced sample...")
    df = calculate_balanced_sample(df)
    
    # 生成表格结果
    print("Generating table results...")
    results = generate_table3(df)
    
    # 写入输出
    print("Writing output...")
    write_output(results)
    
    print("Table 3 replication completed successfully!")
    print(f"Output saved to: {util.get_output_path(__file__)}")

if __name__ == "__main__":
    main()
