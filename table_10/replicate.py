#!/usr/bin/env python3
"""
Analysis of Price Changes (PSODA, PFRY, PENTREE) Before and After Minimum Wage Increase
"""

import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path

# 添加根目录到Python路径以导入utility模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utility as util


def calculate_price_changes(df):
    """
    计算价格变量(PSODA, PFRY, PENTREE)及其总和(PTOTAL)的变化
    """
    # 创建价格总和变量
    df['PTOTAL'] = df['PSODA'] + df['PFRY'] + df['PENTREE']
    df['PTOTAL2'] = df['PSODA2'] + df['PFRY2'] + df['PENTREE2']

    # 识别平衡样本（两期都有价格数据的商店）
    price_vars = ['PSODA', 'PFRY', 'PENTREE', 'PTOTAL']
    balanced_mask = df[price_vars].notna().all(axis=1) & df[[f"{v}2" for v in price_vars]].notna().all(axis=1)
    df['balanced_sample'] = balanced_mask

    return df


def calculate_price_stats(df, group_filter, price_var, wave):
    """
    计算指定价格变量的统计量（均值和标准误）
    """
    group_data = df[group_filter]

    if wave == 1:
        var_name = price_var
    else:
        var_name = f"{price_var}2"

    mean_val, se_val, n = util.calculate_mean_and_se(group_data[var_name])
    return {'mean': mean_val, 'se': se_val, 'n': n}


def calculate_price_changes_stats(df, group_filter, price_var, method='all'):
    """
    计算价格变化统计量
    method: 'all' - 使用所有可用数据（独立样本）
            'balanced' - 使用平衡样本（配对样本）
    """
    group_data = df[group_filter]

    if method == 'all':
        # 使用所有可用数据（独立样本方法）
        stats_w1 = calculate_price_stats(df, group_filter, price_var, 1)
        stats_w2 = calculate_price_stats(df, group_filter, price_var, 2)

        if pd.isna(stats_w1['mean']) or pd.isna(stats_w2['mean']):
            return {'mean': np.nan, 'se': np.nan, 'n': 0}

        mean_change = stats_w2['mean'] - stats_w1['mean']
        se_change = np.sqrt(stats_w1['se'] ** 2 + stats_w2['se'] ** 2)
        n_change = min(stats_w1['n'], stats_w2['n'])

        return {'mean': mean_change, 'se': se_change, 'n': n_change}

    else:  # balanced sample
        balanced_data = group_data[group_data['balanced_sample']]
        if len(balanced_data) == 0:
            return {'mean': np.nan, 'se': np.nan, 'n': 0}

        # 计算每个商店的价格变化
        balanced_data = balanced_data.copy()
        balanced_data['change'] = balanced_data[f"{price_var}2"] - balanced_data[price_var]

        mean_val, se_val, n = util.calculate_mean_and_se(balanced_data['change'])
        return {'mean': mean_val, 'se': se_val, 'n': n}


def calculate_difference(stat1, stat2):
    """
    计算两组之间的差异（如NJ - PA）及其标准误
    """
    if pd.isna(stat1['mean']) or pd.isna(stat2['mean']):
        return {'mean': np.nan, 'se': np.nan}

    mean_diff = stat1['mean'] - stat2['mean']
    se_diff = np.sqrt(stat1['se'] ** 2 + stat2['se'] ** 2)
    return {'mean': mean_diff, 'se': se_diff}


def generate_price_table(df):
    """
    生成价格变化分析表格
    """
    results = {}

    # 定义组别
    groups = {
        'PA': df['nj'] == 0,
        'NJ': df['nj'] == 1
    }

    # 价格变量列表
    price_vars = ['PSODA', 'PFRY', 'PENTREE', 'PTOTAL']

    # 为每个价格变量计算统计量
    for price_var in price_vars:
        var_results = {}

        # Wave 1 统计量
        var_results['wave1'] = {
            'PA': calculate_price_stats(df, groups['PA'], price_var, 1),
            'NJ': calculate_price_stats(df, groups['NJ'], price_var, 1)
        }
        var_results['wave1']['diff'] = calculate_difference(
            var_results['wave1']['NJ'], var_results['wave1']['PA'])

        # Wave 2 统计量
        var_results['wave2'] = {
            'PA': calculate_price_stats(df, groups['PA'], price_var, 2),
            'NJ': calculate_price_stats(df, groups['NJ'], price_var, 2)
        }
        var_results['wave2']['diff'] = calculate_difference(
            var_results['wave2']['NJ'], var_results['wave2']['PA'])

        # 变化量（所有可用数据）
        var_results['change_all'] = {
            'PA': calculate_price_changes_stats(df, groups['PA'], price_var, 'all'),
            'NJ': calculate_price_changes_stats(df, groups['NJ'], price_var, 'all')
        }
        var_results['change_all']['diff'] = calculate_difference(
            var_results['change_all']['NJ'], var_results['change_all']['PA'])

        # 变化量（平衡样本）
        var_results['change_balanced'] = {
            'PA': calculate_price_changes_stats(df, groups['PA'], price_var, 'balanced'),
            'NJ': calculate_price_changes_stats(df, groups['NJ'], price_var, 'balanced')
        }
        var_results['change_balanced']['diff'] = calculate_difference(
            var_results['change_balanced']['NJ'], var_results['change_balanced']['PA'])

        results[price_var] = var_results

    return results


def format_cell(mean_val, se_val):
    """
    格式化表格单元格，显示均值和括号中的标准误
    """
    if pd.isna(mean_val) or pd.isna(se_val):
        return "."
    return f"{mean_val:.3f} ({se_val:.3f})"


def write_price_output(results):
    """
    写入价格分析结果到output_price.md文件
    """
    output_path = Path(util.get_output_path(__file__)).parent / "output_price.md"

    with open(output_path, 'w') as f:
        f.write("**PRICE CHANGES BEFORE AND AFTER THE RISE IN NEW JERSEY MINIMUM WAGE**\n\n")
        f.write("| Variable | Period | PA (i) | NJ (ii) | Difference, NJ-PA (iii) |\n")
        f.write("| :------- | :----- | :----- | :------ | :---------------------- |\n")

        # 价格变量列表
        price_vars = ['PSODA', 'PFRY', 'PENTREE', 'PTOTAL']
        period_labels = {
            'wave1': "Before",
            'wave2': "After",
            'change_all': "Change (all stores)",
            'change_balanced': "Change (balanced sample)"
        }

        for price_var in price_vars:
            # 添加变量名称行
            f.write(f"| **{price_var}** | | | | |\n")

            # 添加各个时期的数据
            for period_key, period_label in period_labels.items():
                period_data = results[price_var][period_key]

                f.write(f"| | {period_label} | ")
                f.write(f"{format_cell(period_data['PA']['mean'], period_data['PA']['se'])} | ")
                f.write(f"{format_cell(period_data['NJ']['mean'], period_data['NJ']['se'])} | ")
                f.write(f"{format_cell(period_data['diff']['mean'], period_data['diff']['se'])} |\n")

        # 添加注释
        f.write("\n**Notes:**\n")
        f.write("- Standard errors are shown in parentheses\n")
        f.write("- 'Before' refers to Wave 1 data collection (February 1992)\n")
        f.write("- 'After' refers to Wave 2 data collection (November 1992)\n")
        f.write(
            "- 'Change (all stores)' calculates the difference using all available data (independent samples method)\n")
        f.write(
            "- 'Change (balanced sample)' calculates the difference using only stores with complete data in both waves\n")
        f.write(
            f"- Sample sizes: PA (n={results['PSODA']['wave1']['PA']['n']}), NJ (n={results['PSODA']['wave1']['NJ']['n']})\n")
        f.write("- PTOTAL = PSODA + PFRY + PENTREE\n")

    print(f"Output saved to: {output_path}")


def main():
    """
    主函数运行价格分析
    """
    print("Starting price analysis...")

    # 读取数据
    print("Reading data...")
    df = util.read_data(method='fixed_width')
    print(f"Loaded {len(df)} observations")

    # 使用utility模块创建基本衍生变量
    print("Creating derived variables...")
    df = util.create_basic_derived_variables(df)

    # 计算价格变化
    print("Calculating price changes...")
    df = calculate_price_changes(df)

    # 生成表格结果
    print("Generating table results...")
    results = generate_price_table(df)

    # 写入输出
    print("Writing output...")
    write_price_output(results)

    print("Price analysis completed successfully!")


if __name__ == "__main__":
    main()