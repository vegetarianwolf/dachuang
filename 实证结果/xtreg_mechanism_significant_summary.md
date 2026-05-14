# 机制检验显著结果汇总

## 本次汇总说明

- 基准主线固定为：`fund_est_scale_cum × debt_pressure` 和 `fund_est_scale_cum × debt_pressure_l1`
- 因变量主要看：`pat_invent_apply`、`pat_utility_apply`、`pat_apply_total`
- 机制模型分为两类：
  - 模型 A：`X × N -> M -> Y`
  - 模型 B：先检验 `N -> M`，再在结果方程中加入 `X × M`
- 本文档只汇总**最有代表性的显著结果**，不再展开全部 608 行结果

完整结果仍保存在：

- [xtreg_mechanism_dualmodel_focus_overview.md](</c:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang/实证结果/xtreg_mechanism_dualmodel_focus_overview.md>)
- [xtreg_mechanism_early_dualmodel_focus.md](</c:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang/实证结果/xtreg_mechanism_early_dualmodel_focus.md>)
- [xtreg_mechanism_soccap_dualmodel_focus.md](</c:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang/实证结果/xtreg_mechanism_soccap_dualmodel_focus.md>)
- [xtreg_mechanism_fc_dualmodel_focus.md](</c:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang/实证结果/xtreg_mechanism_fc_dualmodel_focus.md>)

## 一、早期投资机制

### 1. 机制变量作为中介传导变量

最强的口径是 `early_inv_count` 和 `early_inv_amt`，但 `early_inv_amt_share` 也有一定信号。

#### `early_inv_count`

- `pat_apply_total` + `debt_pressure` + `ctrl`
  - `fund_est_scale_cum × debt_pressure`：`b=-3.6393e-05`，`p=0.00081`
  - `early_inv_count`：`b=269.1425`，`p=1.49e-05`
- `pat_apply_total` + `debt_pressure_l1` + `ctrl`
  - `fund_est_scale_cum × debt_pressure_l1`：`b=-3.5616e-05`，`p=0.00132`
  - `early_inv_count`：`b=290.1339`，`p=2.31e-08`
- `pat_invent_apply` + `debt_pressure` + `ctrl`
  - `fund_est_scale_cum × debt_pressure`：`b=-1.2719e-05`，`p=6.25e-08`
  - `early_inv_count`：`b=72.2107`，`p=1.53e-09`
- `pat_invent_apply` + `debt_pressure_l1` + `ctrl`
  - `fund_est_scale_cum × debt_pressure_l1`：`b=-1.3493e-05`，`p=2.68e-07`
  - `early_inv_count`：`b=80.4649`，`p=7.69e-14`

这组结果说明：如果把早期投资事件数看成机制水平变量，它在结果方程里非常强，且与发明专利、总专利的关系最稳定。

#### `early_inv_amt`

- `pat_invent_apply` + `debt_pressure` + `noctrl`
  - `fund_est_scale_cum × debt_pressure`：`b=-1.1365e-05`，`p=0.0107`
  - `early_inv_amt`：`b=0.1746`，`p=0.0194`
- `pat_invent_apply` + `debt_pressure_l1` + `noctrl`
  - `fund_est_scale_cum × debt_pressure_l1`：`b=-1.1903e-05`，`p=0.0154`
  - `early_inv_amt`：`b=0.1808`，`p=0.0269`
- `pat_apply_total` + `debt_pressure_l1` + `ctrl`
  - `fund_est_scale_cum × debt_pressure_l1`：`b=-4.4810e-05`，`p=0.0436`
  - `early_inv_amt`：`b=2.3445`，`p=0.0939`

如果更强调“早期投资金额”而不是事件数，这组结果也有一定支持，尤其在发明专利上较明显。

#### `early_inv_amt_share`

- 机制方程：`debt_pressure` + `ctrl`
  - `fund_est_scale_cum × debt_pressure -> early_inv_amt_share`：`b=5.1252e-10`，`p=0.00069`
- 机制方程：`debt_pressure` + `noctrl`
  - `fund_est_scale_cum × debt_pressure -> early_inv_amt_share`：`b=3.4933e-10`，`p=0.00773`
- 机制方程：`debt_pressure_l1` + `ctrl`
  - `fund_est_scale_cum × debt_pressure_l1 -> early_inv_amt_share`：`b=2.8258e-10`，`p=0.0548`
- `pat_invent_apply` + `debt_pressure` + `noctrl`
  - `fund_est_scale_cum × debt_pressure`：`b=-1.2967e-05`，`p=0.0226`
- `pat_invent_apply` + `debt_pressure_l1` + `ctrl`
  - `fund_est_scale_cum × debt_pressure_l1`：`b=-1.5081e-05`，`p=0.0401`

这说明“早期投资金额占比”在机制方程里是有信号的，但进入结果方程后，其自身系数并不像 `early_inv_count` 或 `early_inv_amt` 那样稳定。

#### `early_inv_count_share`

- `pat_invent_apply` + `debt_pressure` + `ctrl`
  - `fund_est_scale_cum × debt_pressure`：`b=-1.2792e-05`，`p=0.00110`
- `pat_invent_apply` + `debt_pressure` + `noctrl`
  - `fund_est_scale_cum × debt_pressure`：`b=-1.4045e-05`，`p=6.14e-05`
- `pat_invent_apply` + `debt_pressure_l1` + `ctrl`
  - `fund_est_scale_cum × debt_pressure_l1`：`b=-1.5648e-05`，`p=0.00099`
- `pat_apply_total` + `debt_pressure_l1` + `ctrl`
  - `fund_est_scale_cum × debt_pressure_l1`：`b=-4.2047e-05`，`p=0.0222`

但需要注意：这组结果更多体现为原始债务调节项持续显著，`early_inv_count_share` 自己在结果方程中的系数并不稳，因此它更适合作为补充口径，而不是主口径。

### 2. 机制变量作为调节变量

最强的口径是 `early_inv_count`，其次是 `early_inv_amt`。

#### `early_inv_count`

- `pat_utility_apply` + `debt_pressure` + `ctrl`
  - `fund_est_scale_cum × debt_pressure`：`b=-2.1520e-05`，`p=0.00092`
  - `early_inv_count`：`b=263.5790`，`p=0.00068`
  - `fund_est_scale_cum × early_inv_count`：`b=-0.0001610`，`p=0.00265`
- `pat_utility_apply` + `debt_pressure_l1` + `ctrl`
  - `fund_est_scale_cum × debt_pressure_l1`：`b=-2.0888e-05`，`p=0.00208`
  - `early_inv_count`：`b=277.3035`，`p=8.36e-05`
  - `fund_est_scale_cum × early_inv_count`：`b=-0.0001581`，`p=0.00082`
- `pat_utility_apply` + `debt_pressure` + `noctrl`
  - `fund_est_scale_cum × debt_pressure`：`b=-2.0227e-05`，`p=0.00079`
  - `early_inv_count`：`b=330.2449`，`p=1.45e-05`
  - `fund_est_scale_cum × early_inv_count`：`b=-0.0002150`，`p=4.28e-07`

这组结果很强，说明若把“早期投资事件数”理解成调节变量，它会显著改变基金规模对实用新型创新的影响强弱。

#### `early_inv_amt`

- `pat_apply_total` + `debt_pressure` + `ctrl`
  - `fund_est_scale_cum × debt_pressure`：`b=-4.4870e-05`，`p=0.0241`
  - `early_inv_amt`：`b=6.5786`，`p=0.00026`
  - `fund_est_scale_cum × early_inv_amt`：`b=-9.4155e-06`，`p=0.0145`
- `pat_apply_total` + `debt_pressure_l1` + `ctrl`
  - `fund_est_scale_cum × debt_pressure_l1`：`b=-4.8766e-05`，`p=0.0229`
  - `early_inv_amt`：`b=6.6578`，`p=0.00086`
  - `fund_est_scale_cum × early_inv_amt`：`b=-9.4571e-06`，`p=0.0379`
- `pat_utility_apply` + `debt_pressure` + `ctrl`
  - `fund_est_scale_cum × debt_pressure`：`b=-1.9248e-05`，`p=0.0504`
  - `early_inv_amt`：`b=4.6485`，`p=0.00278`
  - `fund_est_scale_cum × early_inv_amt`：`b=-7.1390e-06`，`p=0.00392`

如果正文更想强调“早期投资偏好”而不是“早期投资水平”，`early_inv_amt` 和 `early_inv_count` 都能支撑，但 `early_inv_count` 的统计强度更高。

#### `early_inv_amt_share`

- 机制方程：`debt_pressure_l1` + `ctrl`
  - `debt_pressure_l1 -> early_inv_amt_share`：`b=0.0002118`，`p=0.00702`
- 机制方程：`debt_pressure` + `ctrl`
  - `debt_pressure -> early_inv_amt_share`：`b=0.0002204`，`p=0.0117`
- `pat_invent_apply` + `debt_pressure_l1` + `ctrl`
  - `fund_est_scale_cum × debt_pressure_l1`：`b=-1.3138e-05`，`p=0.0839`
  - `fund_est_scale_cum × early_inv_amt_share`：`b=-0.008783`，`p=0.0399`

这说明如果把“早期投资金额占比”理解成调节变量，也能找到一定支持，但整体显著性强度仍弱于 `early_inv_count` 和 `early_inv_amt`。

#### `early_inv_count_share`

- 机制方程：`debt_pressure` + `ctrl`
  - `debt_pressure -> early_inv_count_share`：`b=0.0001613`，`p=0.0202`
- 机制方程：`debt_pressure_l1` + `ctrl`
  - `debt_pressure_l1 -> early_inv_count_share`：`b=0.0001209`，`p=0.0161`
- `pat_invent_apply` + `debt_pressure` + `ctrl`
  - `fund_est_scale_cum × debt_pressure`：`b=-1.1527e-05`，`p=0.00830`
  - `fund_est_scale_cum × early_inv_count_share`：`b=-0.03663`，`p=0.0746`

这组结果说明“早期投资事件占比”作为调节变量也有一定信号，但仍属于次优口径。

## 二、社会资本撬动效率机制

### 1. 机制变量作为中介传导变量

最值得优先看的不是 `soccap_leverage`，而是 `gp_amt`、`matched_commit_amt`、`gov_amt`、`fund_commit_total`。

#### `gp_amt`

- `pat_invent_apply` + `debt_pressure` + `ctrl`
  - `fund_est_scale_cum × debt_pressure`：`b=-1.3763e-05`，`p=0.00074`
  - `gp_amt`：`b=-0.003862`，`p=1.92e-05`
- `pat_invent_apply` + `debt_pressure_l1` + `ctrl`
  - `fund_est_scale_cum × debt_pressure_l1`：`b=-1.6757e-05`，`p=0.00036`
  - `gp_amt`：`b=-0.004188`，`p=3.51e-07`
- `pat_invent_apply` + `debt_pressure` + `noctrl`
  - `fund_est_scale_cum × debt_pressure`：`b=-1.3826e-05`，`p=0.00044`
  - `gp_amt`：`b=-0.002125`，`p=0.00609`

#### `matched_commit_amt`

- `pat_invent_apply` + `debt_pressure` + `noctrl`
  - `fund_est_scale_cum × debt_pressure`：`b=-1.4689e-05`，`p=0.00015`
  - `matched_commit_amt`：`b=-0.000709`，`p=9.25e-07`
- `pat_invent_apply` + `debt_pressure_l1` + `noctrl`
  - `fund_est_scale_cum × debt_pressure_l1`：`b=-1.5581e-05`，`p=0.00016`
  - `matched_commit_amt`：`b=-0.000702`，`p=9.35e-06`
- `pat_apply_total` + `debt_pressure_l1` + `ctrl`
  - `fund_est_scale_cum × debt_pressure_l1`：`b=-4.1107e-05`，`p=0.0313`
  - `matched_commit_amt`：`b=0.001347`，`p=0.00157`

#### `gov_amt`

- `pat_invent_apply` + `debt_pressure` + `noctrl`
  - `fund_est_scale_cum × debt_pressure`：`b=-1.4596e-05`，`p=0.00020`
  - `gov_amt`：`b=-0.000825`，`p=0.00011`
- `pat_invent_apply` + `debt_pressure_l1` + `noctrl`
  - `fund_est_scale_cum × debt_pressure_l1`：`b=-1.5454e-05`，`p=0.00022`
  - `gov_amt`：`b=-0.000810`，`p=0.00051`
- `pat_apply_total` + `debt_pressure_l1` + `ctrl`
  - `fund_est_scale_cum × debt_pressure_l1`：`b=-4.0125e-05`，`p=0.0289`
  - `gov_amt`：`b=0.002140`，`p=0.00011`

总体看，社会资本类变量能提供不少显著结果，但“哪个口径最好”要看你更想强调发明专利还是总专利。

### 2. 机制变量作为调节变量

这类里最值得看的口径是 `matched_commit_amt` 和 `gov_amt`。

#### `matched_commit_amt`

- `pat_utility_apply` + `debt_pressure` + `noctrl`
  - `matched_commit_amt`：`b=0.001334`，`p=0.00902`
  - `fund_est_scale_cum × matched_commit_amt`：`b=-8.3588e-10`，`p=0.00056`
- `pat_utility_apply` + `debt_pressure_l1` + `noctrl`
  - `matched_commit_amt`：`b=0.001582`，`p=0.00624`
  - `fund_est_scale_cum × matched_commit_amt`：`b=-9.7596e-10`，`p=0.00074`
- `pat_apply_total` + `debt_pressure_l1` + `noctrl`
  - `fund_est_scale_cum × debt_pressure_l1`：`b=-4.0202e-05`，`p=0.0295`
  - `fund_est_scale_cum × matched_commit_amt`：`b=-1.2736e-09`，`p=0.00233`

#### `gov_amt`

- `pat_utility_apply` + `debt_pressure` + `noctrl`
  - `gov_amt`：`b=0.001420`，`p=0.0270`
  - `fund_est_scale_cum × gov_amt`：`b=-9.1549e-10`，`p=0.00232`
- `pat_utility_apply` + `debt_pressure_l1` + `noctrl`
  - `gov_amt`：`b=0.001724`，`p=0.00813`
  - `fund_est_scale_cum × gov_amt`：`b=-1.0888e-09`，`p=0.00083`
- `pat_apply_total` + `debt_pressure_l1` + `noctrl`
  - `fund_est_scale_cum × debt_pressure_l1`：`b=-3.9923e-05`，`p=0.0310`
  - `fund_est_scale_cum × gov_amt`：`b=-1.5347e-09`，`p=0.00381`

这说明如果把社会资本相关指标理解成“会改变基金扶持创新边际效果的机制性调节变量”，`gov_amt` 和 `matched_commit_amt` 的表现比 `soccap_leverage` 更强。

## 三、融资约束机制

### 1. 机制变量作为中介传导变量

整体上，融资约束类最稳的是 `fcity_fc_mean`，其余口径次之。

#### `fcity_fc_mean`

- `pat_invent_apply` + `debt_pressure` + `ctrl`
  - `fund_est_scale_cum × debt_pressure`：`b=-1.2516e-05`，`p=0.00048`
  - `fcity_fc_mean`：`b=345.4442`，`p=0.5517`
- `pat_invent_apply` + `debt_pressure_l1` + `ctrl`
  - `fund_est_scale_cum × debt_pressure_l1`：`b=-1.4672e-05`，`p=0.00038`
  - `fcity_fc_mean`：`b=258.7599`，`p=0.6547`
- `pat_invent_apply` + `debt_pressure` + `noctrl`
  - `fund_est_scale_cum × debt_pressure`：`b=-1.2792e-05`，`p=2.17e-05`
  - `fcity_fc_mean`：`b=449.5384`，`p=0.1911`

这组结果说明：融资约束类变量更像是在结果方程中伴随主调节项稳定出现，而不是像早期投资那样自己也非常显著。

#### `fcity_sa_mean`

- `pat_utility_apply` + `debt_pressure` + `ctrl`
  - `fund_est_scale_cum × debt_pressure`：`b=-1.4501e-05`，`p=0.0866`
  - `fcity_sa_mean`：`b=-6526.8464`，`p=0.0344`
- `pat_apply_total` + `debt_pressure_l1` + `noctrl`
  - `fund_est_scale_cum × debt_pressure_l1`：`b=-3.4714e-05`，`p=0.0321`
  - `fcity_sa_mean`：`b=-5947.6725`，`p=0.0950`

### 2. 机制变量作为调节变量

如果按“机制性调节变量”写，融资约束类的结果明显更强，尤其是 `fcity_sa_mean` 和 `fcity_fc_mean`。

#### `fcity_sa_mean`

- `pat_utility_apply` + `debt_pressure` + `ctrl`
  - `fund_est_scale_cum × debt_pressure`：`b=-3.0263e-05`，`p=5.11e-06`
  - `fcity_sa_mean`：`b=-7532.7055`，`p=0.005998`
  - `fund_est_scale_cum × fcity_sa_mean`：`b=0.2300864`，`p=5.91e-06`
- `pat_utility_apply` + `debt_pressure_l1` + `noctrl`
  - `fund_est_scale_cum × debt_pressure_l1`：`b=-2.2449e-05`，`p=0.00486`
  - `fcity_sa_mean`：`b=-7228.5481`，`p=0.00973`
  - `fund_est_scale_cum × fcity_sa_mean`：`b=0.1355285`，`p=5.13e-06`
- `pat_apply_total` + `debt_pressure` + `ctrl`
  - `fund_est_scale_cum × debt_pressure`：`b=-6.1216e-05`，`p=0.00019`
  - `fcity_sa_mean`：`b=-7304.6816`，`p=0.0425`
  - `fund_est_scale_cum × fcity_sa_mean`：`b=0.3755416`，`p=0.00097`

#### `fcity_fc_mean`

- `pat_apply_total` + `debt_pressure_l1` + `noctrl`
  - `fund_est_scale_cum × debt_pressure_l1`：`b=-3.9614e-05`，`p=0.00473`
  - `fcity_fc_mean`：`b=-3179.2842`，`p=0.00368`
  - `fund_est_scale_cum × fcity_fc_mean`：`b=0.5928412`，`p=5.68e-06`
- `pat_apply_total` + `debt_pressure` + `noctrl`
  - `fund_est_scale_cum × debt_pressure`：`b=-3.2027e-05`，`p=0.0110`
  - `fcity_fc_mean`：`b=-2827.4948`，`p=0.00582`
  - `fund_est_scale_cum × fcity_fc_mean`：`b=0.4682679`，`p=9.22e-06`
- `pat_invent_apply` + `debt_pressure_l1` + `ctrl`
  - `fund_est_scale_cum × debt_pressure_l1`：`b=-1.6612e-05`，`p=0.00155`
  - `fcity_fc_mean`：`b=-1036.6357`，`p=0.0818`
  - `fund_est_scale_cum × fcity_fc_mean`：`b=0.2295489`，`p=9.08e-09`

如果你想把融资约束机制写得更有力，建议优先采用“机制变量作为调节变量”的解释框架。

## 四、整体判断

### 1. 最容易写进正文主结果的机制

- 早期投资：`early_inv_count`、`early_inv_amt`
- 融资约束：`fcity_sa_mean`、`fcity_fc_mean`

### 2. 更适合作为补充机制的变量

- 社会资本类中的 `gov_amt`、`matched_commit_amt`、`fund_commit_total`、`gp_amt`

### 3. 当前不建议优先作为主口径强调的变量

- `soccap_leverage`
- 一些“share”类变量，虽然 `early_inv_amt_share` 和 `early_inv_count_share` 有若干显著结果，但整体解释力仍不如金额或事件数口径稳定

## 五、一句话结论

从显著结果看，最强的两条机制线索是：

- **早期投资变量会明显影响债务压力下基金扶持创新的作用强弱**
- **融资约束变量在“机制变量作为调节变量”的模型里表现尤其强**

如果要压缩成论文主线，建议优先围绕：

- `early_inv_count / early_inv_amt`
- `fcity_fc_mean / fcity_sa_mean`

来组织机制部分。 
