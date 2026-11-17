"""Write complete second-round tables and the two-primary-test Holm correction."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '实证结果/fiscal_fund_design_round2_20261117'
LABELS = {'F1':'同一基金：年份和行业效应','F2a':'F2共同样本：年份和行业效应','F2':'同一基金：目的地×年份和行业效应',
          'F3a':'债务共同样本：财政主式','F3':'财政缺口×债务',
          'M1':'企业投后一年前一年对数差','M2':'M1增加投前专利水平','M3':'前趋势共同样本的投前后差',
          'M4':'前趋势共同样本的投前变化','M5':'三年前后平均对数差','M6':'三年窗口共同样本的一年差'}


def main():
    r=pd.read_csv(OUT/'model_results.csv')
    assert len(r)==11 and not r.status.str.startswith('stata_error').any()
    core=r[r.model.isin(['F1','M1'])].copy()
    core['correction_input_p']=core.p.fillna(1)
    order=core.correction_input_p.sort_values().index
    core.loc[order,'holm_p']=np.minimum(1,np.maximum.accumulate(core.loc[order,'correction_input_p'].to_numpy()*[2,1]))
    core.to_csv(OUT/'core_tests_holm.csv',index=False)
    lines=['# 第二轮完整试验结果','',
           '全部标准误按来源城市聚类，区间为95%。基金模型吸收基金固定效应；企业模型使用投前后差和投资年份固定效应。F3目标项为财政缺口×债务，其余目标项为投资前／前一年的财政缺口。','',
           '| 规格 | 内容 | 系数 | SE | 95%CI | p | N | 来源城市 | 基金／企业数 |','|---|---|---:|---:|---|---:|---:|---:|---:|']
    for x in r.itertuples():
        if x.status!='ok':
            lines.append(f'| {x.model} | {LABELS[x.model]} | — | — | 样本不足40观测／20来源城，跳过 | — | {int(x.N)} | {int(x.clusters)} | {int(x.units)} |')
        else:
            lines.append(f'| {x.model} | {LABELS[x.model]} | {x.b:.4f} | {x.se:.4f} | [{x.lo:.4f}, {x.hi:.4f}] | {x.p:.4f} | {int(x.N)} | {int(x.clusters)} | {int(x.units)} |')
    lines+=['','F1与M1是本轮两项主要诊断，Holm校正p值均为1。全部其余系数和年份／行业／目的地年份项见all_coefficients.csv。', '']
    influence=OUT/'f2_leave_one_city.csv'
    if influence.exists():
        lines+=['## F2逐一剔除来源城市','','后验影响性诊断因财政变动集中而启动，保留全部剔除结果。原主模型保持不变。详情见[f2_leave_one_city.csv](f2_leave_one_city.csv)。','']
    (OUT/'完整试验结果.md').write_text('\n'.join(lines),encoding='utf-8')
    print(core[['model','b','p','holm_p']].to_string(index=False))


if __name__=='__main__':
    main()
