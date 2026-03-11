---
name: Empirical Research Plan
overview: 基于现有数据和已完成的初步回归结果，诊断当前问题（基准回归符号相反、中介效应不显著、机制变量覆盖率低），提出修正后的完整实证研究路径，覆盖变量重构、基准回归、机制检验（H2-H4三条渠道）、内生性处理、异质性分析与稳健性检验。
todos:
  - id: diag-fix-x
    content: "Phase 1: 修正核心解释变量 - 以 fiscal_self_l1 替代 fiscal_gap_l1，构建 PCA 合成指数"
    status: pending
  - id: build-m3-m4
    content: "Phase 1: 构建 H3/H4 机制变量 - avg_stage, late_ratio; 尝试区分市场化VC"
    status: pending
  - id: map-moderators
    content: "Phase 1: 完成调节变量 - 市场化指数省->市映射、财政透明度合并、城市等级/区域虚拟变量"
    status: pending
  - id: baseline-rerun
    content: "Phase 2: 重跑基准回归 - fiscal_self_l1 为核心X，逐步加控制，汇报标准表格"
    status: pending
  - id: iv-gmm
    content: "Phase 2: 内生性处理 - IV(省内留一均值) + 系统GMM + 安慰剂检验"
    status: pending
  - id: mechanism-h2
    content: "Phase 3: H2机制检验 - fiscal_self -> early_ratio (风险偏好渠道)"
    status: pending
  - id: mechanism-h3h4
    content: "Phase 3: H3+H4机制检验 - 挤出VC渠道 + 耐心资本/投资周期渠道"
    status: pending
  - id: heterogeneity
    content: "Phase 4: 异质性分析 - 按市场化/区域/城市等级/透明度分组回归 + 系数差异检验"
    status: pending
  - id: robustness
    content: "Phase 4: 稳健性检验 - 替换DV/IV/M、改变滞后期、排除特殊样本、缩尾、安慰剂"
    status: pending
  - id: tables-writing
    content: "Phase 5: 结果整理 - LaTeX表格、描述性统计、可视化、论文撰写"
    status: pending
isProject: false
---

# 财政约束、政府引导基金与地区创新：实证研究路径与方案

## 一、现有成果诊断与核心问题

### 1.1 已完成工作

- 城市-年份面板数据构建（347城市 x 11年，2014-2024）
- 被解释变量：ln(发明专利)、ln(专利总量)、发明专利占比（覆盖率100%）
- 核心解释变量：fiscal_gap_l1（84.6%）、debt_ratio_l1（51%）
- 控制变量：人均GDP、第二产业占比、科技支出占比等
- 机制变量：早期投资占比（v4/v5两版，覆盖率21-30%）
- 工具变量：省内留一均值（v5已构建）
- 基准回归和中介效应检验（Python + Stata双验证）

### 1.2 三个核心问题

**问题1：基准回归符号与理论预期相反**

- fiscal_gap_l1 对 ln(发明专利) 的系数显著为正（beta=1.08, p=0.03）
- 理论预期为负：财政压力应抑制创新
- 可能原因：fiscal_gap = (支出-收入)/GDP，支出更高的城市往往发展水平更高、创新投入更多，导致正向偏误

**问题2：中介效应完全不显著**

- 所有 X->M 路径 p>0.1，Sobel p=0.97
- 根本原因：机制变量覆盖率极低（早期投资占比仅覆盖21%的city-year观测）
- 低覆盖导致样本量从2575骤降至564，统计检验力严重不足

**问题3：假说体系需要对齐**

- [内容安排.md](内容安排.md) 提出 H1-H4 四条假说
- [大致思路.md](大致思路.md) 的 H1-H4 与之不完全一致
- 需统一假说框架并对应到可操作化的变量和模型

---

## 二、修正方案：变量重构

### 2.1 核心解释变量（X）修正

**问题根源**：fiscal_gap = (支出-收入)/GDP 的正系数可能是因为支出型城市同时也是创新强市。

**修正策略**：改用**财政自给率**（fiscal_self_sufficiency = 收入/支出）作为主要解释变量。


| 变量              | 定义                 | 预期符号              | 数据状态    |
| --------------- | ------------------ | ----------------- | ------- |
| fiscal_self_l1  | L1.财政自给率 = 收入/支出   | **正**（自给率越高，创新越好） | v5已构建   |
| fiscal_gap_l1   | L1.财政缺口率           | 负（稳健性）            | v4已有    |
| transfer_dep_l1 | L1.转移支付依赖度 = 1-自给率 | **负**             | v5已构建   |
| ln_debt_l1      | L1.ln(债务率)         | 负（稳健性）            | v4已有    |
| fiscal_stress   | PCA合成指数            | 负（稳健性）            | **需构建** |


**理由**：

- 自给率直接反映地方财政的"自主造血能力"，不受GDP分母干扰
- 自给率越低 → 越依赖转移支付 → 财政约束越强 → 预期负向影响创新
- 这个变量的理论解释更直觉、更不容易出现符号歧义

**构建方式**（v5面板中已有 `财政自给率` 和 `财政自给率_滞后一期`）：

```python
df["fiscal_self"] = df["财政收入"] / df["财政支出"]
df["fiscal_self_l1"] = df.groupby("城市")["fiscal_self"].shift(1)
```

### 2.2 机制变量（M）重构

对应 H2-H4 三条机制渠道，需要构建三组机制变量：

**M1 - 风险偏好渠道（H2）**：


| 变量                    | 定义         | 构建方式        | 数据源      |
| --------------------- | ---------- | ----------- | -------- |
| early_ratio_l1        | 早期投资次数占比   | 种子+初创次数/总次数 | 清科数据（已有） |
| early_amt_ratio_l1    | 早期投资金额占比   | 种子+初创金额/总金额 | 清科数据（已有） |
| early_ratio_filled_l1 | 填充版（无基金=0） | 已有          | v5面板     |


**M2 - 挤出效应渠道（H3）**：


| 变量          | 定义              | 构建方式        | 数据源     |
| ----------- | --------------- | ----------- | ------- |
| ln_vc_count | ln(市场化VC投资次数+1) | 需从清科PE数据中区分 | **需构建** |
| vc_amount   | 市场化VC投资总金额      | 同上          | **需构建** |


> **关键问题**：当前 PE_investment_events_cleaned.csv 仅含政府引导基金投资事件。如无市场化VC数据，H3可改为：测试财政压力是否降低了城市整体的PE/VC投资吸引力（使用现有数据中基金投资总量作为替代），或转为理论讨论。

**M3 - 耐心资本渠道（H4）**：


| 变量              | 定义           | 构建方式                    | 数据源           |
| --------------- | ------------ | ----------------------- | ------------- |
| avg_stage_l1    | 平均投资阶段       | 种子=1,初创=2,扩张=3,成熟=4加权均值 | 清科数据（**需构建**） |
| late_ratio_l1   | 后期投资占比       | 扩张+成熟次数/总次数             | 清科数据（**需构建**） |
| M_log_amount_l1 | ln(基金投资总额+1) | 投资规模代理                  | v5已有          |


**构建 avg_stage 的代码逻辑**：

```python
stage_map = {"种子期": 1, "初创期": 2, "扩张期": 3, "成熟期": 4}
events["stage_score"] = events["投资阶段"].map(stage_map)
city_year_avg = events.groupby(["城市", "年份"])["stage_score"].mean()
```

### 2.3 提高机制变量覆盖率

当前覆盖率低的根本原因：大量城市-年份无引导基金投资事件。

**策略**：

1. **广义投资虚拟变量**：M_has_fund_L1（是否有基金投资，0/1），覆盖率可达100%
2. **填充零值**：M_early_ratio_filled_L1（无基金投资的城市填0），已在v5中实现
3. **投资强度变量**：M_log_count_L1 = ln(基金投资次数+1)，覆盖率100%
4. **两阶段模型**：先Probit/Logit估计是否有基金投资，再OLS估计投资结构

### 2.4 控制变量调整

鉴于 finance_depth（38.1%）和 fdi_ratio（55.1%）覆盖率偏低，建议：

- **基准模型**（core_ctrl）：gdp_percap, industry_structure, tech_expend_ratio（覆盖均>77%）
- **扩展模型**（ext_ctrl）：加入 fdi_ratio, finance_depth
- 避免因低覆盖率控制变量导致样本量骤降

---

## 三、实证模型与检验步骤

### 3.1 基准回归（H1）

**H1：财政约束抑制了政府引导基金扶持地方创新绩效**

$$\lninvpatent_{c,t} = \alpha + \beta_1 fiscalself_{c,t-1} + \gamma \mathbf{X}*{c,t} + \mu_c + \lambda_t + \varepsilon*{c,t}$$

- 预期 $\beta_1 > 0$（自给率越高，创新越好）
- 双向固定效应 + 城市聚类标准误
- 替换 X 为 fiscal_gap_l1（预期 $\beta < 0$）、transfer_dep_l1（预期 $\beta < 0$）、ln_debt_l1

**Stata 代码**：

```stata
xtset city_id year
xtreg ln_inv_patent L.fiscal_self gdp_percap industry_structure ///
      tech_expend_ratio i.year, fe vce(cluster city_id)
```

**分步汇报结构**（表格）：

- (1) 仅 fiscal_self_l1，无控制
- (2) + 核心控制
- (3) + 完整控制
- (4)-(6) 替换为 fiscal_gap_l1 重复上述步骤

### 3.2 机制检验方法选择

传统 Baron-Kenny 三步法已受到广泛批评。建议采用以下方法组合：

**方法A：直接检验 X->M**（推荐主要使用）

对每条机制渠道单独回归，检验财政约束是否确实改变了机制变量：

$$M_{c,t} = \alpha + \delta fiscalself_{c,t-1} + \gamma \mathbf{X}*{c,t} + \mu_c + \lambda_t + \varepsilon*{c,t}$$

- H2：M = early_ratio_filled_l1，预期 $\delta > 0$（自给率高 → 更多早期投资）
- H3：M = ln_vc_count 或 M_has_fund_l1，预期 $\delta > 0$
- H4：M = avg_stage_l1，预期 $\delta < 0$（自给率高 → 平均投资阶段更早）

**方法B：交互项检验**

$$Y_{c,t} = \alpha + \beta_1 X_{c,t-1} + \beta_2 M_{c,t} + \beta_3 X_{c,t-1} \times M_{c,t} + \gamma \mathbf{Z}_{c,t} + FE + \varepsilon$$

如果 $\beta_3$ 显著，说明机制变量调节了X对Y的影响。

**方法C：因果中介分析（如数据支撑）**

- Bootstrap 置信区间
- 使用 Stata `medeff` 命令或 R `mediation` 包

### 3.3 机制检验具体实施

**H2：弱化风险偏好，扭曲"投早投小"**

```stata
* Step 1: X -> M (风险偏好)
xtreg early_ratio_filled L.fiscal_self controls i.year, fe vce(cluster city_id)
* Step 2: M -> Y
xtreg ln_inv_patent early_ratio_filled controls i.year, fe vce(cluster city_id)
* Step 3: X + M -> Y
xtreg ln_inv_patent L.fiscal_self early_ratio_filled controls i.year, fe vce(cluster city_id)
```

**H3：挤出市场化VC**

如有市场化VC数据：

```stata
xtreg ln_vc_count L.fiscal_self controls i.year, fe vce(cluster city_id)
```

如无市场化VC数据，替代方案：

- 检验财政压力对基金投资总规模的影响：`xtreg M_log_amount L.fiscal_self ...`
- 或将H3改为安慰剂检验思路：检验财政压力仅影响政府引导基金、不影响其他投资渠道

**H4：弱化耐心资本属性，缩短投资周期**

```stata
* 平均投资阶段（越大越后期）
xtreg avg_stage L.fiscal_self controls i.year, fe vce(cluster city_id)
* 后期投资占比
xtreg late_ratio L.fiscal_self controls i.year, fe vce(cluster city_id)
```

---

## 四、内生性处理

### 4.1 工具变量法（2SLS）

**工具变量**：同省其他城市的平均财政自给率（leave-one-out mean），v5面板中已有 `IV_财政自给率_省内均值_滞后一期`。

- **相关性**：同省城市面临相似的财政制度环境和宏观经济冲击
- **外生性**：其他城市的平均自给率不直接影响本城市的专利产出

```stata
ivreghdfe ln_inv_patent (L.fiscal_self = L.IV_fiscal_self_prov_mean) ///
    controls, absorb(city_id year) cluster(city_id)
* 检验
estat firststage   // 第一阶段F统计量 > 10
estat overid       // 过度识别检验（如有多个IV）
```

### 4.2 系统GMM

解决动态面板偏误：

```stata
xtabond2 ln_inv_patent L.ln_inv_patent L.fiscal_self controls i.year, ///
    gmm(L.ln_inv_patent L.fiscal_self, lag(2 4)) iv(controls i.year) ///
    twostep robust small
estat sargan
estat abond
```

### 4.3 其他内生性处理

- **安慰剂检验**：用未来一期 F.fiscal_self 回归当期 Y，预期不显著
- **排除反向因果**：所有 X 变量已滞后一期；可进一步滞后2-3期
- **PSM-FE**：按财政自给率高/低分组匹配后回归

---

## 五、异质性分析

### 5.1 分组维度


| 维度    | 分组方式            | 数据来源           | 状态      |
| ----- | --------------- | -------------- | ------- |
| 市场化程度 | 樊纲指数中位数分高低组     | 市场化指数（需省->市映射） | **需完成** |
| 地区    | 东部/中部/西部        | 按省份划分          | 可直接构建   |
| 城市等级  | 省会/副省级 vs 普通地级市 | 手工整理           | **需构建** |
| 财政透明度 | 清华透明度指数         | 已有CSV          | **需合并** |


### 5.2 分组回归与系数差异检验

```stata
* 按市场化程度分组
xtreg ln_inv_patent L.fiscal_self controls i.year if high_market==1, fe vce(cluster city_id)
est store high
xtreg ln_inv_patent L.fiscal_self controls i.year if high_market==0, fe vce(cluster city_id)
est store low

* 组间差异检验（SUR）
suest high low
test [high_mean]L.fiscal_self = [low_mean]L.fiscal_self
```

**预期**：

- 市场化程度低的城市，财政约束对创新的抑制更强
- 财政透明度低的城市，扭曲效应更明显
- 西部地区效应大于东部

---

## 六、稳健性检验


| 检验类型     | 具体操作                                             |
| -------- | ------------------------------------------------ |
| 替换被解释变量  | ln(专利总量)、发明专利占比、ln(人均专利)                         |
| 替换核心解释变量 | fiscal_gap_l1、transfer_dep_l1、ln_debt_l1、PCA合成指数 |
| 替换机制变量   | early_deal_ratio ↔ early_amt_ratio、avg_stage     |
| 改变滞后期    | X 滞后2期、3期                                        |
| 排除特殊样本   | 剔除省会/副省级城市；剔除资源型城市；剔除Top5%专利城市                   |
| 缩尾处理     | 1%/99% winsorization                             |
| 动态面板     | 加入 Y 的滞后项，系统GMM                                  |
| 安慰剂检验    | 使用未来期 X；随机打乱 X 赋值500次                            |


---

## 七、实施路线图

### Phase 1：数据修补与变量重构（3-5天）

1. 构建 avg_stage（平均投资阶段）和 late_ratio（后期投资占比）
2. 市场化指数省->市映射
3. 合并财政透明度数据
4. 构建城市等级、区域虚拟变量
5. PCA合成财政压力指数
6. (可选) 尝试从PE数据中区分市场化VC投资用于H3

### Phase 2：基准回归修正（2-3天）

1. 以 fiscal_self_l1 替换 fiscal_gap_l1 重跑基准回归
2. 逐步添加控制变量，检验稳健性
3. IV回归（省内留一均值）
4. 系统GMM

### Phase 3：机制检验（3-4天）

1. H2：fiscal_self -> early_ratio（X->M 回归）
2. H3：fiscal_self -> 基金投资规模/VC活跃度（X->M 回归）
3. H4：fiscal_self -> avg_stage / late_ratio（X->M 回归）
4. 完整中介效应表格（Bootstrap置信区间）

### Phase 4：异质性与稳健性（3-4天）

1. 分组回归（市场化、区域、城市等级、透明度）
2. 组间系数差异检验
3. 全套稳健性检验
4. 安慰剂检验

### Phase 5：结果整理与论文撰写（5-7天）

1. 制作规范的回归结果表格（LaTeX/esttab）
2. 描述性统计表
3. 可视化（地区分布图、时间趋势图、系数图）
4. 论文撰写

---

## 八、关键文件路径


| 用途        | 文件                                                                                                         |
| --------- | ---------------------------------------------------------------------------------------------------------- |
| 最新面板数据    | [cleaned_data/final_regression_panel_v5.csv](cleaned_data/final_regression_panel_v5.csv)                   |
| 基金投资汇总    | [cleaned_data/city_year_fund_investment_stats_v5.csv](cleaned_data/city_year_fund_investment_stats_v5.csv) |
| PE投资事件    | [cleaned_data/PE_investment_events_cleaned.csv](cleaned_data/PE_investment_events_cleaned.csv)             |
| 面板构建脚本    | [rebuild_panel_v5.py](rebuild_panel_v5.py)                                                                 |
| 市场化指数     | [1997-2024年市场化指数和各分项指数 的副本.csv](1997-2024年市场化指数和各分项指数 的副本.csv)                                             |
| 财政透明度     | [市级政府财政透明度（2013-2024年） 的副本.csv](市级政府财政透明度（2013-2024年） 的副本.csv)                                             |
| Stata回归脚本 | [regression_v2/run_mediation_v2.do](regression_v2/run_mediation_v2.do)                                     |


