# regression_v3 实施计划

> 目标：在 `regression_v3/` 文件夹下完成面板数据构建、回归分析、出图全流程

---

## 环境选择

- **Python**：使用 `py -3.12`（Python 3.12, 64-bit），pandas/numpy 已有，需安装 `statsmodels`, `linearmodels`, `matplotlib`
- **Stata**：通过 `#stata-mcp` 执行 `.do` 脚本，用于稳健性回归和导出发表级表格
- **可视化**：调用 `#econ-visualization` skill 生成回归系数图；Python matplotlib 生成其他图

---

## Step 1: 安装 Python 依赖

```bash
py -3.12 -m pip install statsmodels linearmodels matplotlib
```

---

## Step 2: 面板数据构建 (`build_panel_v3.py`)

已有初稿（需修复 Python 3.6 语法 → 改用 `py -3.12` 后无需修复）。脚本逻辑：

1. **解析 CNRDS 专利数据**（获得 + 申请）→ `(城市, 年份, Invg, Umg, Desg, Inva)` 长面板
   - 直辖市：`Pftn` 为空时用 `Prvn`
2. **解析 CEIC 宽表**（7 个文件）→ `(城市, 年份, value)` 长面板
   - 财政收入、支出、总GDP、人均GDP、第二产业、科技支出、债务余额
3. **解析 year-indicator 文件**（3 个）→ 常住人口、实际利用外资、金融贷款余额
4. **合并引导基金投资统计**（分年份文件）→ 投资次数/金额/早期占比
5. **合并省级市场化指数** + **市级财政透明度**
6. **计算派生变量**：
   - `fiscal_gap_L1 = (exp_t-1 - rev_t-1) / exp_t-1`
   - `ln_debt_ratio_L1 = ln(debt_t-1 / rev_t-1)`
   - `ln_invg = ln(1 + invg)` 等 Y 变量
   - `sec_ratio`, `sci_ratio`, `fdi_dep`, `fin_depth` 等比率型 Z
   - `ln_invest_amt_L1`, `early_deal_ratio_L1` 等 M 变量（均取滞后一期）
7. **1%/99% 缩尾 + 城市 ID + 地区/行政等级标签**
8. **输出**：`panel_v3.csv`（约 4000+ 行 × 25+ 列）

---

## Step 3: Python 回归 (`run_regressions.py`)

已有初稿。将用 `linearmodels.PanelOLS` 做双向固定效应 + 城市聚类标准误：

### 3a. 描述性统计 → `descriptive_stats.csv`

### 3b. H1 基准回归（6 列矩阵）

| 列 | X 变量 | 控制变量 |
|----|--------|----------|
| (1) | fiscal_gap_L1 | 无 |
| (2) | fiscal_gap_L1 | ln_pgdp, sec_ratio, sci_ratio |
| (3) | fiscal_gap_L1 | 核心 + fdi_dep, fin_depth, ln_pop |
| (4) | ln_debt_ratio_L1 | 无 |
| (5) | ln_debt_ratio_L1 | 核心 |
| (6) | ln_debt_ratio_L1 | 核心 + 扩展 |

### 3c. H2 机制检验（两步法 + 交互项）
- 两步法：X → early_deal_ratio_L1
- 交互项：X × early_deal_ratio_L1 → Y

### 3d. H5 机制检验（两步法 + 交互项）
- 两步法：X → ln_invest_amt_L1
- 交互项：X × ln_invest_amt_L1 → Y

### 输出
- `reg_results.csv`（全部回归系数汇总）
- `panel_v3.dta`（供 Stata 使用的面板数据）

---

## Step 4: Stata 回归（via #stata-mcp）

用 `#stata-mcp` 执行 `.do` 脚本进行以下回归（Stata 在学术论文中更标准）：

### 4a. `baseline_h1.do` — H1 基准回归
- `reghdfe ln_invg fiscal_gap_L1 [controls], absorb(city_id year) vce(cluster city_id)`
- 6 列规格，`esttab` 导出 LaTeX/CSV 表格

### 4b. `mechanism_h2_h5.do` — H2/H5 机制检验
- 两步法第一步 + 交互项法
- 导出 LaTeX 表格

### 4c. `iv_2sls.do` — 工具变量回归（Bartik IV）
- 构建同省其他城市平均 fiscal_gap 作为 IV
- `ivreghdfe` 或 `ivreg2` + 第一阶段 F 统计量
- 导出结果

### 输出
- `baseline_h1.tex` / `.csv`
- `mechanism_h2_h5.tex` / `.csv`
- `iv_results.tex` / `.csv`

---

## Step 5: 出图（调用 #econ-visualization skill + matplotlib）

### 5a. 基准回归系数图（Coefficient Plot）
- H1 六列回归的 fiscal_gap_L1 / ln_debt_ratio_L1 系数 + 95% CI
- 调用 `#econ-visualization` skill 生成发表级图

### 5b. 机制检验系数图
- H2/H5 两步法第一步系数 + CI
- 交互项的边际效应图

### 5c. 描述性统计可视化
- 财政缺口率 vs 发明授权量的散点图 + 拟合线（binscatter 风格）
- 引导基金投资额的时间趋势图

### 输出文件（均放在 `regression_v3/` 下）
- `fig_h1_coef_plot.png` — 基准回归系数图
- `fig_mechanism_coef.png` — 机制检验系数图
- `fig_scatter_fiscal_patent.png` — 散点拟合图
- `fig_fund_trend.png` — 引导基金投资趋势图

---

## 执行顺序总结

```
1. pip install statsmodels linearmodels matplotlib (py -3.12)
2. py -3.12 build_panel_v3.py          → panel_v3.csv, panel_v3.dta
3. py -3.12 run_regressions.py         → reg_results.csv, descriptive_stats.csv
4. #stata-mcp 执行 .do 脚本           → LaTeX 表格 + Stata 回归结果
5. #econ-visualization + matplotlib    → 4 张发表级图
```

所有产出文件均放在 `regression_v3/` 文件夹中。
