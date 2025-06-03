#!/usr/bin/env python3
"""
测试脚本：演示utility.py模块的功能
用于验证重构后的通用函数是否正常工作
"""

import utility as util
import pandas as pd
import numpy as np

def test_data_loading():
    """测试数据读取功能"""
    print("=" * 60)
    print("测试数据读取功能")
    print("=" * 60)
    
    try:
        # 测试数据读取
        print("1. 测试空白字符分隔读取...")
        df1 = util.read_data(method='whitespace')
        print(f"   成功读取 {len(df1)} 行数据")
        
        print("2. 测试固定宽度读取...")
        df2 = util.read_data(method='fixed_width')
        print(f"   成功读取 {len(df2)} 行数据")
        
        print("3. 测试列名一致性...")
        expected_cols = util.get_column_names()
        print(f"   期望的列数: {len(expected_cols)}")
        print(f"   实际列数 (whitespace): {len(df1.columns)}")
        print(f"   实际列数 (fixed_width): {len(df2.columns)}")
        
        return df1
        
    except Exception as e:
        print(f"   错误: {e}")
        return None

def test_derived_variables(df):
    """测试衍生变量计算"""
    print("\n" + "=" * 60)
    print("测试衍生变量计算")
    print("=" * 60)
    
    if df is None:
        print("跳过测试：数据未成功加载")
        return None
    
    try:
        print("1. 测试基本衍生变量...")
        df_processed = util.create_basic_derived_variables(df)
        
        # 检查关键变量是否存在
        key_vars = ['EMPTOT', 'EMPTOT2', 'DEMP', 'nj', 'bk', 'kfc', 'roys', 'wendys', 'gap']
        missing_vars = [var for var in key_vars if var not in df_processed.columns]
        
        if missing_vars:
            print(f"   警告: 缺少变量 {missing_vars}")
        else:
            print("   ✓ 所有关键变量已创建")
        
        print(f"2. 测试FTE就业计算...")
        print(f"   Wave 1 FTE均值: {df_processed['EMPTOT'].mean():.2f}")
        print(f"   Wave 2 FTE均值: {df_processed['EMPTOT2'].mean():.2f}")
        print(f"   就业变化均值: {df_processed['DEMP'].mean():.2f}")
        
        print(f"3. 测试州指示变量...")
        nj_count = (df_processed['nj'] == 1).sum()
        pa_count = (df_processed['nj'] == 0).sum()
        print(f"   新泽西州店铺数: {nj_count}")
        print(f"   宾夕法尼亚州店铺数: {pa_count}")
        
        return df_processed
        
    except Exception as e:
        print(f"   错误: {e}")
        return None

def test_statistical_functions(df):
    """测试统计计算函数"""
    print("\n" + "=" * 60)
    print("测试统计计算函数")
    print("=" * 60)
    
    if df is None:
        print("跳过测试：数据未处理")
        return
    
    try:
        print("1. 测试均值和标准误计算...")
        test_series = df['EMPTOT'].dropna()
        mean_val, se_val, n = util.calculate_mean_and_se(test_series)
        print(f"   样本量: {n}")
        print(f"   均值: {mean_val:.3f}")
        print(f"   标准误: {se_val:.3f}")
        
        print("2. 测试两样本t检验...")
        nj_data = util.filter_by_state(df, 'nj')['EMPTOT']
        pa_data = util.filter_by_state(df, 'pa')['EMPTOT']
        t_stat, p_val = util.calculate_two_sample_ttest(nj_data, pa_data)
        print(f"   t统计量: {t_stat:.3f}")
        print(f"   p值: {p_val:.3f}")
        
        print("3. 测试比例统计...")
        nj_bk = util.filter_by_state(df, 'nj')['bk']
        pa_bk = util.filter_by_state(df, 'pa')['bk']
        nj_pct, nj_se, pa_pct, pa_se, t_stat = util.calculate_proportion_stats(nj_bk, pa_bk)
        print(f"   NJ Burger King比例: {nj_pct:.1f}% (SE: {nj_se:.1f}%)")
        print(f"   PA Burger King比例: {pa_pct:.1f}% (SE: {pa_se:.1f}%)")
        
    except Exception as e:
        print(f"   错误: {e}")

def test_output_functions():
    """测试输出格式化函数"""
    print("\n" + "=" * 60)
    print("测试输出格式化函数")
    print("=" * 60)
    
    try:
        print("1. 测试系数格式化...")
        test_coef = 1.234
        test_se = 0.567
        formatted = util.format_coefficient(test_coef, test_se)
        print(f"   输入: coef={test_coef}, se={test_se}")
        print(f"   输出: {formatted}")
        
        print("2. 测试数值格式化...")
        test_num = 123.456789
        formatted_num = util.format_number(test_num, decimal_places=3)
        print(f"   输入: {test_num}")
        print(f"   输出: {formatted_num}")
        
        print("3. 测试输出路径生成...")
        output_path = util.get_output_path(__file__)
        print(f"   输出路径: {output_path}")
        
    except Exception as e:
        print(f"   错误: {e}")

def test_data_validation():
    """测试数据验证功能"""
    print("\n" + "=" * 60)
    print("测试数据验证功能")
    print("=" * 60)
    
    try:
        df = util.load_and_prepare_data()
        validation_results = util.validate_data(df, verbose=True)
        
        print(f"\n验证结果总结:")
        print(f"- 总观测数: {validation_results['total_observations']}")
        print(f"- 新泽西州观测数: {validation_results['nj_observations']}")
        print(f"- 宾夕法尼亚州观测数: {validation_results['pa_observations']}")
        
    except Exception as e:
        print(f"   错误: {e}")

def main():
    """主测试函数"""
    print("Card & Krueger (1994) 复制研究 - Utility模块测试")
    print("=" * 60)
    
    # 运行各项测试
    df = test_data_loading()
    df_processed = test_derived_variables(df)
    test_statistical_functions(df_processed)
    test_output_functions()
    test_data_validation()
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("如果看到此消息且没有错误，说明utility.py模块运行正常。")
    print("=" * 60)

if __name__ == "__main__":
    main() 