#!/usr/bin/env python3
"""
Table 2 Replication: Means of Key Variables
Card and Krueger (1994) - Minimum Wages and Employment
"""

import sys
import os

# 添加根目录到Python路径以导入utility模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utility as util

def calculate_stats_by_state(df, var_name, nj_data, pa_data):
    """
    计算按州分组的统计量：均值、标准误、t统计量
    这是table_2特有的统计计算方法
    """
    # 使用utility模块的函数计算基本统计量
    nj_mean, nj_se, n1 = util.calculate_mean_and_se(nj_data)
    pa_mean, pa_se, n2 = util.calculate_mean_and_se(pa_data)
    
    if n1 == 0 or n2 == 0:
        return nj_mean, nj_se, pa_mean, pa_se, float('nan')
    
    # 计算t统计量 (两样本t检验)
    t_stat, _ = util.calculate_two_sample_ttest(nj_data, pa_data)
    
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
    nj_data = util.filter_by_state(df, 'nj')
    pa_data = util.filter_by_state(df, 'pa')
    
    # a. Burger King
    nj_bk_pct, nj_bk_se, pa_bk_pct, pa_bk_se, t_bk = util.calculate_proportion_stats(nj_data['bk'], pa_data['bk'])
    print(f"| a. Burger King                    | {nj_bk_pct:.1f}         | {pa_bk_pct:.1f}         | {t_bk:.1f}      |")
    
    # b. KFC
    nj_kfc_pct, nj_kfc_se, pa_kfc_pct, pa_kfc_se, t_kfc = util.calculate_proportion_stats(nj_data['kfc'], pa_data['kfc'])
    print(f"| b. KFC                            | {nj_kfc_pct:.1f}         | {pa_kfc_pct:.1f}         | {t_kfc:.1f}       |")
    
    # c. Roy Rogers
    nj_roys_pct, nj_roys_se, pa_roys_pct, pa_roys_se, t_roys = util.calculate_proportion_stats(nj_data['roys'], pa_data['roys'])
    print(f"| c. Roy Rogers                     | {nj_roys_pct:.1f}         | {pa_roys_pct:.1f}         | {t_roys:.1f}       |")
    
    # d. Wendy's
    nj_wendys_pct, nj_wendys_se, pa_wendys_pct, pa_wendys_se, t_wendys = util.calculate_proportion_stats(nj_data['wendys'], pa_data['wendys'])
    print(f"| d. Wendy's                        | {nj_wendys_pct:.1f}         | {pa_wendys_pct:.1f}         | {t_wendys:.1f}      |")
    
    # e. Company-owned
    nj_co_pct, nj_co_se, pa_co_pct, pa_co_se, t_co = util.calculate_proportion_stats(nj_data['CO_OWNED'], pa_data['CO_OWNED'])
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
    wage_425_pct_1 = util.calculate_wage_percentages(df, 4.25, wave='1')
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
    nj_bonus_pct, nj_bonus_se, pa_bonus_pct, pa_bonus_se, t_bonus = util.calculate_proportion_stats(nj_data['BONUS'], pa_data['BONUS'])
    print(f"| g. Recruiting bonus               | {nj_bonus_pct:.1f} ({nj_bonus_se:.1f})   | {pa_bonus_pct:.1f} ({pa_bonus_se:.1f})   | {t_bonus:.1f}      |")
    
    # 第三部分：Wave 2 均值
    print("| **3. Means in Wave 2:** |              |              |           |")
    
    # 过滤掉 STATUS2 缺失的观测
    df_wave2 = df[df['STATUS2'].notna()].copy()
    nj_data_2 = util.filter_by_state(df_wave2, 'nj')
    pa_data_2 = util.filter_by_state(df_wave2, 'pa')
    
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
    wage_425_pct_2 = util.calculate_wage_percentages(df_wave2, 4.25, wave='2')
    nj_425_pct_2 = wage_425_pct_2[df_wave2['nj'] == 1]
    pa_425_pct_2 = wage_425_pct_2[df_wave2['nj'] == 0]
    nj_mean, nj_se, pa_mean, pa_se, t_stat = calculate_stats_by_state(df_wave2, 'wage_425_2', nj_425_pct_2, pa_425_pct_2)
    print(f"| d. $Wage=\\$4.25$ (percentage)    | {nj_mean:.1f}          | {pa_mean:.1f} ({pa_se:.1f})   |           |")
    
    # e. Wage=$5.05 (percentage)
    wage_505_pct_2 = util.calculate_wage_percentages(df_wave2, 5.05, wave='2')
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
    nj_special_pct, nj_special_se, pa_special_pct, pa_special_se, t_special = util.calculate_proportion_stats(nj_data_2['SPECIAL2'], pa_data_2['SPECIAL2'])
    print(f"| h. Recruiting bonus               | {nj_special_pct:.1f} ({nj_special_se:.1f})   | {pa_special_pct:.1f} ({pa_special_se:.1f})   | {t_special:.1f}      |")
    
    print("\n*Notes: See text for definitions. Standard errors are given in parentheses.")
    print("<sup>a</sup> Test of equality of means in New Jersey and Pennsylvania.*")

    if output_file:
        output_content = output_buffer.getvalue()
        sys.stdout = old_stdout
        util.save_output_to_file(output_content, output_file)
        return output_content
    
    return None

def main():
    """
    主函数
    """
    print("Replication of Card and Krueger (1994) Table 2")
    print("=" * 60)
    
    # 使用utility模块读取和处理数据
    df = util.read_data()
    print(f"Data loaded successfully: {len(df)} observations")
    
    # 使用utility模块创建衍生变量
    df = util.create_basic_derived_variables(df)
    
    # 生成并保存表格到文件
    output_path = util.get_output_path(__file__)
    
    # 打印 Table 2 并保存到文件
    print_table_2(df, output_path)

if __name__ == "__main__":
    main() 