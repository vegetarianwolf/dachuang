"""Export multiplicity correction, complete tables, and source-backed figures."""
from pathlib import Path
import os
os.environ.setdefault('MPLCONFIGDIR', '/tmp/fiscal-trial-matplotlib')
os.environ.setdefault('XDG_CACHE_HOME', '/tmp/fiscal-trial-cache')
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '实证结果/fiscal_fund_trial_20261117'
LABELS = {
    'I1': '申请t+1，无控制／共同样本', 'I2': '申请t+1，主规格',
    'I3': '申请t+1，两预测期共同样本', 'I4': '申请t+2，两预测期共同样本',
    'I5': '申请t+1，债务共同样本', 'I6': '申请t+1，完整三阶交互',
    'I7a': '申请t+1，科技支出共同样本主式', 'I7': '申请t+1，加入科技支出',
    'I8': '授权t+1', 'I9': '早期比例与申请t+1', 'I10': '申请t+1，纳入2024结果年',
    'B1': '投资记录数对数', 'B2': '早期比例', 'B3': '早期比例，阶段笔数加权',
    'B4': '早期比例，加入行业构成', 'B5': '早期比例，财政×债务',
    'B6': '完整披露金额对数', 'B7': '阶段披露比例',
}


def main():
    r = pd.read_csv(OUT / 'model_results.csv')
    assert len(r) == 36
    assert not r.status.str.startswith('stata_error').any()
    core = r[(r.scope == 'municipal') & r.model.isin(['I2', 'B1', 'B2'])].copy()
    order = core.p.sort_values().index
    adjusted = np.maximum.accumulate(core.loc[order, 'p'].to_numpy() * np.arange(3, 0, -1))
    core.loc[order, 'holm_p'] = np.minimum(adjusted, 1)
    core.to_csv(OUT / 'core_tests_holm.csv', index=False)
    table = ['# 完整规格结果', '', '所有置信区间为95%，标准误按城市聚类。I1–I8、I10报告基金×缺口交互项，I6报告基金×缺口×债务；I9报告早期比例系数，B5报告缺口×债务，其余B规格报告前期财政缺口系数。', '']
    for scope, label in [('municipal', '明确地市级＋注册城市'), ('broad', '全部级别＋注册城市')]:
        table += [f'## {label}', '', '| 规格 | 内容 | 系数 | 聚类SE | 95%CI | p | N／城市 | 投资年份 |', '|---|---|---:|---:|---|---:|---:|---|']
        for x in r[r.scope == scope].itertuples():
            if x.status != 'ok':
                table += [f'| {x.model} | {LABELS[x.model]} | — | — | 样本未达40观测、20城市门槛 | — | {int(x.N)}／{int(x.clusters)} | — |']
            else:
                table += [f'| {x.model} | {LABELS[x.model]} | {x.b:.4f} | {x.se:.4f} | [{x.lo:.4f}, {x.hi:.4f}] | {x.p:.4f} | {int(x.N)}／{int(x.clusters)} | {int(x.year_min)}–{int(x.year_max)} |']
        table += ['']
    table += ['B3用areg吸收城市固定效应，允许权重随年份变化；其有限样本标准误校正计入吸收参数。其他规格使用xtreg。单期城市在各规格执行前移除；详细流失见sample_attrition.csv。', '']
    (OUT / '完整规格结果.md').write_text('\n'.join(table), encoding='utf-8')
    font = Path('/System/Library/Fonts/STHeiti Light.ttc')
    if font.exists():
        font_manager.fontManager.addfont(str(font))
        plt.rcParams['font.family'] = font_manager.FontProperties(fname=str(font)).get_name()
    plt.rcParams.update({'axes.unicode_minus': False, 'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False, 'svg.hashsalt': 'fiscal-fund-trial-20261117'})
    margins = pd.read_csv(OUT / 'marginal_effects.csv')
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.7), sharey=True)
    for ax, scope, label, color in zip(axes, ['municipal', 'broad'], ['地市级基金', '广义注册地'], ['#205b77', '#a0583c']):
        m = margins[(margins.scope == scope) & (margins.model == 'I2')]
        s = pd.read_csv(OUT / f'samples/{scope}_I2.csv')
        title = f'{label}：{s.city.nunique()}城、{len(s)}城年'
        ax.axhline(0, color='#666666', lw=1, ls='--')
        ax.errorbar(m.p_value, m.estimate, yerr=[m.estimate-m.lo, m.hi-m.estimate], fmt='o-', capsize=4, color=color, lw=1.5)
        ax.plot(s.p, np.full(len(s), .025), '|', color=color, alpha=.22, transform=ax.get_xaxis_transform())
        ax.set(title=title, xlabel='上年财政缺口率 (E−R)/E', ylim=(-.26, .21))
        ax.grid(axis='y', alpha=.15)
    axes[0].set_ylabel('基金活动与次年发明申请的边际关系')
    fig.suptitle('主模型的基金边际关系及95%置信区间', fontsize=16, y=.98)
    fig.text(.5, .02, '点位为各自样本的P5、P25、P50、P75、P95；底部短线显示实际财政缺口分布。\nG = ln(1+投资记录数)，Y = ln(1+发明申请量)。城市与年份固定效应，城市聚类标准误。', ha='center', fontsize=9)
    fig.tight_layout(rect=(0, .09, 1, .93))
    fig.savefig(OUT / 'marginal_effects.png', dpi=220, bbox_inches='tight')
    svg = OUT / 'marginal_effects.svg'
    fig.savefig(svg, bbox_inches='tight', metadata={'Date': None})
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines()) + '\n', encoding='utf-8')
    plt.close(fig)
    print(core[['model', 'b', 'p', 'holm_p', 'N', 'clusters']].to_string(index=False))


if __name__ == '__main__':
    main()
