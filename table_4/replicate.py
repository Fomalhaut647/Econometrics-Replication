#!/usr/bin/env python3
"""
Card 和 Krueger (1994) 论文中表格4的复制脚本
"最低工资与就业：新泽西州和宾夕法尼亚州快餐业的案例研究"

此脚本复制了就业变化简化式模型。
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats
import os

def load_data():
    """
    从 public.dat 文件加载并解析 NJ-PA 数据
    """
    # 获取脚本目录并构建数据文件的路径
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

    # 转换为数值类型，将'.'视作 NaN
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df

def create_variables(df):
    """
    创建表格4分析所需的派生变量
    """
    # 计算全职等效就业人数 (FTE) (包括经理：全职 + 0.5 * 兼职 + 经理)
    df['EMPTOT'] = df['EMPPT'] * 0.5 + df['EMPFT'] + df['NMGRS']
    df['EMPTOT2'] = df['EMPPT2'] * 0.5 + df['EMPFT2'] + df['NMGRS2']

    # 全职等效就业人数 (FTE) 的变化 (因变量)
    df['DEMP'] = df['EMPTOT2'] - df['EMPTOT']

    # 工资变化
    df['dwage'] = df['WAGE_ST2'] - df['WAGE_ST']

    # 新泽西州虚拟变量
    df['nj'] = df['STATEr']

    # 创建 GAP 变量 (使用小写以匹配原文)
    df['gap'] = 0.0
    nj_mask = df['STATEr'] == 1  # 新泽西州的商店
    wage_low_mask = df['WAGE_ST'] < 5.05  # 工资低于新的最低工资
    wage_valid_mask = df['WAGE_ST'] > 0  # 有效的工资数据

    # 对于工资有效且低于 $5.05 的新泽西州商店，计算比例差距
    gap_mask = nj_mask & wage_low_mask & wage_valid_mask
    df.loc[gap_mask, 'gap'] = (5.05 - df.loc[gap_mask, 'WAGE_ST']) / df.loc[gap_mask, 'WAGE_ST']

    # 创建连锁店虚拟变量 (使用小写以匹配原文)
    df['bk'] = (df['CHAINr'] == 1).astype(int)      # Burger King (汉堡王)
    df['kfc'] = (df['CHAINr'] == 2).astype(int)     # KFC (肯德基)
    df['roys'] = (df['CHAINr'] == 3).astype(int)    # Roy Rogers
    # Wendy's (CHAINr == 4) 是被省略的基准类别

    # 商店关闭指示变量
    df['CLOSED'] = (df['STATUS2'] == 3).astype(int)

    return df

def create_analysis_sample(df):
    """
    按照原始方法创建分析样本
    """
    # 按照原始逻辑创建子集：
    # 包括已关闭的商店 或 未关闭但具有有效工资变化数据的商店
    c1 = df.copy()
    c1 = c1.dropna(subset=['DEMP'])  # 必须有有效的就业变化数据
    c1 = c1[(c1['CLOSED'] == 1) | ((c1['CLOSED'] == 0) & c1['dwage'].notna())]

    return c1

def run_regressions(df):
    """
    运行表格4的五个回归模型
    """
    results = {}

    # 模型 (i): DEMP ~ NJ
    model1 = smf.ols('DEMP ~ nj', data=df).fit()
    results['model1'] = model1

    # 模型 (ii): DEMP ~ NJ + 连锁店和所有权控制变量
    model2 = smf.ols('DEMP ~ nj + bk + kfc + roys + CO_OWNED', data=df).fit()
    results['model2'] = model2

    # 模型 (iii): DEMP ~ GAP
    model3 = smf.ols('DEMP ~ gap', data=df).fit()
    results['model3'] = model3

    # 模型 (iv): DEMP ~ GAP + 连锁店和所有权控制变量
    model4 = smf.ols('DEMP ~ gap + bk + kfc + roys + CO_OWNED', data=df).fit()
    results['model4'] = model4

    # 模型 (v): DEMP ~ GAP + 连锁店/所有权 + 区域控制变量
    model5 = smf.ols('DEMP ~ gap + bk + kfc + roys + CO_OWNED + CENTRALJ + SOUTHJ + PA1 + PA2', data=df).fit()
    results['model5'] = model5

    return results

def calculate_f_test_pvalue(model, control_vars):
    """
    计算控制变量联合显著性的 F 检验 p 值
    """
    # 从模型中获取参数名称
    param_names = model.params.index.tolist()

    # 找出模型中实际包含的控制变量
    test_vars = [var for var in control_vars if var in param_names]

    if not test_vars:
        return None

    # 为 F 检验创建约束矩阵
    k = len(param_names)
    num_restrictions = len(test_vars)
    R = np.zeros((num_restrictions, k))

    for i, var in enumerate(test_vars):
        j = param_names.index(var)
        R[i, j] = 1

    # 执行 F 检验
    f_stat = model.f_test(R).fvalue
    p_value = model.f_test(R).pvalue

    return p_value

def format_table(results, sample_size):
    """
    将结果格式化为与标准表格4布局完全一致
    Formats the results to exactly match the layout of the standard Table 4
    """
    # 首先是表格标题
    # First, the table title
    title = "**TABLE 4-REDUCED-FORM MODELS FOR CHANGE IN EMPLOYMENT**"

    # 提取系数和标准误
    # Extract coefficients and standard errors
    def get_coef_se(model, var):
        if var in model.params.index:
            coef = model.params[var]
            se = model.bse[var]
            return coef, se
        return None, None

    # 初始化表格数据
    # Initialize table data
    table_data = []

    # 第1行: 新泽西州虚拟变量
    # Row 1: New Jersey dummy
    row1 = ['1. New Jersey dummy']
    nj_coef1, nj_se1 = get_coef_se(results['model1'], 'nj')
    nj_coef2, nj_se2 = get_coef_se(results['model2'], 'nj')

    row1.extend([
        f"{nj_coef1:.2f} ({nj_se1:.2f})" if nj_coef1 is not None else "",
        f"{nj_coef2:.2f} ({nj_se2:.2f})" if nj_coef2 is not None else "",
        "", "", ""
    ])
    table_data.append(row1)

    # 第2行: 初始工资差距
    # Row 2: Initial wage gap
    row2 = ['2. Initial wage gap<sup>a</sup>']
    row2.extend(["", ""])  # 模型 (i) 和 (ii) 中没有差距变量 # No gap variable in Models (i) and (ii)

    gap_coef3, gap_se3 = get_coef_se(results['model3'], 'gap')
    gap_coef4, gap_se4 = get_coef_se(results['model4'], 'gap')
    gap_coef5, gap_se5 = get_coef_se(results['model5'], 'gap')

    row2.extend([
        f"{gap_coef3:.2f} ({gap_se3:.2f})" if gap_coef3 is not None else "",
        f"{gap_coef4:.2f} ({gap_se4:.2f})" if gap_coef4 is not None else "",
        f"{gap_coef5:.2f} ({gap_se5:.2f})" if gap_coef5 is not None else ""
    ])
    table_data.append(row2)

    # 第3行: 连锁店和所有权控制变量
    # Row 3: Controls for chain and ownership
    row3 = ['3. Controls for chain and ownership<sup>b</sup>']
    row3.extend(['no', 'yes', 'no', 'yes', 'yes']) # Changed to English
    table_data.append(row3)

    # 第4行: 区域控制变量
    # Row 4: Controls for region
    row4 = ['4. Controls for region<sup>c</sup>']
    row4.extend(['no', 'no', 'no', 'no', 'yes']) # Changed to English
    table_data.append(row4)

    # 第5行: 回归标准误
    # Row 5: Standard error of regression
    row5 = ['5. Standard error of regression']
    row5.extend([
        f"{results['model1'].scale**0.5:.2f}",
        f"{results['model2'].scale**0.5:.2f}",
        f"{results['model3'].scale**0.5:.2f}",
        f"{results['model4'].scale**0.5:.2f}",
        f"{results['model5'].scale**0.5:.2f}"
    ])
    table_data.append(row5)

    # 第6行: 控制变量的概率值
    # Row 6: Probability value for controls
    row6 = ['6. Probability value for controls<sup>d</sup>']
    row6.append("")  # 模型 (i) 没有控制变量 # Model (i) has no control variables

    # 模型 (ii) 的 F 检验 - 连锁店和所有权控制变量
    # F test for Model (ii) - Chain and ownership controls
    chain_controls = ['bk', 'kfc', 'roys', 'CO_OWNED']
    p_val2 = calculate_f_test_pvalue(results['model2'], chain_controls)
    row6.append(f"{p_val2:.2f}" if p_val2 is not None else "")

    row6.append("")  # 模型 (iii) 没有控制变量 # Model (iii) has no control variables

    # 模型 (iv) 的 F 检验 - 连锁店和所有权控制变量
    # F test for Model (iv) - Chain and ownership controls
    p_val4 = calculate_f_test_pvalue(results['model4'], chain_controls)
    row6.append(f"{p_val4:.2f}" if p_val4 is not None else "")

    # 模型 (v) 的 F 检验 - 所有控制变量
    # F test for Model (v) - All control variables
    all_controls = ['bk', 'kfc', 'roys', 'CO_OWNED', 'CENTRALJ', 'SOUTHJ', 'PA1', 'PA2']
    p_val5 = calculate_f_test_pvalue(results['model5'], all_controls)
    row6.append(f"{p_val5:.2f}" if p_val5 is not None else "")

    table_data.append(row6)

    # 创建 markdown 表格
    # Create markdown table
    header = "| Independent variable                       | Model (i)   | Model (ii)  | Model (iii) | Model (iv)  | Model (v)   |" # Changed to English
    separator = "| :----------------------------------------- | :---------- | :---------- | :---------- | :---------- | :---------- |"

    table_lines = [title, "", header, separator]
    for row in table_data:
        # Adjust formatting slightly for English text width
        # Use a fixed width for the first column and left align others
        line = f"| {row[0]:<42} | {' | '.join(f'{cell:<11}' for cell in row[1:])} |"
        table_lines.append(line)

    # 添加注释
    # Add notes
    notes = [
        "",
        f"Notes: Standard errors are given in parentheses. The sample consists of {sample_size} stores with available data on employment and starting wages in waves 1 and 2. The dependent variable in all models is change in FTE employment. The mean and standard deviation of the dependent variable are {results['model1'].model.endog.mean():.3f} and {results['model1'].model.endog.std():.3f}, respectively. All models include an unrestricted constant (not reported).", # Changed to English and updated mean/std values
        "",
        "<sup>a</sup> Proportional increase in starting wage necessary to raise starting wage to new minimum rate. For stores in Pennsylvania the wage gap is 0.", # Changed to English
        "<sup>b</sup> Three dummy variables for chain type and whether or not the store is company-owned are included.", # Changed to English
        "<sup>c</sup> Dummy variables for two regions of New Jersey and two regions of eastern Pennsylvania are included.", # Changed to English
        "<sup>d</sup> Probability value of joint F test for exclusion of all control variables." # Changed to English
    ]

    return "\n".join(table_lines + notes)

def main():
    """
    主函数，用于复制表格4
    Main function to replicate Table 4
    """
    # 加载和处理数据
    # Load and process data
    df = load_data()
    df = create_variables(df)
    sample = create_analysis_sample(df)

    # 运行回归
    # Run regressions
    results = run_regressions(sample)

    # 格式化并打印表格
    # Format and print the table
    table_output = format_table(results, len(sample))
    print(table_output)

    # 保存到文件
    # Save to file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, 'output.md')

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(table_output)
        print(f"\nResults saved to {output_path}")
    except Exception as e:
        print(f"\nWarning: Could not save results to file: {e}")

if __name__ == "__main__":
    main()