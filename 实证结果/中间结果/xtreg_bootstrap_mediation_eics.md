# Bootstrap 中介检验：早期投资事件占比

回归日期：2026-05-15

任务摘要：在既有显著的债务压力负向调节模型基础上，检验 `early_inv_count_share` 是否中介债务压力对基金规模创新效应的影响，并同时报告：

- `a2 × b4`：债务压力水平效应的间接效应
- `a3 × b4`：债务压力负向调节效应的间接效应

实际使用文件：

- [地级市总面板_2015_2024_英文版.csv](</c:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang/面板数据/地级市总面板_2015_2024_英文版.csv>)

代码与日志：

- [xtreg_bootstrap_mediation_eics.do](</c:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang/运行日志与do代码/xtreg_bootstrap_mediation_eics.do>)
- [xtreg_bootstrap_mediation_eics.log](</c:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang/运行日志与do代码/xtreg_bootstrap_mediation_eics.log>)
- [xtreg_bootstrap_mediation_eics_results.csv](</c:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang/运行日志与do代码/xtreg_bootstrap_mediation_eics_results.csv>)

模型说明：

- 面板模型：城市固定效应 + 年份固定效应
- 标准误：基准回归与路径回归使用城市聚类稳健标准误
- bootstrap：按城市进行手工 cluster bootstrap，`reps=2000`
- 机制变量：`early_inv_count_share`
- 控制变量：`ln_gdp`、`ln_fiscal_scitech`、`ln_pop`、`ln_secondary`、`ln_fdi`

样本筛选：

- 仅保留 `Y`、`D`、`fund_est_scale_cum`、`early_inv_count_share` 及全部控制变量非缺失的城市-年份样本
- `pat_invent_apply` 口径下：
  - `debt_pressure` 样本量 `379`
  - `debt_pressure_l1` 样本量 `385`
- `pat_apply_total` 口径下：
  - `debt_pressure` 样本量 `379`
  - `debt_pressure_l1` 样本量 `385`

## 结果

### 1. `pat_invent_apply` + `debt_pressure`

- 基准负向调节项 `β3 = -1.2870e-05`，`p = 0.0010`
- 机制方程 `a2 = 0.0001142`，`p = 0.2654`
- 机制方程 `a3 = 1.3244e-10`，`p = 0.3445`
- 结果方程 `b4 = -537.0090`，`p = 0.3309`
- 加入中介后 `c3 = -1.2799e-05`，`p = 0.0011`
- bootstrap `a2 × b4 = -0.0682`
  - 95% CI `[-0.3554, 0.1221]`
- bootstrap `a3 × b4 = -1.0270e-07`
  - 95% CI `[-6.1143e-07, 1.6022e-07]`

判定：

- 主负向调节效应稳健存在
- 无论是 `a2 × b4` 还是 `a3 × b4`，置信区间都跨 `0`
- 不支持 `early_inv_count_share` 为显著中介渠道

### 2. `pat_invent_apply` + `debt_pressure_l1`

- 基准负向调节项 `β3 = -1.5671e-05`，`p = 0.0010`
- 机制方程 `a2 = 0.0001204`，`p = 0.1404`
- 机制方程 `a3 = 2.2522e-11`，`p = 0.8719`
- 结果方程 `b4 = -340.7807`，`p = 0.5437`
- 加入中介后 `c3 = -1.5664e-05`，`p = 0.0010`
- bootstrap `a2 × b4 = -0.0459`
  - 95% CI `[-0.2886, 0.1154]`
- bootstrap `a3 × b4 = -1.2170e-08`
  - 95% CI `[-3.1441e-07, 2.5639e-07]`

判定：

- 负向调节项依然稳健
- `early_inv_count_share` 的中介效应不显著

### 3. `pat_apply_total` + `debt_pressure`

- 基准负向调节项 `β3 = -3.6554e-05`，`p = 0.0222`
- 机制方程 `a2 = 0.0001142`，`p = 0.2654`
- 机制方程 `a3 = 1.3244e-10`，`p = 0.3445`
- 结果方程 `b4 = 1195.1054`，`p = 0.4657`
- 加入中介后 `c3 = -3.6712e-05`，`p = 0.0224`
- bootstrap `a2 × b4 = 0.1162`
  - 95% CI `[-0.3478, 0.8838]`
- bootstrap `a3 × b4 = 1.2011e-07`
  - 95% CI `[-7.6111e-07, 1.2603e-06]`

判定：

- 主调节项显著为负
- 中介链条不显著

### 4. `pat_apply_total` + `debt_pressure_l1`

- 基准负向调节项 `β3 = -4.2098e-05`，`p = 0.0220`
- 机制方程 `a2 = 0.0001204`，`p = 0.1404`
- 机制方程 `a3 = 2.2522e-11`，`p = 0.8719`
- 结果方程 `b4 = 1431.1627`，`p = 0.3885`
- 加入中介后 `c3 = -4.2130e-05`，`p = 0.0220`
- bootstrap `a2 × b4 = 0.1778`
  - 95% CI `[-0.2464, 1.0003]`
- bootstrap `a3 × b4 = 8.0919e-09`
  - 95% CI `[-8.3186e-07, 8.6866e-07]`

判定：

- 负向调节项继续显著
- 中介效应仍不成立

## 总体解释

这组结果给出的信息非常一致：

- 你们原先最重要的结论仍然成立：债务压力显著削弱了基金累计规模促进创新的作用。
- 但 `early_inv_count_share` 无论作为“债务压力水平效应”的中介，还是作为“债务压力负向调节效应”的中介，bootstrap 结果都没有通过。
- 加入 `early_inv_count_share` 后，`X × N` 的系数几乎没有缩小，说明这条变量并没有实质性解释掉原有负向调节效应。

因此，按这轮回归结果，更稳妥的论文写法应是：

- 保留“债务压力负向调节基金促创新作用”作为主结论；
- 将 `early_inv_count_share` 写成一项正式但未获稳健支持的补充机制检验；
- 不建议把它上升为主机制结论。

## 结论建议

如果正文需要一句概括，可写成：

> bootstrap 检验显示，早期投资事件占比并未形成债务压力负向调节效应的稳健中介渠道。尽管债务压力显著削弱了政府引导基金累计规模的创新促进作用，但这一作用并未通过城市层面的早期投资事件占比得到显著传导。
