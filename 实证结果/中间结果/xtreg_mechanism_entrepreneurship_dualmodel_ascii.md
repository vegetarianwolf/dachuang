# 创业活跃度机制检验：两种模型分类报告

日期：2026-05-16

## 1. 任务与数据

本轮根据 `研究方案整理` 目录下“机制变量作为中介或调节变量的两种建模方案”，针对新增机制变量 `entrepreneurship_activity`（创业活跃度）进行机制检验。

- 数据文件：`dachuang/面板数据/地级市总面板_2015_2024_英文版.csv`
- 样本：2015-2024 年地级市面板
- 面板设定：城市固定效应 + 年份固定效应
- 标准误：按城市聚类稳健标准误
- 核心解释变量：`fund_est_scale_cum`
- 财政债务压力变量：`debt_pressure`、`debt_pressure_l1`
- 机制变量：`entrepreneurship_activity`
- 创新产出：`pat_invent_apply`、`pat_utility_apply`、`pat_apply_total`
- 控制变量版本：`noctrl` 与 `ctrl`
- 控制变量：`ln_gdp`、`ln_fiscal_scitech`、`ln_pop`、`ln_secondary`、`ln_fdi`

## 2. 模型设定

### 2.1 基准调节模型

```text
Y_it = beta0 + beta1 X_it + beta2 D_it + beta3 X_it * D_it + Controls_it + CityFE + YearFE + e_it
```

关注 `fund_est_scale_cum × debt_pressure` 或 `fund_est_scale_cum × debt_pressure_l1`。

### 2.2 方案一：机制变量作为中介变量

机制方程：

```text
M_it = a0 + a1 X_it + a2 D_it + a3 X_it * D_it + Controls_it + CityFE + YearFE + u_it
```

结果方程：

```text
Y_it = c0 + c1 X_it + c2 D_it + c3 X_it * D_it + c4 M_it + Controls_it + CityFE + YearFE + v_it
```

判定标准：`a3` 显著、`c4` 显著，且加入 `M` 后 `c3` 相对基准 `beta3` 减弱。

### 2.3 方案二：机制变量作为调节变量

机制方程：

```text
M_it = d0 + d1 X_it + d2 D_it + Controls_it + CityFE + YearFE + r_it
```

结果方程：

```text
Y_it = e0 + e1 X_it + e2 D_it + e3 X_it * D_it + e4 M_it + e5 X_it * M_it + Controls_it + CityFE + YearFE + w_it
```

判定标准：`d2` 显著、`e5` 显著，且加入 `X × M` 后 `e3` 相对基准 `beta3` 减弱。

## 3. 基准调节结果

| spec | 债务口径 | 因变量 | `X × D` 系数 | 标准误 | p值 | N | 结论 |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| noctrl | debt_pressure | pat_invent_apply | -0.00001277 | 0.00000294 | 0.0000 | 1805 | 显著负向 |
| noctrl | debt_pressure | pat_utility_apply | -0.00001278 | 0.00000902 | 0.1579 | 1805 | 不显著 |
| noctrl | debt_pressure | pat_apply_total | -0.00003246 | 0.00001467 | 0.0278 | 1805 | 显著负向 |
| noctrl | debt_pressure_l1 | pat_invent_apply | -0.00001335 | 0.00000329 | 0.0001 | 1800 | 显著负向 |
| noctrl | debt_pressure_l1 | pat_utility_apply | -0.00001398 | 0.00000981 | 0.1553 | 1800 | 不显著 |
| noctrl | debt_pressure_l1 | pat_apply_total | -0.00003513 | 0.00001612 | 0.0303 | 1800 | 显著负向 |
| ctrl | debt_pressure | pat_invent_apply | -0.00001249 | 0.00000350 | 0.0005 | 947 | 显著负向 |
| ctrl | debt_pressure | pat_utility_apply | -0.00001465 | 0.00000843 | 0.0839 | 947 | 10%显著负向 |
| ctrl | debt_pressure | pat_apply_total | -0.00003563 | 0.00001517 | 0.0199 | 947 | 显著负向 |
| ctrl | debt_pressure_l1 | pat_invent_apply | -0.00001467 | 0.00000403 | 0.0004 | 944 | 显著负向 |
| ctrl | debt_pressure_l1 | pat_utility_apply | -0.00001558 | 0.00000927 | 0.0945 | 944 | 10%显著负向 |
| ctrl | debt_pressure_l1 | pat_apply_total | -0.00003992 | 0.00001674 | 0.0181 | 944 | 显著负向 |

基准调节项整体仍然支持“债务压力削弱基金累计设立规模创新促进效应”的主线，尤其在控制变量版本下三个创新指标均至少在 10% 水平显著。

## 4. 方案一：创业活跃度作为中介变量

### 4.1 机制方程

| spec | 债务口径 | `X × D -> M` 系数 | 标准误 | p值 | N | 结论 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| noctrl | debt_pressure | 0.0000000127 | 0.0000000275 | 0.6447 | 1776 | 不显著 |
| noctrl | debt_pressure_l1 | 0.0000000263 | 0.0000000339 | 0.4389 | 1775 | 不显著 |
| ctrl | debt_pressure | -0.0000000329 | 0.0000000344 | 0.3403 | 947 | 不显著 |
| ctrl | debt_pressure_l1 | -0.0000000344 | 0.0000000396 | 0.3869 | 944 | 不显著 |

### 4.2 结果方程

| spec | 债务口径 | 因变量 | `X × D` 系数 | p值 | `M` 系数 | p值 | N | 判定 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| noctrl | debt_pressure | pat_invent_apply | -0.00001277 | 0.0000 | -0.0236 | 0.9805 | 1776 | 不支持中介 |
| noctrl | debt_pressure | pat_utility_apply | -0.00001284 | 0.1560 | 7.6810 | 0.1118 | 1776 | 不支持中介 |
| noctrl | debt_pressure | pat_apply_total | -0.00003252 | 0.0275 | 8.2521 | 0.1895 | 1776 | 不支持中介 |
| noctrl | debt_pressure_l1 | pat_invent_apply | -0.00001334 | 0.0001 | -0.1860 | 0.7096 | 1775 | 不支持中介 |
| noctrl | debt_pressure_l1 | pat_utility_apply | -0.00001405 | 0.1528 | 4.4192 | 0.2166 | 1775 | 不支持中介 |
| noctrl | debt_pressure_l1 | pat_apply_total | -0.00003520 | 0.0296 | 4.4906 | 0.2745 | 1775 | 不支持中介 |
| ctrl | debt_pressure | pat_invent_apply | -0.00001254 | 0.0004 | -1.4915 | 0.3666 | 947 | 不支持中介 |
| ctrl | debt_pressure | pat_utility_apply | -0.00001471 | 0.0843 | -1.8231 | 0.6042 | 947 | 不支持中介 |
| ctrl | debt_pressure | pat_apply_total | -0.00003579 | 0.0202 | -5.0768 | 0.4654 | 947 | 不支持中介 |
| ctrl | debt_pressure_l1 | pat_invent_apply | -0.00001471 | 0.0004 | -1.3277 | 0.3565 | 944 | 不支持中介 |
| ctrl | debt_pressure_l1 | pat_utility_apply | -0.00001564 | 0.0948 | -1.5279 | 0.6124 | 944 | 不支持中介 |
| ctrl | debt_pressure_l1 | pat_apply_total | -0.00004009 | 0.0184 | -4.7945 | 0.4315 | 944 | 不支持中介 |

分类结论：创业活跃度不适合作为本轮“债务压力调节效应的中介变量”。原因是机制方程中的 `X × D -> M` 全部不显著，结果方程中的 `M -> Y` 也全部不显著。

## 5. 方案二：创业活跃度作为调节变量

### 5.1 机制方程

| spec | 债务口径 | `D -> M` 系数 | 标准误 | p值 | `X -> M` 系数 | p值 | N | 结论 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| noctrl | debt_pressure | 0.0153 | 0.0142 | 0.2843 | -0.00002263 | 0.2616 | 1776 | 不显著 |
| noctrl | debt_pressure_l1 | 0.0174 | 0.0132 | 0.1875 | -0.00001477 | 0.5143 | 1775 | 不显著 |
| ctrl | debt_pressure | 0.0301 | 0.0230 | 0.1913 | -0.00005466 | 0.0200 | 947 | 债务项不显著 |
| ctrl | debt_pressure_l1 | 0.0404 | 0.0167 | 0.0163 | -0.00005025 | 0.0290 | 944 | 债务滞后项显著 |

### 5.2 结果方程

| spec | 债务口径 | 因变量 | `X × D` 系数 | p值 | `M` 系数 | p值 | `X × M` 系数 | p值 | N | 判定 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| noctrl | debt_pressure | pat_invent_apply | -0.00001309 | 0.0000 | -0.4555 | 0.6924 | 0.00000645 | 0.7381 | 1776 | 不支持调节机制 |
| noctrl | debt_pressure | pat_utility_apply | -0.00001792 | 0.0141 | 0.8515 | 0.8224 | 0.00010204 | 0.2311 | 1776 | 不支持调节机制 |
| noctrl | debt_pressure | pat_apply_total | -0.00003949 | 0.0008 | -1.1126 | 0.8670 | 0.00013992 | 0.2914 | 1776 | 不支持调节机制 |
| noctrl | debt_pressure_l1 | pat_invent_apply | -0.00001362 | 0.0000 | -0.3700 | 0.5686 | 0.00000440 | 0.8048 | 1775 | 不支持调节机制 |
| noctrl | debt_pressure_l1 | pat_utility_apply | -0.00002098 | 0.0122 | -0.1902 | 0.9340 | 0.00011013 | 0.2123 | 1775 | 不支持调节机制 |
| noctrl | debt_pressure_l1 | pat_apply_total | -0.00004442 | 0.0005 | -1.6443 | 0.6656 | 0.00014658 | 0.2662 | 1775 | 不支持调节机制 |
| ctrl | debt_pressure | pat_invent_apply | -0.00001280 | 0.0001 | -2.1969 | 0.3631 | 0.00000518 | 0.7461 | 947 | 不支持调节机制 |
| ctrl | debt_pressure | pat_utility_apply | -0.00001783 | 0.0096 | -10.2593 | 0.1372 | 0.00006200 | 0.3315 | 947 | 不支持调节机制 |
| ctrl | debt_pressure | pat_apply_total | -0.00004017 | 0.0038 | -16.8953 | 0.1936 | 0.00008685 | 0.4122 | 947 | 不支持调节机制 |
| ctrl | debt_pressure_l1 | pat_invent_apply | -0.00001518 | 0.0001 | -2.0634 | 0.3263 | 0.00000653 | 0.7033 | 944 | 不支持调节机制 |
| ctrl | debt_pressure_l1 | pat_utility_apply | -0.00001972 | 0.0171 | -7.9812 | 0.1724 | 0.00005731 | 0.3618 | 944 | 不支持调节机制 |
| ctrl | debt_pressure_l1 | pat_apply_total | -0.00004614 | 0.0035 | -14.3503 | 0.1958 | 0.00008487 | 0.4280 | 944 | 不支持调节机制 |

分类结论：创业活跃度也不适合作为本轮“机制性调节变量”。虽然在 `ctrl + debt_pressure_l1` 的机制方程中，滞后债务压力对创业活跃度显著为正，但结果方程中的 `fund_est_scale_cum × entrepreneurship_activity` 在所有创新产出下均不显著，因此无法说明创业活跃度会改变基金累计设立规模对创新的边际作用。

## 6. 总体判断

本轮两种模型均不支持“创业活跃度”作为债务压力调节效应的有效机制变量。

- 作为中介变量：不成立。`fund_est_scale_cum × debt_pressure` 或 `fund_est_scale_cum × debt_pressure_l1` 对创业活跃度均不显著，创业活跃度对创新产出也不显著。
- 作为调节变量：不成立。债务压力对创业活跃度的影响只有一个受控滞后口径显著，但 `fund_est_scale_cum × entrepreneurship_activity` 在结果方程中全部不显著。
- 对论文写作的含义：创业活跃度可以保留为地区创新创业环境的控制变量或异质性背景变量，但不宜写成核心机制变量。

## 7. 文件路径

- do 文件：`dachuang/运行日志与do代码/xtreg_mechanism_entrepreneurship_dualmodel_ascii.do`
- log 文件：`dachuang/运行日志与do代码/xtreg_mechanism_entrepreneurship_dualmodel_ascii.log`
- 结果 CSV：`dachuang/运行日志与do代码/xtreg_mechanism_entrepreneurship_dualmodel_ascii_results.csv`
- 本报告：`dachuang/实证结果/xtreg_mechanism_entrepreneurship_dualmodel_ascii.md`
