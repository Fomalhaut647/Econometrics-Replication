#!/usr/bin/env python3
"""
通用工具模块：Card和Krueger (1994) 复制研究
包含数据读取、处理、统计计算和输出格式化的通用函数
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats
import os
from pathlib import Path

# =============================================================================
# 数据读取和基础处理
# =============================================================================

def get_data_path():
    """
    获取数据文件的绝对路径
    """
    # 假设utility.py在根目录，数据在data子目录中
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, 'data', 'public.dat')

def get_column_names():
    """
    返回标准化的列名列表
    """
    return [
        'SHEET', 'CHAINr', 'CO_OWNED', 'STATEr', 'SOUTHJ', 'CENTRALJ', 'NORTHJ',
        'PA1', 'PA2', 'SHORE', 'NCALLS', 'EMPFT', 'EMPPT', 'NMGRS', 'WAGE_ST',
        'INCTIME', 'FIRSTINC', 'BONUS', 'PCTAFF', 'MEAL', 'OPEN', 'HRSOPEN',
        'PSODA', 'PFRY', 'PENTREE', 'NREGS', 'NREGS11', 'TYPE2', 'STATUS2',
        'DATE2', 'NCALLS2', 'EMPFT2', 'EMPPT2', 'NMGRS2', 'WAGE_ST2', 'INCTIME2',
        'FIRSTIN2', 'SPECIAL2', 'MEALS2', 'OPEN2R', 'HRSOPEN2', 'PSODA2',
        'PFRY2', 'PENTREE2', 'NREGS2', 'NREGS112'
    ]

def read_data(method='whitespace'):
    """
    读取public.dat数据文件
    
    Parameters:
    method (str): 'whitespace' 或 'fixed_width'
    
    Returns:
    pd.DataFrame: 处理后的数据框
    """
    data_path = get_data_path()
    columns = get_column_names()
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"数据文件未找到: {data_path}")
    
    if method == 'whitespace':
        # 使用空白字符分隔
        df = pd.read_csv(data_path, sep=r'\s+', names=columns, header=None)
    elif method == 'fixed_width':
        # 使用固定宽度格式（如table_3使用的方法）
        colspecs = [
            (0, 3), (4, 5), (6, 7), (8, 9), (10, 11), (12, 13), (14, 15),
            (16, 17), (18, 19), (20, 21), (22, 24), (25, 30), (31, 36),
            (37, 42), (43, 48), (49, 54), (55, 60), (61, 62), (63, 68),
            (69, 70), (71, 76), (77, 82), (83, 88), (89, 94), (95, 100),
            (101, 103), (104, 106), (107, 108), (109, 110), (111, 117),
            (118, 120), (121, 126), (127, 132), (133, 138), (139, 144),
            (145, 150), (151, 156), (157, 158), (159, 160), (161, 166),
            (167, 172), (173, 178), (179, 184), (185, 190), (191, 193),
            (194, 196)
        ]
        df = pd.read_fwf(data_path, colspecs=colspecs, names=columns, na_values=['.'])
    else:
        raise ValueError("method必须是'whitespace'或'fixed_width'")
    
    # 转换为数值类型
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

# =============================================================================
# 衍生变量计算
# =============================================================================

def calculate_fte_employment(df, part_time_weight=0.5):
    """
    计算全职等效就业 (FTE employment)
    
    Parameters:
    df (pd.DataFrame): 数据框
    part_time_weight (float): 兼职员工权重，默认0.5
    
    Returns:
    pd.DataFrame: 添加了FTE变量的数据框
    """
    df = df.copy()
    
    # Wave 1 FTE employment
    df['EMPTOT'] = df['EMPFT'] + df['EMPPT'] * part_time_weight + df['NMGRS']
    
    # Wave 2 FTE employment
    df['EMPTOT2'] = df['EMPFT2'] + df['EMPPT2'] * part_time_weight + df['NMGRS2']
    
    # 处理关闭的商店
    # 永久关闭的商店 (STATUS2 == 3) 设置 EMPTOT2 = 0
    df.loc[df['STATUS2'] == 3, 'EMPTOT2'] = 0
    
    # 就业变化
    df['DEMP'] = df['EMPTOT2'] - df['EMPTOT']
    
    return df

def calculate_chain_dummies(df):
    """
    创建连锁店指示变量
    
    Returns:
    pd.DataFrame: 添加了连锁店虚拟变量的数据框
    """
    df = df.copy()
    
    df['bk'] = (df['CHAINr'] == 1).astype(int)      # Burger King
    df['kfc'] = (df['CHAINr'] == 2).astype(int)     # KFC
    df['roys'] = (df['CHAINr'] == 3).astype(int)    # Roy Rogers
    df['wendys'] = (df['CHAINr'] == 4).astype(int)  # Wendy's
    
    return df

def calculate_state_indicators(df):
    """
    创建州指示变量
    
    Returns:
    pd.DataFrame: 添加了州指示变量的数据框
    """
    df = df.copy()
    
    df['nj'] = df['STATEr']  # New Jersey = 1, Pennsylvania = 0
    df['pa'] = 1 - df['STATEr']  # Pennsylvania = 1, New Jersey = 0
    
    return df

def calculate_wage_gap(df):
    """
    计算工资差距变量 (GAP)
    
    Returns:
    pd.DataFrame: 添加了GAP变量的数据框
    """
    df = df.copy()
    
    df['gap'] = 0.0
    
    # 对于新泽西州且工资低于$5.05的商店
    nj_mask = df['STATEr'] == 1
    wage_low_mask = df['WAGE_ST'] < 5.05
    wage_valid_mask = df['WAGE_ST'] > 0
    
    gap_mask = nj_mask & wage_low_mask & wage_valid_mask
    df.loc[gap_mask, 'gap'] = (5.05 - df.loc[gap_mask, 'WAGE_ST']) / df.loc[gap_mask, 'WAGE_ST']
    
    return df

def calculate_meal_prices(df):
    """
    计算餐食价格
    
    Returns:
    pd.DataFrame: 添加了餐食价格变量的数据框
    """
    df = df.copy()
    
    # Wave 1餐食价格
    df['PMEAL'] = df['PSODA'] + df['PFRY'] + df['PENTREE']
    
    # Wave 2餐食价格
    df['PMEAL2'] = df['PSODA2'] + df['PFRY2'] + df['PENTREE2']
    
    return df

def calculate_full_time_percentage(df):
    """
    计算全职员工比例
    
    Returns:
    pd.DataFrame: 添加了全职员工比例变量的数据框
    """
    df = df.copy()
    
    # Wave 1全职员工比例
    df['FRACFT'] = np.where(df['EMPTOT'] > 0, 
                           (df['EMPFT'] / df['EMPTOT']) * 100, 
                           np.nan)
    
    # Wave 2全职员工比例
    df['FRACFT2'] = np.where(df['EMPTOT2'] > 0, 
                            (df['EMPFT2'] / df['EMPTOT2']) * 100, 
                            np.nan)
    
    return df

def calculate_proportional_change(df):
    """
    计算比例就业变化
    
    Returns:
    pd.DataFrame: 添加了比例变化变量的数据框
    """
    df = df.copy()
    
    # 比例就业变化: 2*(E2-E1)/(E2+E1)
    df['PCHEMPC'] = 2 * (df['EMPTOT2'] - df['EMPTOT']) / (df['EMPTOT2'] + df['EMPTOT'])
    
    # 对于关闭的商店，设置为-1
    df.loc[df['EMPTOT2'] == 0, 'PCHEMPC'] = -1
    
    return df

def create_basic_derived_variables(df):
    """
    创建所有基本衍生变量的便捷函数
    
    Returns:
    pd.DataFrame: 包含所有基本衍生变量的数据框
    """
    df = calculate_fte_employment(df)
    df = calculate_chain_dummies(df)
    df = calculate_state_indicators(df)
    df = calculate_wage_gap(df)
    df = calculate_meal_prices(df)
    df = calculate_full_time_percentage(df)
    df = calculate_proportional_change(df)
    
    # 工资变化
    df['dwage'] = df['WAGE_ST2'] - df['WAGE_ST']
    
    # 关闭指示变量
    df['CLOSED'] = (df['STATUS2'] == 3).astype(int)
    
    return df

# =============================================================================
# 样本准备函数
# =============================================================================

def create_analysis_sample(df, include_temp_closed=False):
    """
    创建分析样本
    
    Parameters:
    df (pd.DataFrame): 原始数据框
    include_temp_closed (bool): 是否包含临时关闭的商店
    
    Returns:
    pd.DataFrame: 分析样本
    """
    sample = df.copy()
    
    if not include_temp_closed:
        # 排除临时关闭的商店
        sample = sample[sample['STATUS2'] != 2]
    else:
        # 将临时关闭的商店的第二波就业设为0
        temp_closed_mask = sample['STATUS2'] == 2
        sample.loc[temp_closed_mask, 'EMPFT2'] = 0
        sample.loc[temp_closed_mask, 'EMPPT2'] = 0
        sample.loc[temp_closed_mask, 'NMGRS2'] = 0
        sample.loc[temp_closed_mask, 'EMPTOT2'] = 0
        sample.loc[temp_closed_mask, 'DEMP'] = sample.loc[temp_closed_mask, 'EMPTOT2'] - sample.loc[temp_closed_mask, 'EMPTOT']
        # 给临时关闭的商店一个虚拟的工资变化值
        sample.loc[temp_closed_mask, 'dwage'] = 0
    
    # 必须有有效的就业变化数据
    sample = sample.dropna(subset=['DEMP'])
    
    # 必须是关闭的商店或有有效工资变化数据的商店
    sample = sample[(sample['CLOSED'] == 1) | 
                   ((sample['CLOSED'] == 0) & sample['dwage'].notna())]
    
    return sample

def create_balanced_sample(df):
    """
    创建平衡样本（两波都有有效数据的商店）
    
    Returns:
    pd.DataFrame: 平衡样本
    """
    sample = df.copy()
    
    # 两波都有有效就业数据
    valid_wave1 = sample['EMPTOT'].notna()
    valid_wave2 = sample['EMPTOT2'].notna()
    
    balanced_sample = sample[valid_wave1 & valid_wave2].copy()
    
    return balanced_sample

# =============================================================================
# 统计计算函数
# =============================================================================

def calculate_mean_and_se(series):
    """
    计算均值和标准误
    
    Parameters:
    series (pd.Series or np.array): 数据序列
    
    Returns:
    tuple: (均值, 标准误, 样本量)
    """
    if isinstance(series, np.ndarray):
        # 处理numpy数组
        clean_series = series[~np.isnan(series)]
    else:
        # 处理pandas Series
        clean_series = series.dropna()
        clean_series = clean_series.values if hasattr(clean_series, 'values') else clean_series
    
    if len(clean_series) == 0:
        return np.nan, np.nan, 0
    
    mean_val = np.mean(clean_series)
    std_val = np.std(clean_series, ddof=1)  # 样本标准差
    n = len(clean_series)
    se_val = std_val / np.sqrt(n) if n > 0 else np.nan
    
    return mean_val, se_val, n

def calculate_two_sample_ttest(series1, series2):
    """
    计算两样本t检验
    
    Parameters:
    series1, series2 (pd.Series or np.array): 两个样本数据
    
    Returns:
    tuple: (t统计量, p值)
    """
    # 处理第一个序列
    if isinstance(series1, np.ndarray):
        clean1 = series1[~np.isnan(series1)]
    else:
        clean1 = series1.dropna()
        clean1 = clean1.values if hasattr(clean1, 'values') else clean1
    
    # 处理第二个序列  
    if isinstance(series2, np.ndarray):
        clean2 = series2[~np.isnan(series2)]
    else:
        clean2 = series2.dropna()
        clean2 = clean2.values if hasattr(clean2, 'values') else clean2
    
    if len(clean1) < 2 or len(clean2) < 2:
        return np.nan, np.nan
    
    # 使用等方差假设的两样本t检验
    t_stat, p_val = stats.ttest_ind(clean1, clean2, equal_var=True)
    
    return t_stat, p_val

def calculate_proportion_stats(nj_data, pa_data):
    """
    计算比例的统计量（用于二分类变量）
    
    Parameters:
    nj_data, pa_data (pd.Series): 新泽西和宾夕法尼亚的数据
    
    Returns:
    tuple: (NJ比例%, NJ标准误%, PA比例%, PA标准误%, t统计量)
    """
    n1, n2 = len(nj_data), len(pa_data)
    p1 = nj_data.sum() / n1
    p2 = pa_data.sum() / n2
    
    # 计算标准误
    se1 = np.sqrt(p1 * (1 - p1) / n1)
    se2 = np.sqrt(p2 * (1 - p2) / n2)
    
    # 计算t统计量
    pooled_p = (n1 * p1 + n2 * p2) / (n1 + n2)
    pooled_se = np.sqrt(pooled_p * (1 - pooled_p) * (1/n1 + 1/n2))
    t_stat = (p1 - p2) / pooled_se if pooled_se > 0 else 0
    
    return p1 * 100, se1 * 100, p2 * 100, se2 * 100, t_stat

def calculate_f_test_pvalue(model, control_vars):
    """
    计算控制变量联合显著性的F检验p值
    
    Parameters:
    model: statsmodels回归结果
    control_vars (list): 控制变量名称列表
    
    Returns:
    float: F检验的p值
    """
    param_names = model.params.index.tolist()
    test_vars = [var for var in control_vars if var in param_names]
    
    if not test_vars:
        return None
    
    # 创建约束矩阵
    k = len(param_names)
    num_restrictions = len(test_vars)
    R = np.zeros((num_restrictions, k))
    
    for i, var in enumerate(test_vars):
        j = param_names.index(var)
        R[i, j] = 1
    
    # 执行F检验
    f_test_result = model.f_test(R)
    return f_test_result.pvalue

# =============================================================================
# 工资计算函数
# =============================================================================

def calculate_wage_percentages(df, target_wage, wave='1'):
    """
    计算工资等于特定值的店铺百分比
    
    Parameters:
    df (pd.DataFrame): 数据框
    target_wage (float): 目标工资值
    wave (str): '1' 或 '2'
    
    Returns:
    np.array: 百分比数组
    """
    wage_col = 'WAGE_ST' if wave == '1' else 'WAGE_ST2'
    
    if target_wage == 4.25:
        if wave == '1':
            # Wave 1：对于所有商店，估算员工中拿$4.25工资的比例
            # 如果起始工资是$4.25，使用PCTAFF值（如果可用）
            # 如果起始工资高于$4.25但较低，可能仍有部分员工拿$4.25
            # 如果起始工资远高于$4.25，则员工中拿$4.25的比例为0
            wage_pct = np.where(
                df[wage_col] == 4.25,
                np.where(df['PCTAFF'].notna(), df['PCTAFF'], 100.0),
                np.where(
                    (df[wage_col] > 4.25) & (df[wage_col] <= 4.75),
                    # 对于起始工资稍高于$4.25的商店，假设有一定比例员工仍拿$4.25
                    np.maximum(0, 100.0 - 2 * (df[wage_col] - 4.25) * 100),
                    0.0
                )
            )
        else:
            # Wave 2：新泽西州最低工资已提高到$5.05，理论上没有员工拿$4.25
            # 但宾夕法尼亚州仍可能有员工拿$4.25
            wage_pct = np.where(
                (df['nj'] == 0) & (df[wage_col] <= 4.25),
                100.0,
                np.where(
                    (df['nj'] == 0) & (df[wage_col] > 4.25) & (df[wage_col] <= 4.75),
                    np.maximum(0, 100.0 - 2 * (df[wage_col] - 4.25) * 100),
                    0.0
                )
            )
    
    elif target_wage == 5.05:
        if wave == '1':
            # Wave 1几乎没有$5.05的工资
            wage_pct = np.where(df[wage_col] >= 5.05, 100.0, 0.0)
        else:
            # Wave 2：主要针对新泽西州，根据起始工资推断
            wage_pct = np.where(
                df[wage_col] == 5.05,
                100.0,
                np.where(
                    (df[wage_col] >= 4.25) & (df[wage_col] < 5.05) & (df['nj'] == 1),
                    # 新泽西州工资在$4.25-$5.05之间的，假设大部分员工被提高到$5.05
                    100.0 - np.where(df['PCTAFF'].notna(), df['PCTAFF'] * 0.2, 20.0),
                    0.0
                )
            )
    
    else:
        # 其他工资值，简单检查起始工资
        wage_pct = np.where(df[wage_col] == target_wage, 100.0, 0.0)
    
    return wage_pct

# =============================================================================
# 输出和格式化函数
# =============================================================================

def format_coefficient(coef, se, decimal_places=2):
    """
    格式化系数和标准误
    
    Parameters:
    coef (float): 系数
    se (float): 标准误
    decimal_places (int): 小数位数
    
    Returns:
    str: 格式化的字符串
    """
    if pd.isna(coef) or pd.isna(se):
        return ""
    
    format_str = f"{{:.{decimal_places}f}}"
    return f"{format_str.format(coef)} ({format_str.format(se)})"

def format_number(num, decimal_places=2):
    """
    格式化数值
    
    Parameters:
    num (float): 数值
    decimal_places (int): 小数位数
    
    Returns:
    str: 格式化的字符串
    """
    if pd.isna(num):
        return ""
    
    format_str = f"{{:.{decimal_places}f}}"
    return format_str.format(num)

def save_output_to_file(content, output_path):
    """
    保存输出到文件
    
    Parameters:
    content (str): 要保存的内容
    output_path (str): 输出文件路径
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"结果已保存到: {output_path}")
    except Exception as e:
        print(f"保存文件时出错: {e}")

def get_output_path(script_file, filename='output.md'):
    """
    获取输出文件的路径
    
    Parameters:
    script_file (str): 脚本文件的__file__变量
    filename (str): 输出文件名
    
    Returns:
    str: 输出文件的完整路径
    """
    script_dir = os.path.dirname(os.path.abspath(script_file))
    return os.path.join(script_dir, filename)

# =============================================================================
# 数据子集选择函数
# =============================================================================

def filter_by_state(df, state='nj'):
    """
    按州筛选数据
    
    Parameters:
    df (pd.DataFrame): 数据框
    state (str): 'nj' 或 'pa'
    
    Returns:
    pd.DataFrame: 筛选后的数据框
    """
    if state.lower() == 'nj':
        return df[df['nj'] == 1]
    elif state.lower() == 'pa':
        return df[df['nj'] == 0]
    else:
        raise ValueError("state必须是'nj'或'pa'")

def filter_by_chain(df, chain):
    """
    按连锁店筛选数据
    
    Parameters:
    df (pd.DataFrame): 数据框
    chain (str): 'bk', 'kfc', 'roys', 或 'wendys'
    
    Returns:
    pd.DataFrame: 筛选后的数据框
    """
    chain_mapping = {
        'bk': 1,
        'kfc': 2,
        'roys': 3,
        'wendys': 4
    }
    
    if chain.lower() not in chain_mapping:
        raise ValueError("chain必须是'bk', 'kfc', 'roys', 或'wendys'")
    
    chain_id = chain_mapping[chain.lower()]
    return df[df['CHAINr'] == chain_id]

def create_wage_groups(df):
    """
    为新泽西州店铺创建工资组指示变量
    
    Returns:
    pd.DataFrame: 添加了工资组变量的数据框
    """
    df = df.copy()
    
    # 为新泽西州店铺创建工资组
    df['NJ_wage_425'] = ((df['STATEr'] == 1) & (df['WAGE_ST'] == 4.25)).astype(int)
    df['NJ_wage_426_499'] = ((df['STATEr'] == 1) & 
                           (df['WAGE_ST'] >= 4.26) & 
                           (df['WAGE_ST'] <= 4.99)).astype(int)
    df['NJ_wage_500plus'] = ((df['STATEr'] == 1) & (df['WAGE_ST'] >= 5.00)).astype(int)
    
    return df

# =============================================================================
# 便捷的完整数据处理函数
# =============================================================================

def load_and_prepare_data(method='whitespace', include_temp_closed=False):
    """
    完整的数据加载和预处理流程
    
    Parameters:
    method (str): 数据读取方法
    include_temp_closed (bool): 是否包含临时关闭的商店
    
    Returns:
    pd.DataFrame: 完全处理好的数据框
    """
    # 读取数据
    df = read_data(method=method)
    
    # 创建基本衍生变量
    df = create_basic_derived_variables(df)
    
    # 创建工资组
    df = create_wage_groups(df)
    
    # 创建分析样本
    df = create_analysis_sample(df, include_temp_closed=include_temp_closed)
    
    return df

# =============================================================================
# 数据验证函数
# =============================================================================

def validate_data(df, verbose=True):
    """
    验证数据的基本特征
    
    Parameters:
    df (pd.DataFrame): 数据框
    verbose (bool): 是否打印详细信息
    
    Returns:
    dict: 验证结果
    """
    results = {}
    
    # 基本信息
    results['total_observations'] = len(df)
    results['nj_observations'] = (df['nj'] == 1).sum()
    results['pa_observations'] = (df['nj'] == 0).sum()
    
    # 连锁店分布
    results['chain_distribution'] = df['CHAINr'].value_counts().to_dict()
    
    # 关闭商店统计
    results['permanently_closed'] = (df['STATUS2'] == 3).sum()
    results['temporarily_closed'] = (df['STATUS2'] == 2).sum()
    
    # 缺失值统计
    results['missing_values'] = df.isnull().sum().to_dict()
    
    if verbose:
        print("数据验证结果:")
        print(f"总观测数: {results['total_observations']}")
        print(f"新泽西州: {results['nj_observations']}")
        print(f"宾夕法尼亚州: {results['pa_observations']}")
        print(f"永久关闭: {results['permanently_closed']}")
        print(f"临时关闭: {results['temporarily_closed']}")
        print("\n连锁店分布:")
        for chain_id, count in results['chain_distribution'].items():
            chain_names = {1: 'Burger King', 2: 'KFC', 3: 'Roy Rogers', 4: "Wendy's"}
            print(f"  {chain_names.get(chain_id, f'Unknown({chain_id})')}: {count}")
    
    return results 