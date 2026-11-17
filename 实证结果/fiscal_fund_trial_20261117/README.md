# 分支试验复现

先读[结果报告](结果报告.md)。预设规则及实现修正见[analysis_plan.md](analysis_plan.md)。

## 运行环境与步骤

在仓库根目录执行。需要Python 3、pandas、numpy、openpyxl、matplotlib以及可运行Stata 18语法的Stata；数据来自仓库已有原始文件，无新增下载。图表脚本优先使用macOS黑体，其他系统可安装中文字体后调整字体路径。

```sh
python3 scripts/build_fund_trial_20261117.py
python3 scripts/build_fiscal_macro_trial_20261117.py
python3 scripts/prepare_fiscal_trial_20261117.py
```

在Stata中，先将工作目录设为仓库根目录，再运行：

```stata
do "运行日志与do代码/xtreg_fiscal_fund_trial_20261117.do"
```

也可将仓库绝对路径作为do文件的第一个参数传入。此次实际执行使用Stata MCP。do文件会自动生成同名日志，放在`运行日志与do代码`，并将完整结果导出到`实证结果/fiscal_fund_trial_20261117/`。

```sh
python3 scripts/summarize_fiscal_trial_20261117.py
python3 scripts/validate_fiscal_trial_20261117.py
```

Python脚本通过自身位置解析仓库根目录；不依赖旧版Windows路径。所有新增文件均使用独立名称，原始数据、旧面板和论文正文保持原版本。

## 产物索引

| 文件 | 内容 |
|---|---|
| `面板数据/fund_trial_20261117.csv` | 地市级与广义注册地的有记录城市年份、阶段、金额、行业构成 |
| `面板数据/fiscal_macro_trial_20261117.csv` | 原始收支重算财政缺口、债务量纲、修复控制变量、专利 |
| `面板数据/fiscal_fund_trial_20261117.csv` | 精确滞后和领先匹配后的分析数据、逐模型资格标记 |
| `model_manifest.json` | 所有规格的因变量、公式、目标项、必需列、年份范围 |
| `model_results.csv` | 全部36规格的目标系数、区间、p值、样本和运行状态 |
| `all_coefficients.csv` | 已估模型的全部系数，包括年份项 |
| `samples/` | 每个已估模型的实际城市年份及关键变量 |
| `sample_attrition.csv` | 缺失筛除和单期城市流失 |
| `marginal_effects.csv` | 样本分位点的基金斜率、双重约束调节及区间 |
| `marginal_effects.png/svg` | 可分享和可编辑的边际关系图 |
| `core_tests_holm.csv` | 地市级I2、B1、B2三个核心检验及Holm校正 |
| `event_audit.json`、`macro_audit.json` | 输入哈希、数据定义、缺失与修复核验 |
| `coverage_by_year.csv` | 基金记录年度覆盖 |
| `fund_mapping_review.csv` | 地市级基金逐基金注册地核验线索，出资辖区待核验 |
| `analysis_input_hashes.json` | 三个试验数据文件的SHA256 |
| `validation.json` | 独立复核结果 |

`municipal`表示明确地市级基金，`broad`表示全部级别基金；两者均按注册城市归属。输出记录数是基金—投资事件记录数。同一融资交易的不同投资基金可能各占一条，不解释为去重后的企业融资轮次数。

Stata的`r2w`仅对应未加权xtreg规格；B3采用areg，留空该字段。B6地市级样本未达到预设门槛，保留状态，不生成估计样本文件。其余实现细节见脚本及日志。
