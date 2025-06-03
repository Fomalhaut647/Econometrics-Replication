#!/usr/bin/env python3
"""
Table 2 Replication: Means of Key Variables
Card and Krueger (1994) - Minimum Wages and Employment
"""

import pandas as pd
import numpy as np
from scipy import stats
import os
import sys

def read_data():
    """
    读取 public.dat 数据文件
    """
    # 获取脚本所在目录的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 构建数据文件的绝对路径（相对于脚本位置）
    data_file = os.path.join(script_dir, '..', 'data', 'public.dat')
    
    # 根据 codebook 定义列名
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
        # 检查数据文件是否存在
        if not os.path.exists(data_file):
            print(f"Data file not found: {data_file}")
            print(f"Script directory: {script_dir}")
            return None
            
        # 读取数据
        df = pd.read_csv(data_file, sep=r'\s+', names=columns, header=None)
        
        # 转换为数值类型
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    except Exception as e:
        print(f"Error reading data file: {e}")
        print(f"Attempted to read from: {data_file}")
        return None

def calculate_derived_variables(df):
    """
    计算衍生变量
    """
    # 全职等效就业 (FTE employment)
    df['EMPTOT'] = df['EMPFT'] + df['EMPPT'] * 0.5 + df['NMGRS']
    df['EMPTOT2'] = df['EMPFT2'] + df['EMPPT2'] * 0.5 + df['NMGRS2']
    
    # 处理第二波调查中关闭的商店
    # 永久关闭的商店 (STATUS2 == 3) 设置 EMPTOT2 = 0
    df.loc[df['STATUS2'] == 3, 'EMPTOT2'] = 0
    
    # 暂时关闭的商店 (STATUS2 == 2, 4, 5) 设置为缺失值
    df.loc[df['STATUS2'].isin([2, 4, 5]), 'EMPTOT2'] = np.nan
    
    # 全职员工比例
    df['FRACFT'] = np.where(df['EMPTOT'] > 0, 
                           (df['EMPFT'] / df['EMPTOT']) * 100, 
                           np.nan)
    df['FRACFT2'] = np.where(df['EMPTOT2'] > 0, 
                            (df['EMPFT2'] / df['EMPTOT2']) * 100, 
                            np.nan)
    
    # 餐食价格
    df['PMEAL'] = df['PSODA'] + df['PFRY'] + df['PENTREE']
    df['PMEAL2'] = df['PSODA2'] + df['PFRY2'] + df['PENTREE2']
    
    # 连锁店指示变量
    df['bk'] = (df['CHAINr'] == 1).astype(int)
    df['kfc'] = (df['CHAINr'] == 2).astype(int)
    df['roys'] = (df['CHAINr'] == 3).astype(int)
    df['wendys'] = (df['CHAINr'] == 4).astype(int)
    
    # 州指示变量 (1=NJ, 0=PA)
    df['nj'] = df['STATEr']
    
    return df

def calculate_wage_percentages(df, wave='1'):
    """
    计算工资等于特定值的店铺百分比
    根据 table_2.md 的要求：计算每个店铺员工中特定工资的百分比，然后取平均
    """
    if wave == '1':
        wage_col = 'WAGE_ST'
    else:
        wage_col = 'WAGE_ST2'
    
    # 对于起始工资，如果店铺的起始工资等于目标工资，则为100%，否则为0%
    wage_425_pct = np.where(df[wage_col] == 4.25, 100.0, 0.0)
    
    # 工资等于 5.05 的百分比 (只对 Wave 2)
    wage_505_pct = None
    if wave == '2':
        wage_505_pct = np.where(df[wage_col] == 5.05, 100.0, 0.0)
    
    return wage_425_pct, wage_505_pct

def calculate_proportion_stats(nj_data, pa_data):
    """
    计算比例的统计量（用于二分类变量）
    """
    n1, n2 = len(nj_data), len(pa_data)
    p1 = nj_data.sum() / n1
    p2 = pa_data.sum() / n2
    
    # 计算标准误
    se1 = np.sqrt(p1 * (1 - p1) / n1)
    se2 = np.sqrt(p2 * (1 - p2) / n2)
    
    # 计算 t 统计量
    pooled_p = (n1 * p1 + n2 * p2) / (n1 + n2)
    pooled_se = np.sqrt(pooled_p * (1 - pooled_p) * (1/n1 + 1/n2))
    t_stat = (p1 - p2) / pooled_se if pooled_se > 0 else 0
    
    return p1 * 100, se1 * 100, p2 * 100, se2 * 100, t_stat

def calculate_stats_by_state(df, var_name, nj_data, pa_data):
    """
    计算按州分组的统计量：均值、标准误、t统计量
    """
    # 转换为 pandas Series 如果输入是 numpy 数组
    if isinstance(nj_data, np.ndarray):
        nj_data = pd.Series(nj_data)
    if isinstance(pa_data, np.ndarray):
        pa_data = pd.Series(pa_data)
    
    # 去除缺失值
    nj_clean = nj_data.dropna()
    pa_clean = pa_data.dropna()
    
    if len(nj_clean) == 0 or len(pa_clean) == 0:
        return np.nan, np.nan, np.nan, np.nan, np.nan
    
    # 计算均值
    nj_mean = nj_clean.mean()
    pa_mean = pa_clean.mean()
    
    # 计算标准误
    nj_se = nj_clean.std(ddof=1) / np.sqrt(len(nj_clean))  # 使用样本标准差
    pa_se = pa_clean.std(ddof=1) / np.sqrt(len(pa_clean))  # 使用样本标准差
    
    # 计算 t 统计量 (两样本 t 检验)
    pooled_var = ((len(nj_clean) - 1) * nj_clean.var(ddof=1) + (len(pa_clean) - 1) * pa_clean.var(ddof=1)) / (len(nj_clean) + len(pa_clean) - 2)
    pooled_se = np.sqrt(pooled_var * (1/len(nj_clean) + 1/len(pa_clean)))
    t_stat = (nj_mean - pa_mean) / pooled_se if pooled_se > 0 else np.nan
    
    return nj_mean, nj_se, pa_mean, pa_se, t_stat

def print_table_2(df, output_file=None):
    """
    打印 Table 2 格式的结果
    """
    if output_file:
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = output_buffer = io.StringIO()
    
    print("**TABLE 2-MEANS OF KEY VARIABLES**\n")
    print("| Variable                          | NJ           | PA           | $t^{a}$   |")
    print("| :-------------------------------- | :----------- | :----------- | :-------- |")
    
    # 第一部分：店铺类型分布
    print("| **1. Distribution of Store Types (percentages):** |              |              |           |")
    
    # 按州分组
    nj_data = df[df['nj'] == 1]
    pa_data = df[df['nj'] == 0]
    
    # a. Burger King
    nj_bk_pct, nj_bk_se, pa_bk_pct, pa_bk_se, t_bk = calculate_proportion_stats(nj_data['bk'], pa_data['bk'])
    print(f"| a. Burger King                    | {nj_bk_pct:.1f}         | {pa_bk_pct:.1f}         | {t_bk:.1f}      |")
    
    # b. KFC
    nj_kfc_pct, nj_kfc_se, pa_kfc_pct, pa_kfc_se, t_kfc = calculate_proportion_stats(nj_data['kfc'], pa_data['kfc'])
    print(f"| b. KFC                            | {nj_kfc_pct:.1f}         | {pa_kfc_pct:.1f}         | {t_kfc:.1f}       |")
    
    # c. Roy Rogers
    nj_roys_pct, nj_roys_se, pa_roys_pct, pa_roys_se, t_roys = calculate_proportion_stats(nj_data['roys'], pa_data['roys'])
    print(f"| c. Roy Rogers                     | {nj_roys_pct:.1f}         | {pa_roys_pct:.1f}         | {t_roys:.1f}       |")
    
    # d. Wendy's
    nj_wendys_pct, nj_wendys_se, pa_wendys_pct, pa_wendys_se, t_wendys = calculate_proportion_stats(nj_data['wendys'], pa_data['wendys'])
    print(f"| d. Wendy's                        | {nj_wendys_pct:.1f}         | {pa_wendys_pct:.1f}         | {t_wendys:.1f}      |")
    
    # e. Company-owned
    nj_co_pct, nj_co_se, pa_co_pct, pa_co_se, t_co = calculate_proportion_stats(nj_data['CO_OWNED'], pa_data['CO_OWNED'])
    print(f"| e. Company-owned                  | {nj_co_pct:.1f}         | {pa_co_pct:.1f}         | {t_co:.1f}      |")
    
    # 第二部分：Wave 1 均值
    print("| **2. Means in Wave 1:** |              |              |           |")
    
    # a. FTE employment
    nj_mean, nj_se, pa_mean, pa_se, t_stat = calculate_stats_by_state(df, 'EMPTOT', nj_data['EMPTOT'], pa_data['EMPTOT'])
    print(f"| a. FTE employment                 | {nj_mean:.1f} ({nj_se:.2f})  | {pa_mean:.1f} ({pa_se:.2f})  | {t_stat:.1f}      |")
    
    # b. Percentage full-time employees
    nj_mean, nj_se, pa_mean, pa_se, t_stat = calculate_stats_by_state(df, 'FRACFT', nj_data['FRACFT'], pa_data['FRACFT'])
    print(f"| b. Percentage full-time employees | {nj_mean:.1f} ({nj_se:.1f})   | {pa_mean:.1f} ({pa_se:.1f})   | {t_stat:.1f}      |")
    
    # c. Starting wage
    nj_mean, nj_se, pa_mean, pa_se, t_stat = calculate_stats_by_state(df, 'WAGE_ST', nj_data['WAGE_ST'], pa_data['WAGE_ST'])
    print(f"| c. Starting wage                  | {nj_mean:.2f} ({nj_se:.2f})  | {pa_mean:.2f} ({pa_se:.2f})  | {t_stat:.1f}      |")
    
    # d. Wage=$4.25 (percentage)
    wage_425_pct_1, _ = calculate_wage_percentages(df, wave='1')
    nj_425_pct = wage_425_pct_1[df['nj'] == 1]
    pa_425_pct = wage_425_pct_1[df['nj'] == 0]
    nj_mean, nj_se, pa_mean, pa_se, t_stat = calculate_stats_by_state(df, 'wage_425', nj_425_pct, pa_425_pct)
    print(f"| d. $Wage=\\$4.25$ (percentage)    | {nj_mean:.1f} ({nj_se:.1f})   | {pa_mean:.1f} ({pa_se:.1f})   | {t_stat:.1f}      |")
    
    # e. Price of full meal
    nj_mean, nj_se, pa_mean, pa_se, t_stat = calculate_stats_by_state(df, 'PMEAL', nj_data['PMEAL'], pa_data['PMEAL'])
    print(f"| e. Price of full meal             | {nj_mean:.2f} ({nj_se:.2f})  | {pa_mean:.2f} ({pa_se:.2f})  | {t_stat:.1f}       |")
    
    # f. Hours open (weekday)
    nj_mean, nj_se, pa_mean, pa_se, t_stat = calculate_stats_by_state(df, 'HRSOPEN', nj_data['HRSOPEN'], pa_data['HRSOPEN'])
    print(f"| f. Hours open (weekday)           | {nj_mean:.1f} ({nj_se:.1f})   | {pa_mean:.1f} ({pa_se:.1f})   | {t_stat:.1f}      |")
    
    # g. Recruiting bonus
    nj_bonus_pct, nj_bonus_se, pa_bonus_pct, pa_bonus_se, t_bonus = calculate_proportion_stats(nj_data['BONUS'], pa_data['BONUS'])
    print(f"| g. Recruiting bonus               | {nj_bonus_pct:.1f} ({nj_bonus_se:.1f})   | {pa_bonus_pct:.1f} ({pa_bonus_se:.1f})   | {t_bonus:.1f}      |")
    
    # 第三部分：Wave 2 均值
    print("| **3. Means in Wave 2:** |              |              |           |")
    
    # 过滤掉 STATUS2 缺失的观测
    df_wave2 = df[df['STATUS2'].notna()].copy()
    nj_data_2 = df_wave2[df_wave2['nj'] == 1]
    pa_data_2 = df_wave2[df_wave2['nj'] == 0]
    
    # a. FTE employment
    nj_mean, nj_se, pa_mean, pa_se, t_stat = calculate_stats_by_state(df_wave2, 'EMPTOT2', nj_data_2['EMPTOT2'], pa_data_2['EMPTOT2'])
    print(f"| a. FTE employment                 | {nj_mean:.1f} ({nj_se:.2f})  | {pa_mean:.1f} ({pa_se:.2f})  | {t_stat:.1f}      |")
    
    # b. Percentage full-time employees
    nj_mean, nj_se, pa_mean, pa_se, t_stat = calculate_stats_by_state(df_wave2, 'FRACFT2', nj_data_2['FRACFT2'], pa_data_2['FRACFT2'])
    print(f"| b. Percentage full-time employees | {nj_mean:.1f} ({nj_se:.1f})   | {pa_mean:.1f} ({pa_se:.1f})   | {t_stat:.1f}       |")
    
    # c. Starting wage
    nj_mean, nj_se, pa_mean, pa_se, t_stat = calculate_stats_by_state(df_wave2, 'WAGE_ST2', nj_data_2['WAGE_ST2'], pa_data_2['WAGE_ST2'])
    print(f"| c. Starting wage                  | {nj_mean:.2f} ({nj_se:.2f})  | {pa_mean:.2f} ({pa_se:.2f})  | {t_stat:.1f}      |")
    
    # d. Wage=$4.25 (percentage)
    wage_425_pct_2, wage_505_pct_2 = calculate_wage_percentages(df_wave2, wave='2')
    nj_425_pct_2 = wage_425_pct_2[df_wave2['nj'] == 1]
    pa_425_pct_2 = wage_425_pct_2[df_wave2['nj'] == 0]
    nj_mean, nj_se, pa_mean, pa_se, t_stat = calculate_stats_by_state(df_wave2, 'wage_425_2', nj_425_pct_2, pa_425_pct_2)
    print(f"| d. $Wage=\\$4.25$ (percentage)    | {nj_mean:.1f}          | {pa_mean:.1f} ({pa_se:.1f})   |           |")
    
    # e. Wage=$5.05 (percentage)
    nj_505_pct_2 = wage_505_pct_2[df_wave2['nj'] == 1]
    pa_505_pct_2 = wage_505_pct_2[df_wave2['nj'] == 0]
    nj_mean, nj_se, pa_mean, pa_se, t_stat = calculate_stats_by_state(df_wave2, 'wage_505_2', nj_505_pct_2, pa_505_pct_2)
    print(f"| e. $Wage=\\$5.05$ (percentage)    | {nj_mean:.1f} ({nj_se:.1f})   | {pa_mean:.1f} ({pa_se:.1f})    | {t_stat:.1f}      |")
    
    # f. Price of full meal
    nj_mean, nj_se, pa_mean, pa_se, t_stat = calculate_stats_by_state(df_wave2, 'PMEAL2', nj_data_2['PMEAL2'], pa_data_2['PMEAL2'])
    print(f"| f. Price of full meal             | {nj_mean:.2f} ({nj_se:.2f})  | {pa_mean:.2f} ({pa_se:.2f})  | {t_stat:.1f}       |")
    
    # g. Hours open (weekday)
    nj_mean, nj_se, pa_mean, pa_se, t_stat = calculate_stats_by_state(df_wave2, 'HRSOPEN2', nj_data_2['HRSOPEN2'], pa_data_2['HRSOPEN2'])
    print(f"| g. Hours open (weekday)           | {nj_mean:.1f} ({nj_se:.1f})   | {pa_mean:.1f} ({pa_se:.1f})   | {t_stat:.1f}      |")
    
    # h. Recruiting bonus
    nj_special_pct, nj_special_se, pa_special_pct, pa_special_se, t_special = calculate_proportion_stats(nj_data_2['SPECIAL2'], pa_data_2['SPECIAL2'])
    print(f"| h. Recruiting bonus               | {nj_special_pct:.1f} ({nj_special_se:.1f})   | {pa_special_pct:.1f} ({pa_special_se:.1f})   | {t_special:.1f}      |")
    
    print("\n*Notes: See text for definitions. Standard errors are given in parentheses.")
    print("<sup>a</sup> Test of equality of means in New Jersey and Pennsylvania.*")

    if output_file:
        output_content = output_buffer.getvalue()
        sys.stdout = old_stdout
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output_content)
        print(f"Results saved to {output_file}")
        return output_content
    
    return None

def main():
    """
    主函数
    """
    print("Replication of Card and Krueger (1994) Table 2")
    print("=" * 60)
    
    # 读取数据
    df = read_data()
    if df is None:
        print("Failed to read data file")
        return
    
    print(f"Data loaded successfully: {len(df)} observations")
    
    # 计算衍生变量
    df = calculate_derived_variables(df)
    
    # 生成并保存表格到文件
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, 'output.md')
    
    # 打印 Table 2 并保存到文件
    print_table_2(df, output_path)

if __name__ == "__main__":
    main() 