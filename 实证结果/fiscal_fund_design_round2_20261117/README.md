# 第二轮研究设计与复现

先读[第二轮研究设计与结果](第二轮研究设计与结果.md)，再看[补充数据清单](补充数据清单与导出说明.md)。已有和外部文献分别核验，完整估计和数据审计放在本目录。

## 运行顺序

环境延续第一轮：Python 3、numpy、pandas、openpyxl及Stata 18兼容环境。第一轮宏观输入为`面板数据/fiscal_macro_trial_20261117.csv`。在仓库根目录运行：

```sh
python3 scripts/build_micro_fiscal_round2_20261117.py
python3 scripts/build_fund_choice_round2_20261117.py
python3 scripts/prepare_round2_20261117.py
```

微观脚本流式扫描20个非上市专利分片，保留精确匹配的目标企业，缺失专利行不填零。它同时输出完整注册地范围的匹配审计；本轮所有回归使用地市级口径。

在Stata中将工作目录设为仓库根目录，运行：

```stata
do "运行日志与do代码/fiscal_fund_micro_round2_20261117.do"
```

也可把仓库绝对路径作为do文件的第一个参数。本次通过Stata MCP实际执行；同名`.log`位于`运行日志与do代码`。输出目录固定为`实证结果/fiscal_fund_design_round2_20261117/`。

```sh
python3 scripts/summarize_round2_20261117.py
python3 scripts/validate_round2_20261117.py
```

F2逐一剔除来源城市的影响性诊断单列脚本和日志，执行次序：

```sh
python3 scripts/prepare_round2_f2_influence_20261117.py
```

```stata
do "运行日志与do代码/fiscal_round2_f2_influence_20261117.do"
```

最后重跑汇总脚本更新结果索引。影响性诊断由识别支撑集中度触发，启动依据见[analysis_plan.md](analysis_plan.md)，不替换原主模型。

## 数据与结果

| 文件 | 用途 |
|---|---|
| `面板数据/micro_fiscal_round2_20261117.csv` | 企业精确匹配、来源城市、专利可见性和事件窗口 |
| `面板数据/firm_changes_round2_20261117.csv` | 每企业一行的前后变化与逐规格资格标记 |
| `面板数据/fund_choice_round2_20261117.csv` | 基金事件、财政滞后、行业／目的地及固定效应样本 |
| `micro_audit.json` | 企业和专利匹配、真实零值、覆盖、输入哈希 |
| `micro_feasibility.json` | 上市路线、出资人目录和退出数据可行性 |
| `micro_firm_source_associations.csv` | 企业—基金—来源／目的地关联 |
| `micro_fund_sponsor_review.csv` | 逐基金出资人线索，保留待核验状态 |
| `fund_choice_audit.json` | 基金模型样本及财政残差变异 |
| `firm_changes_audit.json` | 首投筛除、窗口及样本 |
| `model_results.csv` | 11个固定规格，含2个样本门槛跳过状态 |
| `all_coefficients.csv` | 9个成功模型全部系数 |
| `core_tests_holm.csv` | F1／M1两项主要诊断的Holm校正 |
| `samples/` | 成功模型的实际估计样本 |
| `validation.json` | 独立数据与估计复核，F2识别变动集中度 |
| `f2_leave_one_city.csv` | F2全部40个留一来源城结果 |

基金模型是线性概率模型，企业模型是投前后对数变化回归。二者均按财政来源城市聚类。对照企业、完整融资历程及专利缺行含义的核验完成后，再落实正式企业事件研究。
