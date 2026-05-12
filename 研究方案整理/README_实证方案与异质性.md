# 财政债务约束下政府产业引导基金扶持创新效果研究

## 1. 研究主线

本文核心问题是：**政府产业引导基金是否促进地级市创新产出？在财政债务约束下，这种促进作用是否会被削弱？**

当前论文主线可概括为：

`政府引导基金规模 -> 创新产出`

进一步扩展为：

`政府引导基金规模 × 财政债务压力 -> 创新产出`

并围绕以下机制展开：

- 早期投资（耐心资本）
- 社会资本撬动效率
- 企业融资约束

---

## 2. 当前数据与主面板

当前正式回归优先使用英文变量名面板：

- `地级市总面板_2015_2024_英文版.csv`

对应中文总面板：

- `地级市总面板_2015_2024版.csv`
- `地级市总面板_编制版.csv`

当前回归相关文件输出目录：

- `运行日志与do代码`
- `实证结果`

> 说明：后续如果再跑 Stata 回归，优先读取英文版面板，避免中文路径和中文变量名带来的编码问题。

---

## 3. 基准回归设定

### 3.1 基准因变量

优先使用以下创新产出口径：

- `pat_invent_apply`：发明申请量
- `pat_utility_apply`：实用新型申请量
- `pat_apply_total`：专利申请总量

对应对数形式：

- `ln_pat_invent_apply`
- `ln_pat_utility_apply`
- `ln_pat_apply_total`

### 3.2 基准解释变量

优先使用以下基金规模口径：

- `fund_est_count`：基金当年设立数量
- `fund_est_scale`：基金当年设立规模
- `fund_est_count_cum`：基金累计设立数量
- `fund_est_scale_cum`：基金累计设立规模

经验上，当前更有信号的口径是：

- `fund_est_count`
- `fund_est_scale_cum`

### 3.3 基准模型

基准模型采用地级市固定效应和年份固定效应：

```stata
xtreg y x i.year, fe vce(cluster city_id)
```

如果加入控制变量，则为：

```stata
xtreg y x controls i.year, fe vce(cluster city_id)
```

---

## 4. 调节效应与机制检验

### 4.1 债务压力调节效应

主调节变量：

- `debt_pressure`：债务压力
- `debt_pressure_l1`：债务压力滞后一期

主调节模型建议优先使用：

- `fund_est_scale_cum × debt_pressure`
- `fund_est_scale_cum × debt_pressure_l1`

当前结果最稳的方向是：

**债务压力越高，基金累计设立规模促进创新的作用越弱。**

### 4.2 机制变量

#### （1）早期投资 / 耐心资本

变量口径：

- `early_inv_amt`：早期投资金额
- `early_inv_count`：早期投资事件数
- `early_inv_amt_share`：早期投资金额占比
- `early_inv_count_share`：早期投资事件占比

经验上：

- `early_inv_amt` 更适合作为“调节变量承担债务调节效应的传导机制”来写
- `early_inv_count` 更稳，但更像结果端机制变量

#### （2）社会资本撬动效率

变量口径：

- `soccap_fund_count`
- `soccap_amt`
- `gov_amt`
- `gp_amt`
- `unknown_amt`
- `fund_commit_total`
- `matched_commit_amt`
- `soccap_share_total`
- `gov_share_total`
- `soccap_leverage`
- `matched_share_total`

其中最核心的是：

- `soccap_leverage`

解释为：

**1 单位政府资金大致撬动多少社会资本。**

#### （3）企业融资约束

地级市层面已整理的融资约束口径：

- `fcity_sa_mean`
- `fcity_fc_mean`
- `fcity_kz_mean`
- `fcity_ww_mean`

可作为机制变量，也可作为异质性变量。

---

## 5. “有中介的调节”与“中介的调节”

### 5.1 有中介的调节（moderated mediation）

判断逻辑：

```text
X × W -> M
M -> Y
```

即：调节变量 `W` 影响中介链条 `X -> M -> Y` 的间接效应。

### 5.2 中介的调节（mediated moderation）

判断逻辑：

```text
X × W -> M -> Y
```

即：交互项 `X × W` 先影响机制变量，再传导到结果变量。

### 5.3 当前论文实际采用的思路

当前更接近：

```text
fund_est_scale_cum × debt_pressure -> early_inv_amt / soccap_* / fc_* -> innovation
```

因此当前主线更偏向：

**“债务调节效应的中介传导”**

---

## 6. 后续异质性分析变量及处理方式

异质性分析不要只做简单分组，建议优先采用两种做法：

1. **分组回归**
2. **交互项回归**

### 6.1 市场化水平

数据来源：

- `地级市市场化水平（2000-2024年）.xlsx`

变量名：

- `marketization`

建议做法：

- 以城市层面市场化水平的**样本中位数**分组
- 或者使用**样本前期均值（如 2015-2017 平均值）**分组
- 也可直接与核心解释变量做交互项

建议解释：

- 市场化程度高的城市，政府引导基金与社会资本、产业资源的协同可能更强
- 市场化程度低的城市，引导基金的“补缺”作用可能更明显

### 6.2 金融发展水平

数据来源：

- `2.26地级市金融发展水平(2000-2024).xlsx`

变量名：

- `fin_dev`
- `fin_dev_1`
- `fin_dev_2`

建议做法：

- 先用 `fin_dev` 作为主口径
- 再用 `fin_dev_1`、`fin_dev_2` 做稳健性
- 分组时建议用**城市均值**或**前期均值**

### 6.3 政府财政透明度

数据来源：

- `市级政府财政透明度（2013-2024年） 的副本.csv`

变量名：

- `fiscal_transparency`

建议做法：

- 作为异质性变量时，按城市财政透明度中位数分高低组
- 也可以用滞后一期或前期均值避免当期反向因果

### 6.4 企业融资约束

变量口径：

- `fcity_sa_mean`
- `fcity_fc_mean`
- `fcity_kz_mean`
- `fcity_ww_mean`

建议做法：

- 以城市层面融资约束的**高低组**进行分组回归
- 也可以直接与基金变量做交互项

建议解释：

- 融资约束高的城市，政府引导基金的边际创新补偿效应可能更强
- 融资约束低的城市，市场化资本本身较充足，引导基金边际作用可能较弱

### 6.5 城市规模与经济体量

可用控制/异质性口径：

- `gdp`
- `population_resident`
- `secondary_industry`
- `fdi_actual`

建议做法：

- 用城市规模中位数分组
- 例如“大城市 vs 中小城市”

### 6.6 社会资本撬动效率

变量口径：

- `soccap_leverage`

可作为：

- 机制变量
- 异质性变量

建议做法：

- 按城市 `soccap_leverage` 的中位数分高低组
- 或以基准期均值分组，避免同时期内生性

---

## 7. 异质性分析的推荐写法

### 7.1 分组回归

推荐按以下规则：

- 先算城市的**基准期均值**（优先）
- 再按中位数分成高/低两组
- 在各组内分别估计基准模型或调节模型

### 7.2 交互项回归

推荐形式：

```stata
xtreg y c.fund_est_scale_cum##c.heterogeneity_variable i.year, fe vce(cluster city_id)
```

如果是双重异质性，可以继续加交互：

```stata
xtreg y c.fund_est_scale_cum##c.debt_pressure##c.heterogeneity_variable i.year, fe vce(cluster city_id)
```

### 7.3 变量优先级

当前异质性分析优先顺序建议：

1. 市场化水平 `marketization`
2. 金融发展水平 `fin_dev`
3. 政府财政透明度 `fiscal_transparency`
4. 企业融资约束 `fcity_sa_mean / fcity_fc_mean / fcity_kz_mean / fcity_ww_mean`
5. 城市规模 `gdp / population_resident`

---

## 8. 数据处理约定

- 主面板默认使用英文版回归面板：
  - `地级市总面板_2015_2024_英文版_纯净.csv`
- 中文总面板保留用于人工核对：
  - `地级市总面板_2015_2024版.csv`
  - `地级市总面板_编制版.csv`
- 回归结果保存：
  - `运行日志与do代码`
- 可读性强的结果说明保存：
  - `实证结果`

---

## 9. 后续补数据时的处理原则

如果后续补充新的专利受理数据或其他变量，原则如下：

1. 先统一城市名称与年份格式
2. 再并回总面板
3. 保留原始值、对数值和滞后一期
4. 优先在英文版回归面板中更新
5. 中文总面板仅作为可视化和核对版本
