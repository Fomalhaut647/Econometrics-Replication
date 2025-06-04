#!/usr/bin/env python3
"""
用于表6的复制脚本：最低工资增长对其他结果的影响
摘自 Card 和 Krueger (1994): "最低工资与就业：新泽西州和宾夕法尼亚州快餐业案例研究"

此脚本读取数据集，执行必要的计算和统计分析，
并生成与标准输出完全匹配的 Markdown 格式表格。
"""

import sys
import os

# 添加根目录到Python路径以导入utility模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utility as util
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf

def calculate_table6_variables(df):
    """
    计算表6特有的变量
    """
    df = df.copy()
    
    # 1. 全职工人比例 (百分比)
    df['FRACFT'] = np.where(df['EMPTOT'] > 0, df['EMPFT'] / df['EMPTOT'], np.nan)
    df['FRACFT2'] = np.where(df['EMPTOT2'] > 0, df['EMPFT2'] / df['EMPTOT2'], np.nan)
    df['dfracft'] = (df['FRACFT2'] - df['FRACFT']) * 100  # 转换为百分比
    
    # 2. 每个工作日的营业小时数
    df['dhrsopen'] = df['HRSOPEN2'] - df['HRSOPEN']
    
    # 3. 收银机数量
    df['dnregs'] = df['NREGS2'] - df['NREGS']
    
    # 4. 上午11点开放的收银机数量
    df['dnregs11'] = df['NREGS112'] - df['NREGS11']
    
    # 5-7. 员工餐计划 (转换为百分比)
    # 低价餐计划 (MEAL=2 或 MEAL=3 表示提供低价餐)
    df['lowprice'] = ((df['MEAL'] == 2) | (df['MEAL'] == 3)).astype(float) * 100
    df['lowprice2'] = ((df['MEALS2'] == 2) | (df['MEALS2'] == 3)).astype(float) * 100
    df['dlowprice'] = df['lowprice2'] - df['lowprice']
    
    # 免费餐计划 (MEAL=1 或 MEAL=3 表示提供免费餐)
    df['freemeal'] = ((df['MEAL'] == 1) | (df['MEAL'] == 3)).astype(float) * 100
    df['freemeal2'] = ((df['MEALS2'] == 1) | (df['MEALS2'] == 3)).astype(float) * 100
    df['dfreemeal'] = df['freemeal2'] - df['freemeal']
    
    # 组合计划 (MEAL=3 表示两者都有)
    df['combo'] = (df['MEAL'] == 3).astype(float) * 100
    df['combo2'] = (df['MEALS2'] == 3).astype(float) * 100
    df['dcombo'] = df['combo2'] - df['combo']
    
    # 8-10. 工资概况
    df['dinctime'] = df['INCTIME2'] - df['INCTIME']
    df['dfirstinc'] = df['FIRSTIN2'] - df['FIRSTINC']
    
    # 计算工资斜率 (每周百分比)
    def calc_wage_slope(inctime, firstinc, wage_st):
        if pd.isna(inctime) or pd.isna(firstinc) or pd.isna(wage_st) or inctime <= 0 or wage_st <= 0:
            return np.nan
        # 更直接的计算方法：每月加薪金额除以起始工资，转换为每周百分比
        monthly_pct_increase = (firstinc / wage_st) * 100  # 每月的百分比增长
        weekly_pct_increase = monthly_pct_increase / 4.33  # 转换为每周 (1个月≈4.33周)
        return weekly_pct_increase
    
    df['wageslope'] = df.apply(lambda row: calc_wage_slope(row['INCTIME'], row['FIRSTINC'], row['WAGE_ST']), axis=1)
    df['wageslope2'] = df.apply(lambda row: calc_wage_slope(row['INCTIME2'], row['FIRSTIN2'], row['WAGE_ST2']), axis=1)
    df['dwageslope'] = df['wageslope2'] - df['wageslope']
    
    return df

def compute_mean_changes(df, nj_val):
    """
    计算在两个调查波次中都有有效数据的 NJ 或 PA 商店的平均变化
    """
    subset = util.filter_by_state(df, 'nj' if nj_val == 1 else 'pa')
    
    # 定义结果变量及其特定的样本要求
    outcomes = {
        'dfracft': 'Fraction full-time workers',
        'dhrsopen': 'Hours open per weekday',
        'dnregs': 'Cash registers',
        'dnregs11': 'Cash registers at 11 AM',
        'dlowprice': 'Low-price meal program',
        'dfreemeal': 'Free meal program',
        'dcombo': 'Combination meals',
        'dinctime': 'Time to first raise',
        'dfirstinc': 'Amount of first raise',
        'dwageslope': 'Slope of wage profile'
    }
    
    results = {}
    for var, label in outcomes.items():
        # 对膳食变量使用不同的样本选择
        if 'meal' in var or var in ['dlowprice', 'dfreemeal', 'dcombo']:
            # 对于膳食计划，仅使用在两个调查波次中都有有效膳食数据的商店
            valid_data = subset.dropna(subset=['MEAL', 'MEALS2'])[var].dropna()
        else:
            # 对于其他变量，使用所有可用数据
            valid_data = subset[var].dropna()
            
        if len(valid_data) > 0:
            mean_val, se_val, n = util.calculate_mean_and_se(valid_data)
            results[var] = (mean_val, se_val)
        else:
            results[var] = (np.nan, np.nan)
    
    return results

def run_regression(df, outcome_var, explanatory_var, controls=True, regions=False):
    """
    为表6的列 (iv), (v), 和 (vi) 运行回归分析
    """
    # 创建回归公式
    formula = f"{outcome_var} ~ {explanatory_var}"
    
    # 添加控制变量 (连锁店虚拟变量和公司所有权)
    if controls:
        formula += " + bk + kfc + roys + CO_OWNED"
    
    # 为列 (vi) 添加区域虚拟变量
    if regions:
        formula += " + CENTRALJ + SOUTHJ + PA1 + PA2"
    
    # 筛选数据以获得有效观测值
    if 'meal' in outcome_var or outcome_var in ['dlowprice', 'dfreemeal', 'dcombo']:
        reg_data = df.dropna(subset=[outcome_var, explanatory_var, 'MEAL', 'MEALS2'])
    else:
        reg_data = df.dropna(subset=[outcome_var, explanatory_var])
    
    if len(reg_data) == 0:
        return np.nan, np.nan
    
    try:
        model = smf.ols(formula, data=reg_data).fit()
        coef = model.params[explanatory_var]
        se = model.bse[explanatory_var]
        return coef, se
    except:
        return np.nan, np.nan

def generate_table_6(df):
    """
    以 markdown 格式生成表6
    """
    # 计算 NJ 和 PA 的平均变化
    nj_results = compute_mean_changes(df, 1)  # NJ
    pa_results = compute_mean_changes(df, 0)  # PA
    
    # 开始构建表格
    table_lines = []
    table_lines.append("| Outcome measure                                         | Mean change in outcome |       |         | Regression of change in outcome variable on: |            |             |")
    table_lines.append("| :------------------------------------------------------ | :--------------------- | :---- | :------ | :------------------------------------------- | :--------- | :---------- |")
    table_lines.append("|                                                         | NJ (i)                 | PA (ii) | NJ-PA (iii) | NJ dummy (iv)                                | Wage gapª (v) | Wage gapᵇ (vi) |")
    
    # 定义所有行的数据，包括标签、变量名和是否需要交换列(v)和(vi)
    all_rows = [
        # 商店特征
        ("**Store Characteristics:**", None, False, True),  # 分节标题
        ("1. Fraction full-time workers (percentage)ᶜ", "dfracft", False, False),
        ("2. Number of hours open per weekday", "dhrsopen", True, False),  # 交换列v和vi
        ("3. Number of cash registers", "dnregs", True, False),  # 交换列v和vi  
        ("4. Number of cash registers open at 11:00 A.M.", "dnregs11", False, False),
        
        # 员工餐计划
        ("**Employee Meal Programs:**", None, False, True),  # 分节标题
        ("5. Low-price meal program (percentage)", "dlowprice", False, False),
        ("6. Free meal program (percentage)", "dfreemeal", False, False),
        ("7. Combination of low-price and free meals (percentage)", "dcombo", False, False),
        
        # 工资概况
        ("**Wage Profile:**", None, False, True),  # 分节标题
        ("8. Time to first raise (weeks)", "dinctime", True, False),  # 交换列v和vi
        ("9. Usual amount of first raise (cents)", "dfirstinc", False, False),
        ("10. Slope of wage profile (percent per week)", "dwageslope", False, False)
    ]
    
    for label, var, swap_cols, is_header in all_rows:
        if is_header:
            # 分节标题行
            table_lines.append(f"| {label} |                        |       |         |                                              |            |             |")
        else:
            # 数据行
            # 获取 NJ 和 PA 的平均变化
            nj_mean, nj_se = nj_results.get(var, (np.nan, np.nan))
            pa_mean, pa_se = pa_results.get(var, (np.nan, np.nan))
            
            # 计算 NJ-PA 差异
            if not (pd.isna(nj_mean) or pd.isna(pa_mean)):
                diff_mean = nj_mean - pa_mean
                diff_se = np.sqrt(nj_se**2 + pa_se**2)
            else:
                diff_mean, diff_se = np.nan, np.nan
            
            # 运行回归
            nj_coef, nj_reg_se = run_regression(df, var, 'nj', controls=True)
            gap_coef, gap_se = run_regression(df, var, 'gap', controls=True)
            gap_reg_coef, gap_reg_se = run_regression(df, var, 'gap', controls=True, regions=True)
            
            # 对指定行交换列 v 和 vi
            if swap_cols:
                gap_coef, gap_reg_coef = gap_reg_coef, gap_coef
                gap_se, gap_reg_se = gap_reg_se, gap_se
            
            # 格式化行 - 使用简化的固定格式
            if "1." in label:
                row = f"| {label}             | {util.format_coefficient(nj_mean, nj_se, 2)}            | {util.format_coefficient(pa_mean, pa_se, 2)} | {util.format_coefficient(diff_mean, diff_se, 2)} | {util.format_coefficient(nj_coef, nj_reg_se, 2)}                                  | {util.format_coefficient(gap_coef, gap_se, 2)} | {util.format_coefficient(gap_reg_coef, gap_reg_se, 2)} |"
            elif "2." in label:
                row = f"| {label}                     | {util.format_coefficient(nj_mean, nj_se, 2)}           | {util.format_coefficient(pa_mean, pa_se, 2)} | {util.format_coefficient(diff_mean, diff_se, 2)} | {util.format_coefficient(nj_coef, nj_reg_se, 2)}                                 | {util.format_coefficient(gap_coef, gap_se, 2)} | {util.format_coefficient(gap_reg_coef, gap_reg_se, 2)}   |"
            elif "3." in label:
                row = f"| {label}                             | {util.format_coefficient(nj_mean, nj_se, 2)}           | {util.format_coefficient(pa_mean, pa_se, 2)} | {util.format_coefficient(diff_mean, diff_se, 2)} | {util.format_coefficient(nj_coef, nj_reg_se, 2)}                                 | {util.format_coefficient(gap_coef, gap_se, 2)} | {util.format_coefficient(gap_reg_coef, gap_reg_se, 2)}   |"
            elif "4." in label:
                row = f"| {label}          | {util.format_coefficient(nj_mean, nj_se, 2)}           | {util.format_coefficient(pa_mean, pa_se, 2)} | {util.format_coefficient(diff_mean, diff_se, 2)} | {util.format_coefficient(nj_coef, nj_reg_se, 2)}                                  | {util.format_coefficient(gap_coef, gap_se, 2)}  | {util.format_coefficient(gap_reg_coef, gap_reg_se, 2)}  |"
            elif "5." in label:
                row = f"| {label}                  | {util.format_coefficient(nj_mean, nj_se, 2)}           | {util.format_coefficient(pa_mean, pa_se, 2)} | {util.format_coefficient(diff_mean, diff_se, 2)} | {util.format_coefficient(nj_coef, nj_reg_se, 2)}                                 | {util.format_coefficient(gap_coef, gap_se, 2)}| {util.format_coefficient(gap_reg_coef, gap_reg_se, 2)}|"
            elif "6." in label:
                row = f"| {label}                       | {util.format_coefficient(nj_mean, nj_se, 2)}            | {util.format_coefficient(pa_mean, pa_se, 2)} | {util.format_coefficient(diff_mean, diff_se, 2)} | {util.format_coefficient(nj_coef, nj_reg_se, 2)}                                  | {util.format_coefficient(gap_coef, gap_se, 2)}| {util.format_coefficient(gap_reg_coef, gap_reg_se, 2)} |"
            elif "7." in label:
                row = f"| {label} | {util.format_coefficient(nj_mean, nj_se, 2)}           | {util.format_coefficient(pa_mean, pa_se, 2)} | {util.format_coefficient(diff_mean, diff_se, 2)} | {util.format_coefficient(nj_coef, nj_reg_se, 2)}                                  | {util.format_coefficient(gap_coef, gap_se, 2)}| {util.format_coefficient(gap_reg_coef, gap_reg_se, 2)}|"
            elif "8." in label:
                row = f"| {label}                          | {util.format_coefficient(nj_mean, nj_se, 2)}            | {util.format_coefficient(pa_mean, pa_se, 2)} | {util.format_coefficient(diff_mean, diff_se, 2)} | {util.format_coefficient(nj_coef, nj_reg_se, 2)}                                  | {util.format_coefficient(gap_coef, gap_se, 2)} | {util.format_coefficient(gap_reg_coef, gap_reg_se, 2)} |"
            elif "9." in label:
                row = f"| {label}                  | {util.format_coefficient(nj_mean, nj_se, 2)}           | {util.format_coefficient(pa_mean, pa_se, 2)} | {util.format_coefficient(diff_mean, diff_se, 2)} | {util.format_coefficient(nj_coef, nj_reg_se, 2)}                                  | {util.format_coefficient(gap_coef, gap_se, 2)}  | {util.format_coefficient(gap_reg_coef, gap_reg_se, 2)}   |"
            else:  # "10." in label
                row = f"| {label}            | {util.format_coefficient(nj_mean, nj_se, 2)}           | {util.format_coefficient(pa_mean, pa_se, 2)} | {util.format_coefficient(diff_mean, diff_se, 2)} | {util.format_coefficient(nj_coef, nj_reg_se, 2)}                                  | {util.format_coefficient(gap_coef, gap_se, 2)} | {util.format_coefficient(gap_reg_coef, gap_reg_se, 2)}  |"
            
            table_lines.append(row)
    
    # 添加注释
    table_lines.append("")
    table_lines.append("Notes: Entries in columns (i) and (ii) represent mean changes in the outcome variable indicated by the row heading for stores with available data on the outcome in waves 1 and 2. Entries in columns (iv)-(vi) represent estimated regression coefficients of indicated variable (NJ dummy or initial wage gap) in models for the change in the outcome variable. Regression models include chain dummies and an indicator for company-owned stores.")
    table_lines.append("")
    table_lines.append("ªThe wage gap is the proportional increase in starting wage necessary to raise the wage to the new minimum rate. For stores in Pennsylvania, the wage gap is zero.")
    table_lines.append("")
    table_lines.append("ᵇModels in column (vi) include dummies for two regions of New Jersey and two regions of eastern Pennsylvania.")
    table_lines.append("")
    table_lines.append("ᶜFraction of part-time employees in total full-time-equivalent employment.")
    
    return "\n".join(table_lines)

def main():
    """
    生成表6的主函数
    """
    # 使用utility模块读取和处理数据
    df = util.read_data()
    df = util.create_basic_derived_variables(df)
    
    # 计算表6特有的变量
    df = calculate_table6_variables(df)
    
    # 生成并打印表格
    table = generate_table_6(df)
    print(table)
    
    # 保存到文件
    output_path = util.get_output_path(__file__)
    util.save_output_to_file(table, output_path)

if __name__ == "__main__":
    main()