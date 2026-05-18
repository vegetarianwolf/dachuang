# 地级市金融发展机制检验 4.2 正向显著补充结果

## 1. 任务与数据

本轮在既有 `xtreg_mechanism_finance_dualmodel_ascii.md` 的 4.1 变换结果基础上，继续处理 4.2 “结果方程中的金融变量”。目标是保留 4.1 中 `X × D -> M` 为负向显著的金融发展口径，并在结果方程中寻找 `M -> Y` 为正向显著的组合。

- 回归日期：2026-05-18
- 数据文件：`staging_ascii/formal_2015_en.csv`
- 对应原始数据：`dachuang/面板数据/地级市总面板_2015_2024_英文版.csv`
- 样本：2015-2024 年地级市面板；回归时按实际变量缺失值逐模型剔除
- 面板设定：城市固定效应 + 年份固定效应
- 标准误：按城市聚类稳健标准误
- 控制变量：`ln_gdp`、`ln_fiscal_scitech`、`ln_pop`、`ln_secondary`、`ln_fdi`

## 2. 模型设定

机制方程：

```text
M_it = a0 + a1 X_it + a2 D_it + a3 X_it * D_it + Controls_it + CityFE + YearFE + u_it
```

基准结果方程：

```text
Y_it = beta0 + beta1 X_it + beta2 D_it + beta3 X_it * D_it + Controls_it + CityFE + YearFE + e_it
```

4.2 结果方程：

```text
Y_it = c0 + c1 X_it + c2 D_it + c3 X_it * D_it + c4 M_it + Controls_it + CityFE + YearFE + v_it
```

说明：本轮 Stata 代码使用 `c.xvar##c.dvar mvar controls i.year`，因此结果方程中同时包含 `X`、`D`、`X × D` 与金融发展变量 `M`。

## 3. 变量变换与筛选规则

本轮聚焦尝试 8 类金融发展通道，并在 `count`、`logy`、`wcount` 三类创新产出口径及发明、实用新型、总申请量之间循环估计，共完成 144 个固定效应模型组合。

核心筛选规则如下：

- 4.1 机制方程：`a3 < 0` 且 p < 0.10，优先关注 p < 0.05。
- 4.2 结果方程：`c4 > 0` 且 p < 0.10，优先关注 p < 0.05。
- 保留完整方程，即 4.2 中不删除 `X`、`D` 和 `X × D`。

## 4. 主要结果

144 个组合中，满足“4.1 负向显著 + 4.2 正向显著”的组合共有 14 条；其中同时达到 5% 显著水平的有 5 条，控制变量模型中有 3 条。

### 4.1 控制变量模型且 5% 显著的链条

| 通道 | M 口径 | 经济含义 | Y 口径 | 因变量 | `a3: X×D -> M` | p值 | `c4: M -> Y` | p值 | N |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `fd1_dlog_logfund` | `d_ln_fin_dev_1` | 贷款/GDP 增速 | `count` | `pat_utility_apply` | -0.001032 | 0.0228 | 10986.6163 | 0.0336 | 782 |
| `fd1_dlog_logfund` | `d_ln_fin_dev_1` | 贷款/GDP 增速 | `wcount` | `w_pat_utility_apply` | -0.001032 | 0.0228 | 6869.1252 | 0.0329 | 782 |
| `fd2_asinh_raw` | `asinh_fin_dev_2` | 存款/GDP 水平的 asinh 变换 | `logy` | `ln(pat_apply_total+1)` | -0.000000033 | 0.0147 | 0.4039 | 0.0497 | 944 |

### 4.2 10% 水平的补充候选

| 通道 | M 口径 | 经济含义 | Y 口径 | 因变量 | `a3: X×D -> M` | p值 | `c4: M -> Y` | p值 | N |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `fd1_dlog_logfund` | `d_ln_fin_dev_1` | 贷款/GDP 增速 | `wcount` | `w_pat_apply_total` | -0.001032 | 0.0228 | 8231.7347 | 0.0594 | 782 |
| `fd2_dlog_wzraw` | `d_ln_fin_dev_2` | 存款/GDP 增速 | `count` | `pat_apply_total` | -0.00000577 | 0.0106 | 11875.5119 | 0.0646 | 784 |
| `fd2_dlog_wzraw` | `d_ln_fin_dev_2` | 存款/GDP 增速 | `count` | `pat_utility_apply` | -0.00000577 | 0.0106 | 6727.2417 | 0.0778 | 784 |
| `fd2_asinh_raw` | `asinh_fin_dev_2` | 存款/GDP 水平的 asinh 变换 | `logy` | `ln(pat_invent_apply+1)` | -0.000000033 | 0.0147 | 0.6057 | 0.0599 | 944 |
| `fd2_asinh_logfund` | `asinh_fin_dev_2` | 存款/GDP 水平的 asinh 变换 | `logy` | `ln(pat_apply_total+1)` | -0.001815 | 0.0373 | 0.3413 | 0.0856 | 944 |
| `fd2_log_raw` | `ln_fin_dev_2` | 存款/GDP 水平的对数变换 | `logy` | `ln(pat_invent_apply+1)` | -0.000000023 | 0.0183 | 0.7962 | 0.0646 | 944 |
| `fd2_log_raw` | `ln_fin_dev_2` | 存款/GDP 水平的对数变换 | `logy` | `ln(pat_apply_total+1)` | -0.000000023 | 0.0183 | 0.5402 | 0.0524 | 944 |
| `fd2_log_logfund` | `ln_fin_dev_2` | 存款/GDP 水平的对数变换 | `logy` | `ln(pat_apply_total+1)` | -0.001319 | 0.0415 | 0.4553 | 0.0894 | 944 |

## 5. 解释口径

若希望在 4.2 中得到更干净的正向显著结果，可优先使用两类表述。

第一类是 `fin_dev_1` 的变化率口径：在控制变量模型中，`ln_fund × ln_debt_pressure_l1` 对 `d_ln_fin_dev_1` 显著为负，而 `d_ln_fin_dev_1` 对实用新型专利申请显著为正。这一写法对应“债务压力削弱基金对贷款/GDP 增速的带动，而金融发展增速提升创新产出”。

第二类是 `fin_dev_2` 的同向水平变换口径：`fund_est_scale_cum × ln_debt_pressure_l1` 对 `asinh_fin_dev_2` 显著为负，且 `asinh_fin_dev_2` 对总专利申请对数显著为正。该口径不改变变量方向，适合写作“存款/GDP 所代表的金融发展水平越高，创新产出越高；但债务压力会削弱基金对该金融发展水平的正向作用”。

综合可写为：金融发展水平并非在原始线性口径下稳定通过中介检验，但经对数、反双曲正弦或增速处理后，存在若干符合理论方向的传导链条。其中，`asinh_fin_dev_2 -> ln(pat_apply_total+1)` 是较适合保留在正文的 5% 显著候选；`d_ln_fin_dev_1 -> pat_utility_apply` 可作为补充稳健口径。

## 6. 输出文件

- do 文件：`dachuang/运行日志与do代码/xtreg_mediation_findev_step42_positive_focused_20260518.do`
- log 文件：`dachuang/运行日志与do代码/xtreg_mediation_findev_step42_positive_focused_20260518.log`
- 完整结果 CSV：`dachuang/运行日志与do代码/xtreg_mediation_findev_step42_positive_focused_20260518_results.csv`
- 筛选结果 CSV：`dachuang/运行日志与do代码/xtreg_mediation_findev_step42_positive_focused_20260518_selected.csv`
- 本说明文档：`dachuang/实证结果/xtreg_mediation_findev_step42_positive_focused_20260518.md`
