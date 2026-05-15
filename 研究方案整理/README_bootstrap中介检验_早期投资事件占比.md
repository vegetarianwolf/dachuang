# 债务压力负向调节效应的 Bootstrap 中介检验方案：以早期投资事件占比为中介变量

## 1. 方案定位

本方案不是再做一遍普通的“基金规模 -> 创新产出”的传统三步中介，而是在你们已经得到显著结果的债务压力负向调节模型基础上，进一步检验：

`fund_est_scale_cum × debt_pressure`

对创新产出的负向调节效应，是否会通过

`early_inv_count_share`

这一机制变量发生中介传导。

因此，这里的计量逻辑更准确地说属于：

- `mediated moderation`
- 中文可表述为“债务压力调节效应的中介传导检验”

而不是简单的“债务压力是中介”或“早期投资事件占比是普通中介”。

## 2. 为什么单独写这一版

根据现有结果，债务压力负向调节效应本身已经较稳定，尤其集中在以下主线上：

- `pat_invent_apply`
- `pat_apply_total`

并且主要来自：

- `fund_est_scale_cum × debt_pressure`
- `fund_est_scale_cum × debt_pressure_l1`

同时，`early_inv_count_share` 已经作为机制变量做过初步检验，但现有结果更像“补充口径”，还没有经过正式的 bootstrap 间接效应检验。既然你现在希望把它写成一版更正式的中介检验方案，就应当把识别目标、样本口径和 bootstrap 实施方式单独固定下来。

## 3. 研究问题

本轮机制检验要回答的问题是：

1. 债务压力是否会削弱基金累计设立规模对创新产出的促进作用。
2. 这一负向调节效应，是否会通过降低或改变城市层面的早期投资事件占比而传导到创新产出。
3. 这种传导是否达到统计显著，能否通过 bootstrap 间接效应置信区间得到支持。

## 4. 核心变量设定

### 4.1 核心解释变量

- `X = fund_est_scale_cum`

含义：城市层面政府引导基金累计设立规模。

### 4.2 调节变量

- `N = debt_pressure`
- 稳健口径：`debt_pressure_l1`

含义：财政债务压力。

### 4.3 机制变量

- `M = early_inv_count_share`

含义：早期投资事件占比。按你已经确认的口径，早期事件仅包括：

- `种子期`
- `初创期`

该变量衡量的是一个城市在某一年中，政府引导基金投资事件里“投早”的事件占比。

### 4.4 被解释变量

建议优先按已有显著主结果排序：

1. `pat_invent_apply`
2. `pat_apply_total`
3. `pat_utility_apply`

其中前两项更适合写入主文，第三项可作为补充或扩展检验。

### 4.5 控制变量

与现有 `ctrl` 口径保持一致：

- `ln_gdp`
- `ln_fiscal_scitech`
- `ln_pop`
- `ln_secondary`
- `ln_fdi`

对应原始变量为：

- `gdp`
- `fiscal_scitech`
- `population_resident`
- `secondary_industry`
- `fdi_actual`

## 5. 推荐主样本与样本口径

为了和你们已经显著的调节模型完全对齐，本轮中介检验不建议重新随意换样本，而应直接沿用已有 `ctrl` 口径下的可比样本。

建议主报告分两组：

### 5.1 当期债务压力口径

- 机制变量：`early_inv_count_share`
- 调节变量：`debt_pressure`
- 主结果样本量：现有回归有效样本约为 `377`

### 5.2 滞后一期债务压力口径

- 机制变量：`early_inv_count_share`
- 调节变量：`debt_pressure_l1`
- 主结果样本量：现有回归有效样本约为 `383`

说明：

- 这里应以回归实际 `e(N)` 为最终报告样本量。
- 不建议把 `957` 条“仅早期投资事件占比非空”的样本直接作为正式回归样本口径，因为那里面不少观测缺少债务压力或控制变量。

## 6. 识别思路

本轮检验的核心不是看 `debt_pressure -> early_inv_count_share`，而是看：

`fund_est_scale_cum × debt_pressure`

这一交互项是否会先影响 `early_inv_count_share`，再由后者影响创新产出。

因此应采用两步模型：

### 6.1 机制方程

```text
M_it = a0 + a1 X_it + a2 N_it + a3 (X_it × N_it) + gamma Controls_it + city FE + year FE + u_it
```

这里重点关注：

- `a3`

其含义是：债务压力对基金规模创新效应的调节，是否已经先体现在“投早比例”上。

### 6.2 结果方程

```text
Y_it = b0 + b1 X_it + b2 N_it + b3 (X_it × N_it) + b4 M_it + gamma Controls_it + city FE + year FE + e_it
```

这里重点关注：

- `b4`
- 以及 `b3` 相对基准调节模型中的变化

其中：

- `b4` 反映早期投资事件占比是否进一步影响创新产出。
- 若加入 `M` 后，`X × N` 的系数绝对值缩小，说明债务压力负向调节效应有一部分通过 `M` 传导。

## 7. Bootstrap 检验对象

本轮 bootstrap 的核心不是单独检验 `a3` 或 `b4`，而是直接检验间接效应：

```text
Indirect Effect = a3 × b4
```

这才是“债务压力负向调节效应是否通过早期投资事件占比传导”的正式统计对象。

建议同时报告：

- `indirect effect = a3 × b4`
- `direct effect = b3`
- `total moderated effect = b3 + a3 × b4`

## 8. 结果判定标准

### 8.1 支持中介传导

若 bootstrap 得到的 `a3 × b4` 置信区间不包含 0，则说明：

- 债务压力负向调节效应存在显著的间接传导路径；
- 早期投资事件占比可以被写成一条正式机制链条。

### 8.2 仅部分支持

若：

- `a3 × b4` 点估计方向符合预期；
- 但 bootstrap 置信区间跨 0；
- 同时 `b3` 仍显著为负；

则可表述为：

- 早期投资事件占比具有一定传导迹象；
- 但证据不足以支持其为稳健主机制；
- 更适合作为补充机制或附录结果。

### 8.3 不支持中介传导

若 bootstrap 置信区间明显包含 0，且 `a3` 或 `b4` 缺乏稳定性，则应如实表述为：

- 早期投资事件占比并不能稳健中介债务压力的负向调节效应；
- 主结论仍应保留在“债务压力负向调节存在”这一层面；
- 机制部分可转而强调更稳的早期投资事件数或早期投资金额口径。

## 9. 与现有结果的衔接方式

根据目前已经跑出的结果，`early_inv_count_share` 这一路径有两个特点：

1. 它所在的结果方程里，`fund_est_scale_cum × debt_pressure` 的负向显著性还在，说明主调节结论较稳。
2. 但把它严格当作“中介变量”时，机制方程里的 `a3` 目前并不强。

这意味着：

- 这套 bootstrap 中介检验可以做；
- 但应在文稿里预先定位为“正式补充机制检验”，而不是最核心主机制；
- 若 bootstrap 不显著，不应硬写成成立，而应据此把 `early_inv_count_share` 退回到补充说明位置。

换句话说，这个方案最有价值的地方，不只是“证明它成立”，也包括“正式检验后排除它不够稳”。

## 10. 推荐的主文写法

建议把正文表述成：

> 在确认财政债务压力显著削弱政府引导基金累计设立规模的创新促进效应后，本文进一步考察该负向调节效应是否会通过改变引导基金的早期投资事件占比而传导至创新产出。为此，本文采用“调节效应的中介传导”框架，并以 bootstrap 方法直接检验交互项 `fund_est_scale_cum × debt_pressure` 的间接效应。

如果结果不显著，则建议改写成：

> bootstrap 检验显示，早期投资事件占比的间接效应置信区间跨 0，说明该变量尚不足以构成债务压力负向调节效应的稳健中介渠道。因此，本文将其保留为补充性机制证据，而不作为主机制结论。

## 11. Stata 实施模板

下面给出一版可直接改写为 `.do` 文件的模板思路。主样本优先用英文面板：

- `地级市总面板_2015_2024_英文版.csv`

### 11.1 先固定基准负向调节模型

```stata
xtreg pat_invent_apply c.fund_est_scale_cum##c.debt_pressure ///
    ln_gdp ln_fiscal_scitech ln_pop ln_secondary ln_fdi i.year, ///
    fe vce(cluster city_id)
```

### 11.2 机制方程

```stata
xtreg early_inv_count_share c.fund_est_scale_cum##c.debt_pressure ///
    ln_gdp ln_fiscal_scitech ln_pop ln_secondary ln_fdi i.year, ///
    fe vce(cluster city_id)
```

### 11.3 结果方程

```stata
xtreg pat_invent_apply c.fund_est_scale_cum##c.debt_pressure ///
    early_inv_count_share ///
    ln_gdp ln_fiscal_scitech ln_pop ln_secondary ln_fdi i.year, ///
    fe vce(cluster city_id)
```

### 11.4 Bootstrap 间接效应

建议自定义程序，返回：

- `a3`
- `b4`
- `indirect = a3*b4`
- `direct = b3`

伪代码如下：

```stata
capture program drop med_boot_eics
program define med_boot_eics, rclass
    xtset city_id year

    quietly xtreg early_inv_count_share ///
        c.fund_est_scale_cum##c.debt_pressure ///
        ln_gdp ln_fiscal_scitech ln_pop ln_secondary ln_fdi i.year, ///
        fe vce(cluster city_id)
    scalar a3 = _b[c.fund_est_scale_cum#c.debt_pressure]

    quietly xtreg pat_invent_apply ///
        c.fund_est_scale_cum##c.debt_pressure ///
        early_inv_count_share ///
        ln_gdp ln_fiscal_scitech ln_pop ln_secondary ln_fdi i.year, ///
        fe vce(cluster city_id)
    scalar b4 = _b[early_inv_count_share]
    scalar b3 = _b[c.fund_est_scale_cum#c.debt_pressure]

    return scalar indirect = a3 * b4
    return scalar direct = b3
    return scalar a3 = a3
    return scalar b4 = b4
end

bootstrap ///
    indirect = r(indirect) ///
    direct   = r(direct) ///
    a3       = r(a3) ///
    b4       = r(b4), ///
    reps(2000) seed(20260515) cluster(city_id): med_boot_eics
```

### 11.5 Bootstrap 细节建议

- 主报告：`reps(2000)`
- 稳健性：`reps(5000)`
- 按城市聚类抽样
- 报告 percentile CI 与 BCa CI

## 12. 建议的结果呈现顺序

建议结果呈现顺序固定为：

1. 基准负向调节模型仍显著。
2. 机制方程报告 `a3`。
3. 结果方程报告 `b4` 与新的 `b3`。
4. bootstrap 报告 `a3 × b4` 的点估计、标准误、95% 置信区间。
5. 最后再解释该机制是“成立”“部分成立”还是“不成立”。

## 13. 本方案的现实预期

从你们当前已有结果看，这个方案是可以成立为一版正式检验的，但应保持预期克制：

- 它最可能成为“补充机制检验”；
- 不一定能成为最强主机制；
- 若 bootstrap 间接效应不显著，也属于有价值的研究发现，因为它可以帮助你们把机制叙述从“早期投资事件占比”转向更稳的行为口径。

## 14. 推荐结论

如果你现在就是要落一版论文方案，我建议这样定位：

- 主结果仍然写“债务压力显著负向调节基金扶持创新效果”。
- `early_inv_count_share` 的 bootstrap 检验写成“正式补充中介检验”。
- 主报告优先聚焦：
  - `pat_invent_apply`
  - `pat_apply_total`
- `pat_utility_apply` 作为扩展项。

这样最稳，也最符合你们现有结果基础。
