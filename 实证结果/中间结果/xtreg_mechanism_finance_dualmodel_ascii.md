# 金融发展水平机制检验：两种模型分类报告

日期：2026-05-16

## 1. 任务与数据

本轮根据 `研究方案整理` 目录下“机制变量作为中介或调节变量的两种建模方案”，针对金融发展水平的多个变量口径进行机制检验。

- 数据文件：`dachuang/面板数据/地级市总面板_2015_2024_英文版.csv`
- 样本：2015-2024 年地级市面板
- 面板设定：城市固定效应 + 年份固定效应
- 标准误：按城市聚类稳健标准误
- 核心解释变量：`fund_est_scale_cum`
- 财政债务压力变量：`debt_pressure`、`debt_pressure_l1`
- 创新产出：`pat_invent_apply`、`pat_utility_apply`、`pat_apply_total`
- 控制变量版本：`noctrl` 与 `ctrl`
- 控制变量：`ln_gdp`、`ln_fiscal_scitech`、`ln_pop`、`ln_secondary`、`ln_fdi`

本轮按用户要求没有使用合成口径 `fin_dev`。实际检验的金融发展口径为：

- `fin_dev_1`：贷款余额/GDP 口径
- `fin_dev_2`：存款余额/GDP 口径
- `ln_loan_balance`：年末金融机构贷款余额对数
- `ln_deposit_balance`：年末金融机构存款余额对数
- `ln_gdp_finance_src`：金融发展口径 GDP 对数

## 2. 模型设定

### 2.1 基准调节模型

```text
Y_it = beta0 + beta1 X_it + beta2 D_it + beta3 X_it * D_it + Controls_it + CityFE + YearFE + e_it
```

### 2.2 方案一：金融发展作为中介变量

机制方程：

```text
M_it = a0 + a1 X_it + a2 D_it + a3 X_it * D_it + Controls_it + CityFE + YearFE + u_it
```

结果方程：

```text
Y_it = c0 + c1 X_it + c2 D_it + c3 X_it * D_it + c4 M_it + Controls_it + CityFE + YearFE + v_it
```

判定标准：`a3` 显著、`c4` 显著，且加入 `M` 后 `c3` 相对基准 `beta3` 减弱。

### 2.3 方案二：金融发展作为调节变量

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

| spec | 债务口径 | 因变量 | `X × D` 系数 | p值 | N | 结论 |
| --- | --- | --- | ---: | ---: | ---: | --- |
| noctrl | debt_pressure | pat_invent_apply | -0.00001277 | 0.0000 | 1805 | 显著负向 |
| noctrl | debt_pressure | pat_utility_apply | -0.00001278 | 0.1579 | 1805 | 不显著 |
| noctrl | debt_pressure | pat_apply_total | -0.00003246 | 0.0278 | 1805 | 显著负向 |
| noctrl | debt_pressure_l1 | pat_invent_apply | -0.00001335 | 0.0001 | 1800 | 显著负向 |
| noctrl | debt_pressure_l1 | pat_utility_apply | -0.00001398 | 0.1553 | 1800 | 不显著 |
| noctrl | debt_pressure_l1 | pat_apply_total | -0.00003513 | 0.0303 | 1800 | 显著负向 |
| ctrl | debt_pressure | pat_invent_apply | -0.00001249 | 0.0005 | 947 | 显著负向 |
| ctrl | debt_pressure | pat_utility_apply | -0.00001465 | 0.0839 | 947 | 10%显著负向 |
| ctrl | debt_pressure | pat_apply_total | -0.00003563 | 0.0199 | 947 | 显著负向 |
| ctrl | debt_pressure_l1 | pat_invent_apply | -0.00001467 | 0.0004 | 944 | 显著负向 |
| ctrl | debt_pressure_l1 | pat_utility_apply | -0.00001558 | 0.0945 | 944 | 10%显著负向 |
| ctrl | debt_pressure_l1 | pat_apply_total | -0.00003992 | 0.0181 | 944 | 显著负向 |

## 4. 方案一：金融发展作为中介变量

### 4.1 机制方程摘要

| spec | 债务口径 | 机制变量 | `X × D -> M` 系数 | p值 | N | 结论 |
| --- | --- | --- | ---: | ---: | ---: | --- |
| noctrl | debt_pressure | fin_dev_1 | 0.000000000239 | 0.0310 | 1776 | 显著 |
| noctrl | debt_pressure_l1 | fin_dev_1 | 0.000000000235 | 0.0628 | 1775 | 10%显著 |
| ctrl | debt_pressure | fin_dev_1 | 0.000000000254 | 0.0225 | 947 | 显著 |
| ctrl | debt_pressure_l1 | fin_dev_1 | 0.000000000182 | 0.2025 | 944 | 不显著 |
| 其他口径 | 两类债务口径 | fin_dev_2、ln_loan_balance、ln_deposit_balance、ln_gdp_finance_src | - | 大多不显著 | - | 不稳定 |

### 4.2 结果方程中的金融变量

在受控模型中，金融变量对创新产出的显著结果主要包括：

| spec | 债务口径 | 机制变量 | 因变量 | `M -> Y` 系数 | p值 | 说明 |
| --- | --- | --- | --- | ---: | ---: | --- |
| ctrl | debt_pressure | fin_dev_1 | pat_utility_apply | 4091.4283 | 0.0672 | 10%显著 |
| ctrl | debt_pressure | ln_gdp_finance_src | pat_apply_total | 9065.9958 | 0.0941 | 10%显著 |
| ctrl | debt_pressure_l1 | fin_dev_1 | pat_utility_apply | 4399.1671 | 0.0664 | 10%显著 |

### 4.3 分类结论

没有任何金融发展口径通过完整的“中介变量”判定。

- `fin_dev_1` 在部分机制方程中显著，说明债务压力调节项会影响贷款/GDP 口径的金融发展水平。
- 但 `fin_dev_1` 对创新产出的显著性主要集中在 `pat_utility_apply`，且加入 `M` 后并未形成稳定的 `X × D -> M -> Y` 传导链。
- `fin_dev_2`、`ln_loan_balance`、`ln_deposit_balance`、`ln_gdp_finance_src` 在机制方程或结果方程中不够同时显著，因此不能作为完整中介机制。

## 5. 方案二：金融发展作为调节变量

### 5.1 机制方程摘要

| spec | 债务口径 | 机制变量 | `D -> M` 系数 | p值 | N | 结论 |
| --- | --- | --- | ---: | ---: | ---: | --- |
| noctrl | debt_pressure | fin_dev_1 | 0.000207 | 0.0000 | 1776 | 显著正向 |
| noctrl | debt_pressure_l1 | fin_dev_1 | 0.000179 | 0.0000 | 1775 | 显著正向 |
| ctrl | debt_pressure | fin_dev_1 | 0.000248 | 0.0001 | 947 | 显著正向 |
| ctrl | debt_pressure_l1 | fin_dev_1 | 0.000223 | 0.0001 | 944 | 显著正向 |
| ctrl | debt_pressure | ln_deposit_balance | -0.0000523 | 0.0014 | 947 | 显著负向 |
| ctrl | debt_pressure_l1 | ln_deposit_balance | -0.0000541 | 0.0003 | 944 | 显著负向 |

### 5.2 结果方程中的 `X × M`

部分金融口径的 `X × M` 项显著，但并非都能构成完整调节机制：

| spec | 债务口径 | 机制变量 | 因变量 | `X × M` 系数 | p值 | 是否构成完整机制 |
| --- | --- | --- | --- | ---: | ---: | --- |
| noctrl | debt_pressure | fin_dev_2 | pat_invent_apply | 0.005122 | 0.0040 | 否，`D -> M` 不显著 |
| noctrl | debt_pressure | fin_dev_2 | pat_utility_apply | -0.020489 | 0.0000 | 否，`D -> M` 不显著 |
| noctrl | debt_pressure | fin_dev_2 | pat_apply_total | -0.019559 | 0.0007 | 否，`D -> M` 不显著 |
| ctrl | debt_pressure | ln_deposit_balance | pat_invent_apply | 0.012083 | 0.0001 | 是 |
| ctrl | debt_pressure_l1 | ln_deposit_balance | pat_invent_apply | 0.012889 | 0.0000 | 是 |
| ctrl | debt_pressure | ln_loan_balance | pat_invent_apply | 0.019019 | 0.0000 | 否，`D -> M` 不显著 |
| ctrl | debt_pressure_l1 | ln_loan_balance | pat_invent_apply | 0.020066 | 0.0000 | 否，`D -> M` 不显著 |
| ctrl | debt_pressure | ln_gdp_finance_src | pat_invent_apply | 0.019931 | 0.0000 | 否，`D -> M` 不显著 |
| ctrl | debt_pressure_l1 | ln_gdp_finance_src | pat_invent_apply | 0.020497 | 0.0000 | 否，`D -> M` 不显著 |

### 5.3 通过完整判定的路径

| spec | 债务口径 | 机制变量 | 因变量 | `D -> M` 系数 | p值 | `X × M` 系数 | p值 | 加入机制后 `X × D` | 基准 `X × D` | 判定 |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| ctrl | debt_pressure | ln_deposit_balance | pat_invent_apply | -0.0000523 | 0.0014 | 0.012083 | 0.0001 | -0.00000348 | -0.00001249 | 支持 |
| ctrl | debt_pressure_l1 | ln_deposit_balance | pat_invent_apply | -0.0000541 | 0.0003 | 0.012889 | 0.0000 | -0.00000446 | -0.00001467 | 支持 |

分类结论：金融发展作为调节机制时，有一条较清晰的支持性证据，即 `ln_deposit_balance` 承接债务压力影响，并进一步调节基金累计设立规模对发明申请量的作用。加入 `fund_est_scale_cum × ln_deposit_balance` 后，原本的 `fund_est_scale_cum × debt_pressure` 负向系数明显缩小且不再显著，说明存款余额口径的金融环境可能承接了部分债务压力调节效应。

## 6. 总体判断

- `fin_dev_1`：债务压力对其影响较稳定，尤其在方案二机制方程中显著为正；但 `fund_est_scale_cum × fin_dev_1` 不显著，不能构成完整调节机制。
- `fin_dev_2`：`fund_est_scale_cum × fin_dev_2` 在多个结果方程中显著，但债务压力并未显著改变 `fin_dev_2`，因此更像金融环境边界变量，而不是债务压力传导机制。
- `ln_loan_balance`：`fund_est_scale_cum × ln_loan_balance` 对发明申请量显著，但债务压力对贷款余额对数不显著，完整机制不成立。
- `ln_deposit_balance`：在受控模型下通过完整调节机制判定，且结果集中于发明申请量。
- `ln_gdp_finance_src`：`fund_est_scale_cum × ln_gdp_finance_src` 对发明申请量显著，但债务压力对该变量不显著，不构成完整机制。

因此，本轮金融发展机制检验的分类结论是：

- 作为中介变量：全部不成立。
- 作为调节变量：`ln_deposit_balance` 在受控模型中成立，且只稳定体现在 `pat_invent_apply` 上。
- 写作建议：若要写“金融发展水平机制”，建议谨慎表述为“存款规模所代表的金融环境可能承接债务压力对基金创新效应的部分调节作用”；`fin_dev_1`、`fin_dev_2` 更适合作为异质性或边界条件补充，而非主机制。

## 7. 文件路径

- do 文件：`dachuang/运行日志与do代码/xtreg_mechanism_finance_dualmodel_ascii.do`
- log 文件：`dachuang/运行日志与do代码/xtreg_mechanism_finance_dualmodel_ascii.log`
- 结果 CSV：`dachuang/运行日志与do代码/xtreg_mechanism_finance_dualmodel_ascii_results.csv`
- 本报告：`dachuang/实证结果/xtreg_mechanism_finance_dualmodel_ascii.md`
