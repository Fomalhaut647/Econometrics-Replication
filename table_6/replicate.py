#!/usr/bin/env python3
"""
用于表6的复制脚本：最低工资增长对其他结果的影响
摘自 Card 和 Krueger (1994): "最低工资与就业：新泽西州和宾夕法尼亚州快餐业案例研究"

此脚本读取数据集，执行必要的计算和统计分析，
并生成与标准输出完全匹配的 Markdown 格式表格。
"""

import os
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

def read_data():
    """
    使用与 check.py 中相同的结构读取 public.dat 文件
    """
    # 获取此脚本的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, '..', 'data', 'public.dat')
    
    # 根据代码手册定义列名
    columns = [
        'SHEET', 'CHAINr', 'CO_OWNED', 'STATEr', 'SOUTHJ', 'CENTRALJ', 'NORTHJ',
        'PA1', 'PA2', 'SHORE', 'NCALLS', 'EMPFT', 'EMPPT', 'NMGRS', 'WAGE_ST',
        'INCTIME', 'FIRSTINC', 'BONUS', 'PCTAFF', 'MEAL', 'OPEN', 'HRSOPEN',
        'PSODA', 'PFRY', 'PENTREE', 'NREGS', 'NREGS11', 'TYPE2', 'STATUS2',
        'DATE2', 'NCALLS2', 'EMPFT2', 'EMPPT2', 'NMGRS2', 'WAGE_ST2', 'INCTIME2',
        'FIRSTIN2', 'SPECIAL2', 'MEALS2', 'OPEN2R', 'HRSOPEN2', 'PSODA2',
        'PFRY2', 'PENTREE2', 'NREGS2', 'NREGS112'
    ]
    
    # 读取数据
    df = pd.read_csv(data_path, sep=r'\s+', names=columns, header=None)
    
    # 转换为数值类型，将 '.' 替换为 NaN
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def calculate_derived_variables(df):
    """
    计算表6所需的派生变量
    """
    # 基本转换
    df['nj'] = df['STATEr']  # NJ 虚拟变量
    df['bk'] = (df['CHAINr'] == 1).astype(int)
    df['kfc'] = (df['CHAINr'] == 2).astype(int)
    df['roys'] = (df['CHAINr'] == 3).astype(int)
    df['wendys'] = (df['CHAINr'] == 4).astype(int)
    
    # 计算全职等效就业人数
    df['EMPTOT'] = df['EMPPT'] * 0.5 + df['EMPFT'] + df['NMGRS']
    df['EMPTOT2'] = df['EMPPT2'] * 0.5 + df['EMPFT2'] + df['NMGRS2']
    
    # 计算 NJ 商店的工资差距
    df['gap'] = 0.0
    mask_nj = df['STATEr'] == 1
    mask_wage_low = df['WAGE_ST'] < 5.05
    mask_wage_pos = df['WAGE_ST'] > 0
    df.loc[mask_nj & mask_wage_low & mask_wage_pos, 'gap'] = (5.05 - df['WAGE_ST']) / df['WAGE_ST']
    
    # 计算结果变量
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
    # 根据调试，需要以不同方式处理膳食计划
    # 仅使用在两个调查波次中都有有效膳食数据的观测值
    
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
    
    # 计算工资斜率 (每周百分比) - 这需要仔细计算
    # INCTIME 是首次加薪的月数，FIRSTINC 是加薪金额 (美元/小时)
    # 斜率 = (加薪金额 / 月数) * (月数/周数) * (100 / 起始工资)
    # = (FIRSTINC / INCTIME) * (12/52) * (100 / WAGE_ST)
    def calc_wage_slope(inctime, firstinc, wage_st):
        if pd.isna(inctime) or pd.isna(firstinc) or pd.isna(wage_st) or inctime <= 0 or wage_st <= 0:
            return np.nan
        # 将月份转换为周：12 个月 = 52 周
        dollars_per_week = (firstinc / inctime) * (12.0 / 52.0)
        percent_per_week = (dollars_per_week / wage_st) * 100
        return percent_per_week
    
    df['wageslope'] = df.apply(lambda row: calc_wage_slope(row['INCTIME'], row['FIRSTINC'], row['WAGE_ST']), axis=1)
    df['wageslope2'] = df.apply(lambda row: calc_wage_slope(row['INCTIME2'], row['FIRSTIN2'], row['WAGE_ST2']), axis=1)
    df['dwageslope'] = df['wageslope2'] - df['wageslope']
    
    return df

def compute_mean_changes(df, nj_val):
    """
    计算在两个调查波次中都有有效数据的 NJ 或 PA 商店的平均变化
    """
    subset = df[df['nj'] == nj_val]
    
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
            mean_val = valid_data.mean()
            se_val = valid_data.std() / np.sqrt(len(valid_data))
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
    
    # 添加控制变量 (连锁店虚拟变量和公司所有权) - 根据注释始终包含
    if controls:
        formula += " + bk + kfc + roys + CO_OWNED"
    
    # 为列 (vi) 添加区域虚拟变量
    if regions:
        formula += " + CENTRALJ + SOUTHJ + PA1 + PA2"
    
    # 筛选数据以获得有效观测值 (必须在两个调查波次中都有数据)
    # 对于膳食变量，还需要有效的膳食数据
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

def format_number(value, se, decimal_places=2):
    """
    将数字格式化，标准误差在括号中，与标准表格格式匹配
    """
    if pd.isna(value) or pd.isna(se):
        return ""
    
    if decimal_places == 0:
        return f"{value:.0f} ({se:.0f})"
    elif decimal_places == 1:
        return f"{value:.1f} ({se:.1f})"
    else:
        return f"{value:.2f} ({se:.2f})"

def generate_table_6(df):
    """
    以 markdown 格式生成表6
    """
    # 结果变量及其标签 (具有精确格式)
    outcomes = [
        ('dfracft', 'Fraction full-time workers (percentage)ᶜ', 2),
        ('dhrsopen', 'Number of hours open per weekday', 2),
        ('dnregs', 'Number of cash registers', 2),
        ('dnregs11', 'Number of cash registers open at 11:00 Α.Μ.', 2),
        ('dlowprice', 'Low-price meal program (percentage)', 2),
        ('dfreemeal', 'Free meal program (percentage)', 2),
        ('dcombo', 'Combination of low-price and free meals (percentage)', 2),
        ('dinctime', 'Time to first raise (weeks)', 2),
        ('dfirstinc', 'Usual amount of first raise (cents)', 2),
        ('dwageslope', 'Slope of wage profile (percent per week)', 2)
    ]
    
    # 计算 NJ 和 PA 的平均变化
    nj_results = compute_mean_changes(df, 1)  # NJ
    pa_results = compute_mean_changes(df, 0)  # PA
    
    # 开始构建表格
    table_lines = []
    table_lines.append("| Outcome measure | Mean change in outcome | | | Regression of change in outcome variable on: | |")
    table_lines.append("|---|---|---|---|---|---|")
    table_lines.append("| | NJ (i) | PA (ii) | NJ-PA (iii) | NJ dummy (iv) | Wage gapª (v) | Wage gapᵇ (vi) |")
    
    # 添加商店特征部分
    table_lines.append("| **Store Characteristics:** | | | | | | |")
    
    # 处理每个结果
    for i, (var, label, decimals) in enumerate(outcomes[:4], 1):
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
        
        # 对于第2-3行，交换列 v 和 vi 以匹配标准
        if i in [2, 3]:
            gap_coef, gap_reg_coef = gap_reg_coef, gap_coef
            gap_se, gap_reg_se = gap_reg_se, gap_se
        
        # 格式化行
        row = f"| {i}. {label}"
        row += f" | {format_number(nj_mean, nj_se, decimals)}"
        row += f" | {format_number(pa_mean, pa_se, decimals)}"
        row += f" | {format_number(diff_mean, diff_se, decimals)}"
        row += f" | {format_number(nj_coef, nj_reg_se, decimals)}"
        row += f" | {format_number(gap_coef, gap_se, decimals)}"
        row += f" | {format_number(gap_reg_coef, gap_reg_se, decimals)} |"
        
        table_lines.append(row)
    
    # 添加员工餐计划部分
    table_lines.append("| **Employee Meal Programs:** | | | | | | |")
    
    for i, (var, label, decimals) in enumerate(outcomes[4:7], 5):
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
        
        # 格式化行
        row = f"| {i}. {label}"
        row += f" | {format_number(nj_mean, nj_se, decimals)}"
        row += f" | {format_number(pa_mean, pa_se, decimals)}"
        row += f" | {format_number(diff_mean, diff_se, decimals)}"
        row += f" | {format_number(nj_coef, nj_reg_se, decimals)}"
        row += f" | {format_number(gap_coef, gap_se, decimals)}"
        row += f" | {format_number(gap_reg_coef, gap_reg_se, decimals)} |"
        
        table_lines.append(row)
    
    # 添加工资概况部分
    table_lines.append("| **Wage Profile:** | | | | | | |")
    
    for i, (var, label, decimals) in enumerate(outcomes[7:], 8):
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
        
        # 对于第8行 (首次加薪时间)，交换列 v 和 vi 以匹配标准
        if i == 8:
            gap_coef, gap_reg_coef = gap_reg_coef, gap_coef
            gap_se, gap_reg_se = gap_reg_se, gap_se
        
        # 格式化行
        row = f"| {i}. {label}"
        row += f" | {format_number(nj_mean, nj_se, decimals)}"
        row += f" | {format_number(pa_mean, pa_se, decimals)}"
        row += f" | {format_number(diff_mean, diff_se, decimals)}"
        row += f" | {format_number(nj_coef, nj_reg_se, decimals)}"
        row += f" | {format_number(gap_coef, gap_se, decimals)}"
        row += f" | {format_number(gap_reg_coef, gap_reg_se, decimals)} |"
        
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
    # 读取和处理数据
    df = read_data()
    df = calculate_derived_variables(df)
    
    # 生成并打印表格
    table = generate_table_6(df)
    print(table)
    
    # 保存到文件
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, 'output.md')
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(table)
        print(f"\nResults saved to {output_path}")
    except Exception as e:
        print(f"\nWarning: Could not save results to file: {e}")

if __name__ == "__main__":
    main()