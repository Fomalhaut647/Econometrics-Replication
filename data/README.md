data/ 包含5个与 _Minimum Wages and Employment: A Case Study of the Fast-Food Industry in New Jersey and Pennsylvania_ 相关的文件：

* `` `public.dat` `` 一个ASCII（平面文件）数据集（410个观测值）
* `` `codebook` `` `public.dat`数据的ASCII码本
* `` `check.sas` `` 一个SAS程序的ASCII版本，用于读取数据并创建一些关键的制表
* `` `survey1.nj` `` 第一轮调查的文本版本
* `` `survey2.nj` `` 第二轮调查的文本版本

---

# NJ-PA 数据分析 - Python 版本

这是用于分析新泽西州和宾夕法尼亚州就业数据的原始 SAS `check.sas` 程序的 Python 翻译版本。

## 概览

该程序执行全面的数据分析，包括：
- 数据输入和验证
- 变量创建和转换
- 描述性统计和频率表
- 分组比较（按州和工资类别）
- 检验就业变化的回归分析

## 要求

安装所需的 Python 包：

```bash
pip install -r requirements.txt
```

所需包：
- pandas（数据操作）
- numpy（数值计算）
- scipy（统计函数）
- statsmodels（回归分析）
- pathlib（文件路径处理）

## 数据文件

程序使用此目录中包含的 `public.dat` 文件。它也支持以下替代文件名：
- `public.dat` (默认)
- `FLAT`
- `data.txt`
- `njpa_data.txt`
- `flat_data.txt`

数据文件包含以空格分隔的值，具有 47 个变量，包括两个调查波次的就业数据、工资和商店特征。

## 快速开始

1. **测试设置**（推荐的第一步）：
   ```bash
   python test_check.py
   ```
   这将验证所有依赖项是否已安装以及数据文件是否可访问。

2. **运行完整分析**：
   ```bash
   python check.py
   ```

## 包含的文件

- `check.py` - 主要分析程序（check.sas 的 Python 版本）
- `test_check.py` - 测试脚本，用于验证设置
- `requirements.txt` - Python 包依赖项
- `public.dat` - 数据文件
- `README.md` - 本文档

## 输出

程序生成以下分析结果：

1. **频率表**：分类变量的分布（连锁店、州、状态等）
2. **描述性统计**：所有变量的汇总统计
3. **表 2**：按 NJ/PA 州划分的统计数据
4. **表 3**：按州和工资类别划分的就业变化
5. **关闭商店分析**：两轮调查间关闭的商店列表
6. **表 4**：就业变化的回归分析

## 创建的关键变量

程序创建了几个衍生变量：

- `EMPTOT`：总就业人数（全职 + 0.5×兼职 + 经理）
- `DEMP`：两轮调查间的就业变化
- `PCHEMPC`：就业变化的百分比
- `gap`：相对于最低工资（5.05）的工资差距
- `nj`：新泽西州指示变量（1=NJ，0=PA）
- 连锁店指示变量：`bk`, `kfc`, `roys`, `wendys`
- `CLOSED`：商店关闭指示变量
- `ICODE`：按州和工资水平划分的商店分类

## 回归模型

程序拟合了 10 个回归模型来检验：

1. **就业变化模型 (DEMP)**：
   - 模型 1: DEMP ~ gap
   - 模型 2: DEMP ~ gap + 连锁店控制变量
   - 模型 3: DEMP ~ gap + 连锁店 + 地点控制变量
   - 模型 4: DEMP ~ nj
   - 模型 5: DEMP ~ nj + 连锁店控制变量

2. **就业百分比变化模型 (PCHEMPC)**：
   - 模型 6: PCHEMPC ~ gap
   - 模型 7: PCHEMPC ~ gap + 连锁店控制变量
   - 模型 8: PCHEMPC ~ gap + 连锁店 + 地点控制变量
   - 模型 9: PCHEMPC ~ nj
   - 模型 10: PCHEMPC ~ nj + 连锁店控制变量

## 故障排除

如果遇到问题：

1. **缺少包**：运行 `pip install -r requirements.txt`
2. **未找到数据文件**：确保 `public.dat` 位于同一目录中
3. **导入错误**：检查您是否正在使用 Python 3.6 或更高版本
4. **运行时错误**：首先运行测试脚本：`python test_check.py`

## 注意

- 程序适当处理缺失数据
- 所有回归模型都包含错误处理
- 输出与原始 SAS 程序的结构和内容匹配
- 所有变量转换都精确复制了 SAS 的逻辑
- 用于回归分析的子集排除了就业变化数据缺失或工资过渡无效的商店