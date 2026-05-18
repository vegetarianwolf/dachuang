# 早期投资作为调节变量的机制检验

## 本次操作
- 使用数据：`staging_ascii/panel_2015_2024_regression_ascii_clean.csv`
- 回归方法：地级市固定效应 + 年份固定效应（`xtreg, fe`）
- 标准误：按城市聚类稳健标准误
- 时间范围：2015-2024
- 说明：本次按“早期投资作为调节变量”的新设定，检验 `fund_est_scale_cum × debt_pressure × early_inv_*` 的三重交互。

## 数据与样本
- 因变量：
  - `pat_invent_apply`
  - `pat_utility_apply`
  - `pat_apply_total`
- 核心解释变量：
  - `fund_est_scale_cum`
- 调节变量：
  - `debt_pressure`
  - `debt_pressure_l1`
- 早期投资调节变量口径：
  - `early_inv_amt`
  - `early_inv_count`
- 控制变量：
  - `ln_gdp`
  - `ln_fiscal_scitech`
  - `ln_pop`
  - `ln_secondary`
  - `ln_fdi`

## 模型设定
采用三重交互形式：

`Y = fund_est_scale_cum × debt_pressure × early_inv + FE + controls`

其中重点看三重交互项 `fund_est_scale_cum#debt_pressure#early_inv` 是否显著。

## 回归结果

### 1. `early_inv_amt` 作为调节变量
- `pat_apply_total`
  - `debt_pressure`：加控制 `b3=-5.37e-08, p=0.0067, N=575`
  - `debt_pressure_l1`：加控制 `b3=-5.27e-08, p=0.0165, N=577`
- `pat_utility_apply`
  - `debt_pressure`：加控制 `b3=-3.32e-08, p=0.0052, N=575`
  - `debt_pressure_l1`：加控制 `b3=-3.11e-08, p=0.0039, N=577`
- `pat_invent_apply`
  - `debt_pressure_l1`：无控制 `b3=1.55e-08, p=0.0126, N=1035`
  - 其余不显著

### 2. `early_inv_count` 作为调节变量
- 三重交互项整体不显著
- 说明“早期投资事件数”作为调节变量的证据较弱

## 简要解读
- 如果把早期投资定义为**调节变量**，那么当前最有解释力的是 `early_inv_amt`，而不是 `early_inv_count`。
- `early_inv_amt` 在 `pat_apply_total` 和 `pat_utility_apply` 上的三重交互项多次显著为负，说明当早期投资金额更强时，债务压力对基金规模促进创新的抑制效应更明显。
- 这比前一轮把早期投资当“水平中介变量”的设定更贴近你们现在想要的“调节变量承担债务调节效应的传导机制”的解释。
- 但总体上，`early_inv_count` 的证据不强，因此若将早期投资写入正文主结果，建议优先使用 `early_inv_amt`。

## 输出文件
- do 文件：`运行日志与do代码/xtreg_fe_moderation_earlyinv_ascii.do`
- log 文件：`运行日志与do代码/xtreg_fe_moderation_earlyinv_ascii.log`
- 结果表：`运行日志与do代码/xtreg_fe_moderation_earlyinv_ascii_results.csv`
