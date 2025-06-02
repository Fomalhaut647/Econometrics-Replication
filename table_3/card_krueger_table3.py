#!/usr/bin/env python3
"""
Card and Krueger (1994) Table 3 Replication
表3复现：新泽西州最低工资上涨前后每家店铺的平均就业情况
Average Employment Per Store Before and After the Rise in New Jersey Minimum Wage

This script replicates Table 3 from the famous Card and Krueger (1994) paper:
"Minimum Wages and Employment: A Case Study of the Fast-Food Industry in New Jersey and Pennsylvania"

Author: Card-Krueger Replication Team
Date: 2024
"""

import os
import sys
import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

def get_data_path():
    """
    获取数据文件路径，支持从任何目录运行
    """
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 尝试不同的可能路径
    possible_paths = [
        os.path.join(script_dir, '..', 'data', 'public.dat'),  # 从table_3目录运行
        os.path.join(script_dir, 'data', 'public.dat'),        # 如果data在同一目录
        os.path.join(os.getcwd(), 'data', 'public.dat'),       # 从项目根目录运行
        'data/public.dat'                                       # 相对路径
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # 如果都找不到，抛出错误
    raise FileNotFoundError(
        "Could not find data/public.dat. Please ensure the data directory "
        "is accessible from the current working directory or script location."
    )

def read_data(file_path=None):
    """
    读取Card-Krueger数据集
    根据码本定义的列位置读取固定列宽格式数据
    """
    if file_path is None:
        file_path = get_data_path()
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    # 根据码本定义列规格 (start, end, name)
    colspecs = [
        (0, 3),    # SHEET
        (4, 5),    # CHAIN
        (6, 7),    # CO_OWNED
        (8, 9),    # STATE
        (10, 11),  # SOUTHJ
        (12, 13),  # CENTRALJ
        (14, 15),  # NORTHJ
        (16, 17),  # PA1
        (18, 19),  # PA2
        (20, 21),  # SHORE
        (22, 24),  # NCALLS
        (25, 30),  # EMPFT
        (31, 36),  # EMPPT
        (37, 42),  # NMGRS
        (43, 48),  # WAGE_ST
        (49, 54),  # INCTIME
        (55, 60),  # FIRSTINC
        (61, 62),  # BONUS
        (63, 68),  # PCTAFF
        (69, 70),  # MEALS
        (71, 76),  # OPEN
        (77, 82),  # HRSOPEN
        (83, 88),  # PSODA
        (89, 94),  # PFRY
        (95, 100), # PENTREE
        (101, 103), # NREGS
        (104, 106), # NREGS11
        (107, 108), # TYPE2
        (109, 110), # STATUS2
        (111, 117), # DATE2
        (118, 120), # NCALLS2
        (121, 126), # EMPFT2
        (127, 132), # EMPPT2
        (133, 138), # NMGRS2
        (139, 144), # WAGE_ST2
        (145, 150), # INCTIME2
        (151, 156), # FIRSTIN2
        (157, 158), # SPECIAL2
        (159, 160), # MEALS2
        (161, 166), # OPEN2R
        (167, 172), # HRSOPEN2
        (173, 178), # PSODA2
        (179, 184), # PFRY2
        (185, 190), # PENTREE2
        (191, 193), # NREGS2
        (194, 196), # NREGS112
    ]
    
    names = [
        'SHEET', 'CHAIN', 'CO_OWNED', 'STATE', 'SOUTHJ', 'CENTRALJ', 'NORTHJ',
        'PA1', 'PA2', 'SHORE', 'NCALLS', 'EMPFT', 'EMPPT', 'NMGRS', 'WAGE_ST',
        'INCTIME', 'FIRSTINC', 'BONUS', 'PCTAFF', 'MEALS', 'OPEN', 'HRSOPEN',
        'PSODA', 'PFRY', 'PENTREE', 'NREGS', 'NREGS11', 'TYPE2', 'STATUS2',
        'DATE2', 'NCALLS2', 'EMPFT2', 'EMPPT2', 'NMGRS2', 'WAGE_ST2', 'INCTIME2',
        'FIRSTIN2', 'SPECIAL2', 'MEALS2', 'OPEN2R', 'HRSOPEN2', 'PSODA2',
        'PFRY2', 'PENTREE2', 'NREGS2', 'NREGS112'
    ]
    
    # 读取固定列宽数据
    df = pd.read_fwf(file_path, colspecs=colspecs, names=names, na_values=['.'])
    
    return df

def calculate_fte_employment(df):
    """
    计算全职等量就业 (FTE)
    FTE = (全职员工数，包括经理) + (0.5 * 兼职员工数)
    """
    # Wave 1 (第一波)
    df['FTE_W1'] = df['EMPFT'] + df['NMGRS'] + 0.5 * df['EMPPT']
    
    # Wave 2 (第二波)
    df['FTE_W2'] = df['EMPFT2'] + df['NMGRS2'] + 0.5 * df['EMPPT2']
    
    return df

def identify_store_status(df):
    """
    识别店铺状态
    根据码本：
    STATUS2: 0=拒绝第二次访谈, 1=完成第二次访谈, 2=装修关闭, 3=永久关闭, 4=道路施工关闭, 5=商场火灾关闭
    """
    # 永久关闭：STATUS2 = 3
    df['permanently_closed'] = (df['STATUS2'] == 3)
    
    # 临时关闭：STATUS2 = 2, 4, 5
    df['temporarily_closed'] = df['STATUS2'].isin([2, 4, 5])
    
    return df

def create_wage_groups(df):
    """
    根据第一波起始工资对新泽西州店铺进行分类
    """
    # 新泽西州 (STATE = 1) 的工资分组
    df['wage_group'] = np.nan
    
    # 只对新泽西州店铺分组
    nj_mask = (df['STATE'] == 1)
    
    # 低工资组：$4.25/小时
    low_wage = nj_mask & (df['WAGE_ST'] == 4.25)
    df.loc[low_wage, 'wage_group'] = 'low'
    
    # 中等工资组：$4.26-$4.99/小时
    mid_wage = nj_mask & (df['WAGE_ST'] >= 4.26) & (df['WAGE_ST'] <= 4.99)
    df.loc[mid_wage, 'wage_group'] = 'mid'
    
    # 高工资组：>=$5.00/小时
    high_wage = nj_mask & (df['WAGE_ST'] >= 5.00)
    df.loc[high_wage, 'wage_group'] = 'high'
    
    return df

def calculate_statistics_with_se(data, name=""):
    """
    计算均值和标准误
    """
    if len(data) == 0 or data.isna().all():
        return np.nan, np.nan, 0
    
    clean_data = data.dropna()
    if len(clean_data) == 0:
        return np.nan, np.nan, 0
    
    mean = clean_data.mean()
    se = clean_data.std() / np.sqrt(len(clean_data))
    n = len(clean_data)
    
    return mean, se, n

def process_row_1_2(df):
    """
    处理表格第1-2行：上涨前后FTE就业，所有可获得观测值
    """
    results = {}
    
    # 第1行：上涨前FTE就业
    # NJ
    nj_mask = (df['STATE'] == 1)
    nj_w1_data = df.loc[nj_mask, 'FTE_W1']
    nj_w1_mean, nj_w1_se, nj_w1_n = calculate_statistics_with_se(nj_w1_data)
    
    # PA
    pa_mask = (df['STATE'] == 0)
    pa_w1_data = df.loc[pa_mask, 'FTE_W1']
    pa_w1_mean, pa_w1_se, pa_w1_n = calculate_statistics_with_se(pa_w1_data)
    
    # NJ工资分组
    nj_low_w1 = df.loc[nj_mask & (df['wage_group'] == 'low'), 'FTE_W1']
    nj_low_w1_mean, nj_low_w1_se, _ = calculate_statistics_with_se(nj_low_w1)
    
    nj_mid_w1 = df.loc[nj_mask & (df['wage_group'] == 'mid'), 'FTE_W1']
    nj_mid_w1_mean, nj_mid_w1_se, _ = calculate_statistics_with_se(nj_mid_w1)
    
    nj_high_w1 = df.loc[nj_mask & (df['wage_group'] == 'high'), 'FTE_W1']
    nj_high_w1_mean, nj_high_w1_se, _ = calculate_statistics_with_se(nj_high_w1)
    
    # 第2行：上涨后FTE就业
    # 对于第2行，需要特殊处理：永久关闭店铺设为0，临时关闭视为缺失
    df_w2 = df.copy()
    # 永久关闭店铺的FTE_W2设为0
    df_w2.loc[df_w2['permanently_closed'], 'FTE_W2'] = 0
    # 临时关闭店铺的FTE_W2设为NaN（缺失）
    df_w2.loc[df_w2['temporarily_closed'], 'FTE_W2'] = np.nan
    
    # NJ
    nj_w2_data = df_w2.loc[nj_mask, 'FTE_W2']
    nj_w2_mean, nj_w2_se, nj_w2_n = calculate_statistics_with_se(nj_w2_data)
    
    # PA
    pa_w2_data = df_w2.loc[pa_mask, 'FTE_W2']
    pa_w2_mean, pa_w2_se, pa_w2_n = calculate_statistics_with_se(pa_w2_data)
    
    # NJ工资分组
    nj_low_w2 = df_w2.loc[nj_mask & (df['wage_group'] == 'low'), 'FTE_W2']
    nj_low_w2_mean, nj_low_w2_se, _ = calculate_statistics_with_se(nj_low_w2)
    
    nj_mid_w2 = df_w2.loc[nj_mask & (df['wage_group'] == 'mid'), 'FTE_W2']
    nj_mid_w2_mean, nj_mid_w2_se, _ = calculate_statistics_with_se(nj_mid_w2)
    
    nj_high_w2 = df_w2.loc[nj_mask & (df['wage_group'] == 'high'), 'FTE_W2']
    nj_high_w2_mean, nj_high_w2_se, _ = calculate_statistics_with_se(nj_high_w2)
    
    results['row1'] = {
        'nj': (nj_w1_mean, nj_w1_se),
        'pa': (pa_w1_mean, pa_w1_se),
        'nj_low': (nj_low_w1_mean, nj_low_w1_se),
        'nj_mid': (nj_mid_w1_mean, nj_mid_w1_se),
        'nj_high': (nj_high_w1_mean, nj_high_w1_se)
    }
    
    results['row2'] = {
        'nj': (nj_w2_mean, nj_w2_se),
        'pa': (pa_w2_mean, pa_w2_se),
        'nj_low': (nj_low_w2_mean, nj_low_w2_se),
        'nj_mid': (nj_mid_w2_mean, nj_mid_w2_se),
        'nj_high': (nj_high_w2_mean, nj_high_w2_se)
    }
    
    return results

def process_row_3(df):
    """
    处理表格第3行：平均FTE就业变化，所有可获得观测值
    Row 3 应该使用所有可获得的观测值来计算平均变化，而不只是平衡样本
    这意味着我们计算两个独立的均值（W1和W2）的差值，而不是逐店铺计算变化
    """
    # 为Row 3使用与Row 1-2相同的处理方式
    df_w1 = df.copy()
    df_w2 = df.copy()
    
    # Row 1: Wave 1数据（所有可用观测）
    # Row 2: Wave 2数据（永久关闭设为0，临时关闭设为缺失）
    df_w2.loc[df_w2['permanently_closed'], 'FTE_W2'] = 0
    df_w2.loc[df_w2['temporarily_closed'], 'FTE_W2'] = np.nan
    
    # 计算各组的统计 - 使用两个独立均值的差
    nj_mask = (df['STATE'] == 1)
    pa_mask = (df['STATE'] == 0)
    
    # NJ: W2均值 - W1均值
    nj_w1_mean, nj_w1_se, _ = calculate_statistics_with_se(df_w1.loc[nj_mask, 'FTE_W1'])
    nj_w2_mean, nj_w2_se, _ = calculate_statistics_with_se(df_w2.loc[nj_mask, 'FTE_W2'])
    nj_demp_mean = nj_w2_mean - nj_w1_mean
    nj_demp_se = np.sqrt(nj_w1_se**2 + nj_w2_se**2)
    
    # PA: W2均值 - W1均值
    pa_w1_mean, pa_w1_se, _ = calculate_statistics_with_se(df_w1.loc[pa_mask, 'FTE_W1'])
    pa_w2_mean, pa_w2_se, _ = calculate_statistics_with_se(df_w2.loc[pa_mask, 'FTE_W2'])
    pa_demp_mean = pa_w2_mean - pa_w1_mean
    pa_demp_se = np.sqrt(pa_w1_se**2 + pa_w2_se**2)
    
    # NJ工资分组
    # Low wage
    nj_low_w1_mean, nj_low_w1_se, _ = calculate_statistics_with_se(df_w1.loc[nj_mask & (df['wage_group'] == 'low'), 'FTE_W1'])
    nj_low_w2_mean, nj_low_w2_se, _ = calculate_statistics_with_se(df_w2.loc[nj_mask & (df['wage_group'] == 'low'), 'FTE_W2'])
    nj_low_demp_mean = nj_low_w2_mean - nj_low_w1_mean
    nj_low_demp_se = np.sqrt(nj_low_w1_se**2 + nj_low_w2_se**2)
    
    # Mid wage
    nj_mid_w1_mean, nj_mid_w1_se, _ = calculate_statistics_with_se(df_w1.loc[nj_mask & (df['wage_group'] == 'mid'), 'FTE_W1'])
    nj_mid_w2_mean, nj_mid_w2_se, _ = calculate_statistics_with_se(df_w2.loc[nj_mask & (df['wage_group'] == 'mid'), 'FTE_W2'])
    nj_mid_demp_mean = nj_mid_w2_mean - nj_mid_w1_mean
    nj_mid_demp_se = np.sqrt(nj_mid_w1_se**2 + nj_mid_w2_se**2)
    
    # High wage
    nj_high_w1_mean, nj_high_w1_se, _ = calculate_statistics_with_se(df_w1.loc[nj_mask & (df['wage_group'] == 'high'), 'FTE_W1'])
    nj_high_w2_mean, nj_high_w2_se, _ = calculate_statistics_with_se(df_w2.loc[nj_mask & (df['wage_group'] == 'high'), 'FTE_W2'])
    nj_high_demp_mean = nj_high_w2_mean - nj_high_w1_mean
    nj_high_demp_se = np.sqrt(nj_high_w1_se**2 + nj_high_w2_se**2)
    
    return {
        'nj': (nj_demp_mean, nj_demp_se),
        'pa': (pa_demp_mean, pa_demp_se),
        'nj_low': (nj_low_demp_mean, nj_low_demp_se),
        'nj_mid': (nj_mid_demp_mean, nj_mid_demp_se),
        'nj_high': (nj_high_demp_mean, nj_high_demp_se)
    }

def process_row_4(df):
    """
    处理表格第4行：平均FTE就业变化，平衡样本店铺
    平衡样本：在第一波和第二波中均具有有效就业数据的店铺
    """
    # 创建平衡样本：两波都有FTE数据的店铺
    balanced_mask = df['FTE_W1'].notna() & df['FTE_W2'].notna()
    
    # 对于永久关闭的店铺，如果第一波有数据，包含在平衡样本中（第二波FTE为0）
    permanently_closed_with_w1 = df['permanently_closed'] & df['FTE_W1'].notna()
    balanced_mask = balanced_mask | permanently_closed_with_w1
    
    # 临时关闭店铺从平衡样本中排除（因为第二波视为缺失）
    balanced_mask = balanced_mask & (~df['temporarily_closed'])
    
    df_balanced = df.loc[balanced_mask].copy()
    
    # 对永久关闭店铺设置FTE_W2 = 0
    df_balanced.loc[df_balanced['permanently_closed'], 'FTE_W2'] = 0
    
    # 计算就业变化
    df_balanced['FTE_change'] = df_balanced['FTE_W2'] - df_balanced['FTE_W1']
    
    # 计算各组统计
    nj_mask = (df_balanced['STATE'] == 1)
    pa_mask = (df_balanced['STATE'] == 0)
    
    nj_change = df_balanced.loc[nj_mask, 'FTE_change']
    nj_change_mean, nj_change_se, _ = calculate_statistics_with_se(nj_change)
    
    pa_change = df_balanced.loc[pa_mask, 'FTE_change']
    pa_change_mean, pa_change_se, _ = calculate_statistics_with_se(pa_change)
    
    # NJ工资分组
    nj_low_change = df_balanced.loc[nj_mask & (df_balanced['wage_group'] == 'low'), 'FTE_change']
    nj_low_change_mean, nj_low_change_se, _ = calculate_statistics_with_se(nj_low_change)
    
    nj_mid_change = df_balanced.loc[nj_mask & (df_balanced['wage_group'] == 'mid'), 'FTE_change']
    nj_mid_change_mean, nj_mid_change_se, _ = calculate_statistics_with_se(nj_mid_change)
    
    nj_high_change = df_balanced.loc[nj_mask & (df_balanced['wage_group'] == 'high'), 'FTE_change']
    nj_high_change_mean, nj_high_change_se, _ = calculate_statistics_with_se(nj_high_change)
    
    return {
        'nj': (nj_change_mean, nj_change_se),
        'pa': (pa_change_mean, pa_change_se),
        'nj_low': (nj_low_change_mean, nj_low_change_se),
        'nj_mid': (nj_mid_change_mean, nj_mid_change_se),
        'nj_high': (nj_high_change_mean, nj_high_change_se)
    }

def process_row_5(df):
    """
    处理表格第5行：平均FTE就业变化，将临时关闭店铺的FTE设为0
    使用与第4行相同的平衡样本，但临时关闭店铺的第二波FTE设为0而非缺失
    """
    # 使用相同的平衡样本定义，但包含临时关闭店铺
    balanced_mask = df['FTE_W1'].notna() & df['FTE_W2'].notna()
    permanently_closed_with_w1 = df['permanently_closed'] & df['FTE_W1'].notna()
    temporarily_closed_with_w1 = df['temporarily_closed'] & df['FTE_W1'].notna()
    
    balanced_mask = balanced_mask | permanently_closed_with_w1 | temporarily_closed_with_w1
    
    df_balanced = df.loc[balanced_mask].copy()
    
    # 对永久关闭和临时关闭店铺都设置FTE_W2 = 0
    df_balanced.loc[df_balanced['permanently_closed'], 'FTE_W2'] = 0
    df_balanced.loc[df_balanced['temporarily_closed'], 'FTE_W2'] = 0
    
    # 计算就业变化
    df_balanced['FTE_change'] = df_balanced['FTE_W2'] - df_balanced['FTE_W1']
    
    # 计算各组统计
    nj_mask = (df_balanced['STATE'] == 1)
    pa_mask = (df_balanced['STATE'] == 0)
    
    nj_change = df_balanced.loc[nj_mask, 'FTE_change']
    nj_change_mean, nj_change_se, _ = calculate_statistics_with_se(nj_change)
    
    pa_change = df_balanced.loc[pa_mask, 'FTE_change']
    pa_change_mean, pa_change_se, _ = calculate_statistics_with_se(pa_change)
    
    # NJ工资分组
    nj_low_change = df_balanced.loc[nj_mask & (df_balanced['wage_group'] == 'low'), 'FTE_change']
    nj_low_change_mean, nj_low_change_se, _ = calculate_statistics_with_se(nj_low_change)
    
    nj_mid_change = df_balanced.loc[nj_mask & (df_balanced['wage_group'] == 'mid'), 'FTE_change']
    nj_mid_change_mean, nj_mid_change_se, _ = calculate_statistics_with_se(nj_mid_change)
    
    nj_high_change = df_balanced.loc[nj_mask & (df_balanced['wage_group'] == 'high'), 'FTE_change']
    nj_high_change_mean, nj_high_change_se, _ = calculate_statistics_with_se(nj_high_change)
    
    return {
        'nj': (nj_change_mean, nj_change_se),
        'pa': (pa_change_mean, pa_change_se),
        'nj_low': (nj_low_change_mean, nj_low_change_se),
        'nj_mid': (nj_mid_change_mean, nj_mid_change_se),
        'nj_high': (nj_high_change_mean, nj_high_change_se)
    }

def calculate_differences(row_data):
    """
    计算差值及其标准误
    """
    # NJ-PA差值
    nj_mean, nj_se = row_data['nj']
    pa_mean, pa_se = row_data['pa']
    
    if not (np.isnan(nj_mean) or np.isnan(pa_mean)):
        diff_nj_pa = nj_mean - pa_mean
        diff_nj_pa_se = np.sqrt(nj_se**2 + pa_se**2)
    else:
        diff_nj_pa = np.nan
        diff_nj_pa_se = np.nan
    
    # 低-高差值 (NJ内部)
    low_mean, low_se = row_data['nj_low']
    high_mean, high_se = row_data['nj_high']
    
    if not (np.isnan(low_mean) or np.isnan(high_mean)):
        diff_low_high = low_mean - high_mean
        diff_low_high_se = np.sqrt(low_se**2 + high_se**2)
    else:
        diff_low_high = np.nan
        diff_low_high_se = np.nan
    
    # 中-高差值 (NJ内部)
    mid_mean, mid_se = row_data['nj_mid']
    
    if not (np.isnan(mid_mean) or np.isnan(high_mean)):
        diff_mid_high = mid_mean - high_mean
        diff_mid_high_se = np.sqrt(mid_se**2 + high_se**2)
    else:
        diff_mid_high = np.nan
        diff_mid_high_se = np.nan
    
    return {
        'nj_pa': (diff_nj_pa, diff_nj_pa_se),
        'low_high': (diff_low_high, diff_low_high_se),
        'mid_high': (diff_mid_high, diff_mid_high_se)
    }

def format_number(mean, se):
    """
    格式化数字以匹配目标表格
    """
    if np.isnan(mean) or np.isnan(se):
        return "."
    
    # 根据数值大小选择适当的小数位数
    mean_str = f"{mean:.2f}"
    se_str = f"{se:.2f}"
    
    return f"{mean_str} ({se_str})"

def generate_table_3(df, output_file=None):
    """
    生成表3的完整输出
    """
    output_lines = []
    
    output_lines.append("**TABLE 3-AVERAGE EMPLOYMENT PER STORE BEFORE AND AFTER THE RISE IN NEW JERSEY MINIMUM WAGE**")
    output_lines.append("")
    
    # 处理各行数据
    row1_2_data = process_row_1_2(df)
    row3_data = process_row_3(df)
    row4_data = process_row_4(df)
    row5_data = process_row_5(df)
    
    # 计算差值
    row1_diffs = calculate_differences(row1_2_data['row1'])
    row2_diffs = calculate_differences(row1_2_data['row2'])
    row3_diffs = calculate_differences(row3_data)
    row4_diffs = calculate_differences(row4_data)
    row5_diffs = calculate_differences(row5_data)
    
    # 表头
    header = "| Variable | NJ (i) | PA (ii) | Difference, NJ-PA (iii) | NJ Wage = $4.25 (iv) | NJ Wage = $4.26-$4.99 (v) | NJ Wage >= $5.00 (vi) | Diff Low-high (vii)<sup>b</sup> | Diff Midrange-high (viii)<sup>b</sup> |"
    separator = "| :----------------------------------------------------------------------- | :------------ | :------------ | :---------------------- | :------------------- | :------------------------ | :-------------------- | :-------------------------- | :---------------------------- |"
    
    output_lines.append(header)
    output_lines.append(separator)
    
    # 第1行
    row1 = row1_2_data['row1']
    row1_diff = row1_diffs
    line1 = f"| 1. FTE employment before, all available observations<sup>a</sup> | {format_number(*row1['nj'])} | {format_number(*row1['pa'])} | {format_number(*row1_diff['nj_pa'])} | {format_number(*row1['nj_low'])} | {format_number(*row1['nj_mid'])} | {format_number(*row1['nj_high'])} | {format_number(*row1_diff['low_high'])} | {format_number(*row1_diff['mid_high'])} |"
    output_lines.append(line1)
    
    # 第2行
    row2 = row1_2_data['row2']
    row2_diff = row2_diffs
    line2 = f"| 2. FTE employment after, all available observations<sup>a</sup> | {format_number(*row2['nj'])} | {format_number(*row2['pa'])} | {format_number(*row2_diff['nj_pa'])} | {format_number(*row2['nj_low'])} | {format_number(*row2['nj_mid'])} | {format_number(*row2['nj_high'])} | {format_number(*row2_diff['low_high'])} | {format_number(*row2_diff['mid_high'])} |"
    output_lines.append(line2)
    
    # 第3行
    row3_diff = row3_diffs
    line3 = f"| 3. Change in mean FTE employment | {format_number(*row3_data['nj'])} | {format_number(*row3_data['pa'])} | {format_number(*row3_diff['nj_pa'])} | {format_number(*row3_data['nj_low'])} | {format_number(*row3_data['nj_mid'])} | {format_number(*row3_data['nj_high'])} | {format_number(*row3_diff['low_high'])} | {format_number(*row3_diff['mid_high'])} |"
    output_lines.append(line3)
    
    # 第4行
    row4_diff = row4_diffs
    line4 = f"| 4. Change in mean FTE employment, balanced sample of stores<sup>c</sup> | {format_number(*row4_data['nj'])} | {format_number(*row4_data['pa'])} | {format_number(*row4_diff['nj_pa'])} | {format_number(*row4_data['nj_low'])} | {format_number(*row4_data['nj_mid'])} | {format_number(*row4_data['nj_high'])} | {format_number(*row4_diff['low_high'])} | {format_number(*row4_diff['mid_high'])} |"
    output_lines.append(line4)
    
    # 第5行
    row5_diff = row5_diffs
    line5 = f"| 5. Change in mean FTE employment, setting FTE at temporarily closed stores to 0<sup>d</sup> | {format_number(*row5_data['nj'])} | {format_number(*row5_data['pa'])} | {format_number(*row5_diff['nj_pa'])} | {format_number(*row5_data['nj_low'])} | {format_number(*row5_data['nj_mid'])} | {format_number(*row5_data['nj_high'])} | {format_number(*row5_diff['low_high'])} | {format_number(*row5_diff['mid_high'])} |"
    output_lines.append(line5)
    
    output_lines.append("")
    output_lines.append("Notes: Standard errors are shown in parentheses. The sample consists of all stores with available data on employment.")
    output_lines.append("<sup>a</sup> FTE (full-time-equivalent) employment counts each part-time worker as half a full-time worker. Employment at six closed stores is set to zero. Employment at four temporarily closed stores is treated as missing.")
    output_lines.append("<sup>b</sup> Stores in New Jersey were classified by whether starting wage in wave 1 equals $4.25 per hour (N=101), is between $4.26 and $4.99 per hour (N=140), or is $5.00 per hour or higher (N=73). Difference in employment between low-wage ($4.25 per hour) and high-wage (>= $5.00 per hour) stores; and difference in employment between midrange ($4.26-$4.99 per hour) and high-wage stores.")
    output_lines.append("<sup>c</sup> Subset of stores with available employment data in wave 1 and wave 2.")
    output_lines.append("<sup>d</sup> In this row only, wave-2 employment at four temporarily closed stores is set to 0. Employment changes are based on the subset of stores with available employment data in wave 1 and wave 2.")
    
    # 输出到控制台
    for line in output_lines:
        print(line)
    
    # 如果指定了输出文件，也写入文件
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(output_lines))
            print(f"\nTable 3 results saved to: {output_file}")
        except Exception as e:
            print(f"\nWarning: Could not save results to file: {e}")

def print_verification_statistics(df):
    """
    打印验证统计信息
    """
    print("\n" + "=" * 80)
    print("VERIFICATION STATISTICS")
    print("=" * 80)
    
    # 样本大小
    print(f"Total observations: {len(df)}")
    print(f"NJ stores: {(df['STATE'] == 1).sum()}")
    print(f"PA stores: {(df['STATE'] == 0).sum()}")
    print(f"Permanently closed stores: {df['permanently_closed'].sum()}")
    print(f"Temporarily closed stores: {df['temporarily_closed'].sum()}")
    
    # NJ工资分组统计
    nj_mask = (df['STATE'] == 1)
    print(f"NJ low wage ($4.25): {(nj_mask & (df['wage_group'] == 'low')).sum()}")
    print(f"NJ mid wage ($4.26-$4.99): {(nj_mask & (df['wage_group'] == 'mid')).sum()}")
    print(f"NJ high wage (>=$5.00): {(nj_mask & (df['wage_group'] == 'high')).sum()}")

def main(output_file=None):
    """
    主函数
    """
    print("Card and Krueger (1994) Table 3 Replication")
    print("=" * 80)
    
    try:
        # 读取数据
        print("Reading data...")
        data_path = get_data_path()
        print(f"Data file: {data_path}")
        df = read_data(data_path)
        print(f"Loaded {len(df)} observations")
        
        # 计算FTE就业
        print("Calculating FTE employment...")
        df = calculate_fte_employment(df)
        
        # 识别店铺状态
        print("Identifying store status...")
        df = identify_store_status(df)
        
        # 创建工资分组
        print("Creating wage groups...")
        df = create_wage_groups(df)
        
        # 生成表3
        print("\nGenerating Table 3...")
        print("=" * 80)
        generate_table_3(df, output_file)
        
        # 验证关键统计
        print_verification_statistics(df)
        
        print("\n" + "=" * 80)
        print("SUCCESS: Table 3 replication completed!")
        print("=" * 80)
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Please ensure the data/public.dat file is available in one of the following locations:")
        print("- data/public.dat (relative to current directory)")
        print("- ../data/public.dat (relative to script location)")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # 检查命令行参数
    output_file = None
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
        print(f"Output will be saved to: {output_file}")
    
    main(output_file) 