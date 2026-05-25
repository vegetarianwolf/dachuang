# 地级市金融发展机制检验：基准调节负向显著严格筛选版

## 1. 筛选口径修正

此前综合版主要限定了两步机制方向：

```text
X × D -> M < 0
M -> Y > 0
```

但完整机制检验还应先满足基准调节项成立，即基准结果方程中的 `X × D -> Y` 必须负向显著。因此本版采用更严格的三重筛选规则：

```text
beta3: X × D -> Y < 0，且显著
a3:    X × D -> M < 0，且显著
c4:    M -> Y     > 0，且显著
```

其中，基准方程和结果方程均保留 `X`、`D`、`X × D`；结果方程额外加入金融发展变量 `M`。

## 2. 模型设定

基准调节方程：

```text
Y_it = beta0 + beta1 X_it + beta2 D_it + beta3 X_it * D_it + Controls_it + CityFE + YearFE + e_it
```

机制方程：

```text
M_it = a0 + a1 X_it + a2 D_it + a3 X_it * D_it + Controls_it + CityFE + YearFE + u_it
```

结果方程：

```text
Y_it = c0 + c1 X_it + c2 D_it + c3 X_it * D_it + c4 M_it + Controls_it + CityFE + YearFE + v_it
```

Stata 结果方程写法为：

```stata
xtreg yvar c.xvar##c.dvar mvar controls i.year, fe vce(cluster city_id)
```

因此，结果方程中确实包含 `X`、`D`、`X × D` 和 `M`。

## 3. 严格筛选后的结论

在加入“基准调节负向显著”这一硬条件后，原先推荐的 `fund_est_scale_cum × ln_debt_pressure_l1 -> asinh_fin_dev_2 -> ln(pat_apply_total+1)` 不再适合作为主结果，因为该组合的基准调节项 `beta3` 不显著。

严格筛选后，受控模型中仍可保留的结果主要集中在 `fin_dev_2` 口径，但 `M -> Y` 多为 10% 显著；若要求基准调节、机制方程、结果方程三步全部达到 5%，目前只剩未加控制变量模型。

## 4. 受控模型：基准调节 5% 负向显著 + 机制 5% 负向显著 + 结果方程 10% 正向显著

| 机制变量 | 含义 | X 口径 | D 口径 | Y 口径 | `beta3: X×D -> Y` | p值 | `a3: X×D -> M` | p值 | `c4: M -> Y` | p值 | N |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `d_ln_fin_dev_2` | 存款/GDP 增速 | `z_w_fund_est_scale_cum` | `debt_pressure` | `pat_apply_total` | -6.2443 | 0.0012 | -0.00000577 | 0.0106 | 11875.5119 | 0.0646 | 784 |
| `d_ln_fin_dev_2` | 存款/GDP 增速 | `z_w_fund_est_scale_cum` | `debt_pressure` | `pat_utility_apply` | -3.5167 | 0.0001 | -0.00000577 | 0.0106 | 6727.2417 | 0.0778 | 784 |
| `asinh_fin_dev_2` | 存款/GDP 水平 | `ln_fund` | `ln_debt_pressure_l1` | `ln(pat_apply_total+1)` | -0.0069 | 0.0314 | -0.001815 | 0.0373 | 0.3413 | 0.0856 | 944 |
| `ln_fin_dev_2` | 存款/GDP 水平 | `ln_fund` | `ln_debt_pressure_l1` | `ln(pat_apply_total+1)` | -0.0069 | 0.0314 | -0.001319 | 0.0415 | 0.4553 | 0.0894 | 944 |

这四条都满足基准调节负向显著和机制方程负向显著；结果方程中金融发展变量均为正向，显著性达到 10% 水平。

## 5. 三步全部 5% 显著的结果

若要求 `beta3`、`a3` 和 `c4` 三步全部达到 5% 显著，目前筛选结果只剩未加控制变量模型：

| spec | 机制变量 | 含义 | X 口径 | D 口径 | Y 口径 | `beta3: X×D -> Y` | p值 | `a3: X×D -> M` | p值 | `c4: M -> Y` | p值 | N |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| noctrl | `d_ln_fin_dev_2` | 存款/GDP 增速 | `z_w_fund_est_scale_cum` | `debt_pressure` | `pat_apply_total` | -7.4701 | 0.0001 | -0.00000824 | 0.0006 | 7925.0889 | 0.0415 | 1547 |
| noctrl | `d_ln_fin_dev_2` | 存款/GDP 增速 | `z_w_fund_est_scale_cum` | `debt_pressure` | `pat_utility_apply` | -4.3117 | 0.0000 | -0.00000824 | 0.0006 | 3985.2562 | 0.0392 | 1547 |

这两条统计显著性最强，但由于未加入控制变量，只适合作为附录或补充说明，不建议作为正文主机制。

## 6. 推荐写作口径

正文建议使用较稳妥的受控模型 10% 结果：

```text
ln_fund × ln_debt_pressure_l1
    -> asinh(fin_dev_2) 或 ln_fin_dev_2
    -> ln(pat_apply_total + 1)
```

可写为：

> 在基准调节项负向显著的前提下，进一步检验金融发展机制发现，政府投资基金规模与滞后债务压力的交互项对存款/GDP 口径的金融发展水平具有显著负向影响；同时，金融发展水平对总专利申请对数具有正向影响，并在 10% 水平上显著。该结果说明，债务压力可能通过削弱地区金融发展环境，抑制政府投资基金对创新产出的促进作用。

若必须要求三步均达到 5% 显著，则只能使用未加控制变量的 `d_ln_fin_dev_2` 增速口径，并应在文中明确其稳健性弱于受控模型。

## 7. 原综合版需要修正的地方

原综合版中 `fund_est_scale_cum × ln_debt_pressure_l1 -> asinh_fin_dev_2 -> ln(pat_apply_total+1)` 虽然满足 4.1 负向和 4.2 正向，但基准调节项 `beta3` 不显著，不能作为严格意义上的完整机制主结果。

因此，严格版主结果应改为：

```text
ln_fund × ln_debt_pressure_l1
    -> asinh_fin_dev_2 / ln_fin_dev_2
    -> ln(pat_apply_total + 1)
```

或作为增速机制：

```text
z_w_fund_est_scale_cum × debt_pressure
    -> d_ln_fin_dev_2
    -> pat_apply_total / pat_utility_apply
```

## 8. 数据来源文件

- 4.1 负向机制方程结果：`dachuang/实证结果/中间结果/xtreg_mediation_findev_transform_negative_20260516.md`
- 4.2 正向结果方程结果：`dachuang/实证结果/中间结果/xtreg_mediation_findev_step42_positive_focused_20260518.md`
- 4.2 筛选结果 CSV：`dachuang/运行日志与do代码/xtreg_mediation_findev_step42_positive_focused_20260518_selected.csv`
- 本严格筛选文档：`dachuang/实证结果/可用结果/xtreg_mediation_findev_theory_consistent_strict_baseline_negative_20260525.md`
