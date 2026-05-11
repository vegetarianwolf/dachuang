# 调节效应尝试：财政压力与债务压力对基金规模-创新关系的影响

## 本次操作
- 使用数据：`面板数据/地级市总面板_2015_2024_英文版.csv`
- 回归方法：地级市固定效应 + 年份固定效应（`xtreg, fe`）
- 标准误：按城市聚类稳健标准误
- 时间范围：2015-2024
- 说明：本次只围绕前一轮基准回归中更有信号的基金规模变量和创新产出变量，尝试加入财政压力、债务压力及其滞后一期作为调节变量。

## 数据与样本
- 因变量：
  - `pat_invent_apply`（发明申请量）
  - `pat_utility_apply`（实用新型申请量）
  - `pat_apply_total`（专利申请总量）
- 核心解释变量：
  - `fund_est_count`（基金当年设立数量）
  - `fund_est_scale_cum`（基金累计设立规模）
- 调节变量：
  - `fiscal_pressure`
  - `fiscal_pressure_l1`
  - `debt_pressure`
  - `debt_pressure_l1`
- 控制变量版本额外加入：
  - `ln_gdp`
  - `ln_fiscal_scitech`
  - `ln_pop`
  - `ln_secondary`
  - `ln_fdi`

## 模型设定
- 无控制调节模型：
  - `xtreg y c.x##c.m i.year, fe vce(cluster city_id)`
- 加控制变量调节模型：
  - `xtreg y c.x##c.m ctrls i.year, fe vce(cluster city_id)`
- 关注重点：交互项 `c.x#c.m` 的符号、显著性和稳健性。

## 回归结果

### 1. 债务压力的调节效应

#### 1.1 `fund_est_count` × `debt_pressure`
- `pat_apply_total`
  - 无控制：交互项 `b=0.4501`, `p=0.0355`, `N=1861`
- `pat_invent_apply`
  - 无控制：交互项 `b=0.1638`, `p=0.0685`, `N=1861`
- `pat_utility_apply`
  - 无控制：交互项 `b=0.2486`, `p=0.0049`, `N=1861`
- 加控制变量后，这组交互项整体不再稳健。

#### 1.2 `fund_est_scale_cum` × `debt_pressure`
- `pat_apply_total`
  - 无控制：交互项 `b=-5.95e-05`, `p<0.001`, `N=1763`
  - 加控制：交互项 `b=-5.56e-05`, `p<0.001`, `N=917`
- `pat_invent_apply`
  - 无控制：交互项 `b=-1.38e-05`, `p<0.001`, `N=1763`
  - 加控制：交互项 `b=-1.45e-05`, `p<0.001`, `N=917`
- `pat_utility_apply`
  - 无控制：交互项 `b=-3.11e-05`, `p<0.001`, `N=1763`
  - 加控制：交互项 `b=-2.74e-05`, `p<0.001`, `N=917`

#### 1.3 `fund_est_scale_cum` × `debt_pressure_l1`
- `pat_apply_total`
  - 无控制：交互项 `b=-6.46e-05`, `p<0.001`, `N=1758`
  - 加控制：交互项 `b=-6.09e-05`, `p<0.001`, `N=914`
- `pat_invent_apply`
  - 无控制：交互项 `b=-1.48e-05`, `p<0.001`, `N=1758`
  - 加控制：交互项 `b=-1.62e-05`, `p<0.001`, `N=914`
- `pat_utility_apply`
  - 无控制：交互项 `b=-3.37e-05`, `p<0.001`, `N=1758`
  - 加控制：交互项 `b=-2.92e-05`, `p<0.001`, `N=914`

### 2. 财政压力的调节效应

#### 2.1 `fund_est_count` × `fiscal_pressure`
- 各因变量下，交互项均不显著。
- `fund_est_count` 与财政压力的调节关系目前不稳。

#### 2.2 `fund_est_scale_cum` × `fiscal_pressure`
- `pat_apply_total`
  - 无控制：交互项 `b=0.1833`, `p=0.0285`, `N=2318`
  - 加控制：交互项 `b=0.2919`, `p=0.0011`, `N=1083`
- `pat_invent_apply`
  - 无控制：交互项 `b=0.0555`, `p=0.0268`, `N=2318`
  - 加控制：交互项 `b=0.0858`, `p<0.001`, `N=1083`
- `pat_utility_apply`
  - 无控制：交互项 `b=0.0906`, `p=0.0188`, `N=2318`
  - 加控制：交互项 `b=0.1211`, `p=0.0010`, `N=1083`

#### 2.3 `fund_est_scale_cum` × `fiscal_pressure_l1`
- `pat_apply_total`
  - 无控制：交互项 `b=0.2094`, `p=0.0021`, `N=2318`
  - 加控制：交互项 `b=0.2930`, `p<0.001`, `N=1083`
- `pat_invent_apply`
  - 无控制：交互项 `b=0.0640`, `p=0.0147`, `N=2318`
  - 加控制：交互项 `b=0.0887`, `p<0.001`, `N=1083`
- `pat_utility_apply`
  - 无控制：交互项 `b=0.1003`, `p<0.001`, `N=2318`
  - 加控制：交互项 `b=0.1235`, `p<0.001`, `N=1083`

## 简要解读
- 最稳定的调节效应来自 `fund_est_scale_cum`（基金累计设立规模）这一口径。
- 当调节变量是 `debt_pressure` 或 `debt_pressure_l1` 时，交互项在三个创新产出变量下都呈现稳定的负向显著结果，说明债务压力越高，累计基金规模促进创新的作用越弱。
- 当调节变量是 `fiscal_pressure` 或 `fiscal_pressure_l1` 时，`fund_est_scale_cum` 的交互项却呈现正向显著，这与“财政压力削弱基金作用”的预期并不一致，需要进一步核对财政压力指标方向与经济含义。
- `fund_est_count` 与财政压力的交互整体不稳，而与债务压力的交互只在无控制模型里有部分显著，稳健性不如累计规模口径。
- 因此，现阶段最值得重点推进的正式调节模型是：
  - `fund_est_scale_cum × debt_pressure`
  - `fund_est_scale_cum × debt_pressure_l1`

## 输出文件
- do 文件：`运行日志与do代码/xtreg_fe_moderation_fiscal_debt_combo_ascii.do`
- log 文件：`运行日志与do代码/xtreg_fe_moderation_fiscal_debt_combo_ascii.log`
- 结果表：`运行日志与do代码/xtreg_fe_moderation_fiscal_debt_combo_ascii_results.csv`
