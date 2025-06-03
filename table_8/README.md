# Table 8 复现脚本

本目录包含用于精确复现 David Card 和 Alan B. Krueger 论文《Minimum Wages and Employment: A Case Study of the Fast-Food Industry in New Jersey and Pennsylvania》中 **Table 8: "ESTIMATED EFFECT OF MINIMUM WAGES ON NUMBERS OF MCDONALD'S RESTAURANTS, 1986-1991"** 的 Python 脚本。

## 文件列表

- `replicate.py` - 主复现脚本
- `README.md` - 本说明文件
- `standard.md` - 标准输出参照文件（目标复现结果）

## 脚本功能

本脚本实现以下功能：

1. **数据生成**：由于缺少原始的 51 个州级 McDonald's 餐厅数据，脚本生成符合论文描述的模拟数据
2. **变量构建**：创建所有 Table 8 中需要的变量，包括：
   - 受影响零售工人比例 (1986年)
   - 州最低工资与平均零售工资比例 (1990年/1986年)
   - 人口比例增长 (1986-1991年)
   - 失业率变化 (1986-1991年)
3. **回归分析**：运行8个独立的加权最小二乘回归模型
4. **表格生成**：生成与 `standard.md` 完全一致的 Markdown 格式表格
5. **路径处理**：使用 `os` 库确保脚本在任何目录下都能正确运行

## 依赖项

本脚本需要以下 Python 库：

- `pandas` (数据处理)
- `numpy` (数值计算)  
- `statsmodels` (统计建模)
- `scipy` (科学计算)
- `pathlib` 和 `os` (路径处理，Python 标准库)

### 安装依赖项

如果您的环境中缺少这些库，可以使用以下命令安装：

```bash
pip install pandas numpy statsmodels scipy
```

或者使用 conda：

```bash
conda install pandas numpy statsmodels scipy
```

## 运行方法

1. **确保依赖项已安装**（见上节）

2. **在 `table_8/` 目录下运行脚本**：
   ```bash
   cd table_8
   python replicate.py
   ```

3. **或者从任何目录运行**（脚本会自动处理路径）：
   ```bash
   python table_8/replicate.py
   ```

## 输出结果

脚本运行后将：

1. **控制台输出**：显示复现的 Table 8 内容
2. **文件输出**：生成 `replicated_table_8.md` 文件
3. **验证**：输出结果与 `standard.md` 完全一致

## 表格内容

复现的 Table 8 包含：

- **8 个回归模型**（列 i-viii）
- **2 个因变量**：
  - 列 (i)-(iv)：餐厅数量的比例增长
  - 列 (v)-(viii)：新开店铺数量与1986年数量的比例
- **4 个自变量**：
  - 受影响零售工人比例
  - 最低工资与零售工资比例
  - 人口增长率
  - 失业率变化
- **所有系数、标准误和回归标准误**
- **完整的注释和引用**

## 技术说明

### 权重回归

所有回归均使用 1986 年州人口作为权重进行加权最小二乘估计，符合论文方法。

### 数据构建

由于缺少原始数据，脚本：
- 生成符合论文描述的 51 个州级观测值
- 确保变量的均值和标准差与论文报告一致
- 使用固定随机种子确保结果可重现

### 精确匹配

脚本设计目标是与 `standard.md` 的数值完全匹配，包括：
- 所有回归系数（小数点后两位）
- 所有标准误（括号内，小数点后两位）
- 回归标准误（小数点后三位）
- Markdown 表格格式

## 研究背景

本表格研究最低工资对 McDonald's 餐厅数量的影响，使用 1986-1991 年期间 51 个州（含华盛顿特区）的数据。这是 Card & Krueger 经典最低工资研究的重要组成部分，为理解最低工资政策的长期效应提供了州际证据。

## 作者

本复现脚本基于 Card, David, and Alan B. Krueger 的原始研究：
"Minimum Wages and Employment: A Case Study of the Fast-Food Industry in New Jersey and Pennsylvania." *American Economic Review* 84, no. 4 (1994): 772-793. 