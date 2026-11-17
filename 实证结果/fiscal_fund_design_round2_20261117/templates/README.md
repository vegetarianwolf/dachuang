# 补充数据接收模板

这些文件只有表头，不含示例值或模拟数据。首轮可直接交付数据库原始Excel、字段字典、筛选条件和查询总行数；随后将原列映射到模板。英文列名是本项目的标准字段，不是已经核实的供应商变量代码。总目标为2012—2024年，P0只取少量样本。

## 文件、行单位与连接键

| 文件 | 一行代表什么 | 关键连接或唯一键 | 首轮用途 |
|---|---|---|---|
| `access_probe.csv` | 一次平台／子表权限与导出测试 | `probe_id` | P0先填写；含权限、起止期、导出上限、筛选条件、查询数和实际行数 |
| `financing_events.csv` | 一次企业融资事件 | `source,event_id` | 同一融资轮次总额只存一次 |
| `event_investors.csv` | 一个事件中的一个投资方／具体基金 | `source,event_id,investor_id,fund_id` | 保留联合投资；金额是该投资方份额，未知留空 |
| `coverage_city_year.csv` | 某来源对某城市某年的一次完整取数口径 | 来源、模块、城市、年和筛选条件 | 记录数据库零条与真实零值的依据 |
| `fund_lp_history.csv` | 某基金与某LP在一段有效期内的出资关系 | `fund_id,lp_id,valid_from` | 对应实际出资财政；多层关系保留路径 |
| `fund_capital_payments.csv` | 一次计划缴款或实际付款记录 | `fund_id,lp_id,installment_id,payment_record_id` | 区分政府承诺与到账；原文没有分期配对时分行保留 |
| `fund_year_coverage.csv` | 某来源中的一只基金某年的活动与覆盖状态 | `source,fund_id,year` | 建立存在且被观察的基金风险集 |
| `fiscal_series_year.csv` | 某辖区某财政指标某年的一个来源版本 | `source,series_id,year,extracted_at` | 保存转移支付、收支、付息等长表；允许多个待核版本 |
| `bond_master.csv` | 一只债券的一版合同／发行人识别信息 | `source,bond_id,information_as_of` | 包含已到期债券和历史实际控制关系 |
| `bond_cashflows.csv` | 一只债券的一期计划／实际现金流及信息版本 | `source,bond_id,cashflow_id,schedule_version` | 区分冲击前安排与后续兑付变化 |
| `firm_identity_history.csv` | 法律实体一段时间内的名称／地址／集团身份 | 公司ID、名称及地点有效期 | 连接融资企业、工商和专利申请人；交叠关系保留原证据 |
| `patent_applicants.csv` | 一件专利的一个申请人 | `source,application_number,applicant_id` | 共同申请按明细保存，企业年计数前选择整计或分数计法 |
| `firm_year_outcomes.csv` | 一个法律实体或明确集团口径的一年结果 | `source,firm_id,year,entity_scope` | 同时保存专利覆盖、零值核验和可得财务数据 |

## 共通字段

- `source`：数据库及子库；`source_url`／`source_document`／`source_page`：可复查的链接、文档名和页码；`extracted_at`：提取时间。
- `*_id`：供应商稳定ID优先；跨库映射另建表，不能假定不同供应商同名ID相同。`*_uscc` 是统一社会信用代码，按文本保存。
- `*_date`：`YYYY-MM-DD`；仅有年份或月份时保持原始精度，并在日期类型或说明中注明，不虚构1月1日。日期有效期未知留空。
- `year` 是数据统计年度；`source_yearbook_year` 是年鉴册次年份，两者分别保存。
- 金额保留原币种和原单位；`amount_raw`／`value_raw` 保存原文，数值字段未知留空。融资金额区间放 `amount_lower,amount_upper`；不取区间中点充当已知金额。
- `government_status` 建议使用 `direct_government`、`government_lp_backed`、`verified_private`、`unknown`；对应证据时间放 `status_valid_at`。管理人国资、LP国资与主管财政角色分开核验。
- `fiscal_jurisdiction_code` 是出资或承担财政义务的辖区，`firm_city_code` 是企业所在辖区；保留财政层级。`geographic_scope` 建议保存来源原文，如“全市”“市本级”“市辖区”。
- `permission_status` 建议使用 `untested`、`allowed`、`partial`、`denied`；本文未实际验证学校账号，起始状态为未测试。
- `coverage_status`／`source_coverage_status` 建议使用 `verified_in_scope`、`partial`、`out_of_scope`、`unknown`；`query_complete` 表示完整执行指定查询，并不表示来源收录了全部实际活动。
- 布尔字段用 `1/0`，无法确认则留空。`observed_zero=1` 仅表示完整查询返回零条；`true_zero_verified=1` 还需覆盖及对象在观察期内的证据，填 `zero_verification_basis`。基金未成立、已清算、专利姓名匹配失败与未收录各自保存状态。
- `information_as_of` 表示当时能够获得的信息截止日。以历史合同构造债务暴露时，保留原条款版本；现时回溯导出日期另记 `extracted_at`。
- `record_type` 建议使用 `scheduled`、`actual`、`matched`；`cashflow_type` 同样区分计划与实际。若一笔计划分多次付款，分别记录实际款项，计划总额只累计一次。
- `entity_scope` 区分法律实体、母公司、合并集团。集团研发与集团专利不能默认为某一家被投子公司的结果。
- `patent_zero_verified`只针对`zero_verification_basis`明确列出的指标；注明核验的是发明申请、总申请还是授权。各数值列只有该指标被确认零时才填0；其他未知指标留空，发明零不推导为总专利零。

## 验收顺序

先查权限与覆盖，再核事件唯一键和查询数，随后查共同投资及身份映射，最后匹配财政与专利。筛选条件、原始文件和字典完整时，允许标准模板的未披露字段为空。具体取数顺序、字段用途及最低替代方案见同目录上一级的《补充数据清单与导出说明》。
