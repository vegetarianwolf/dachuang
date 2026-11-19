"""Audit exact-name financing risk-set feasibility; no regressions or private-VC labels.

Reads existing Choice/Qingke preparations and streams 20 nonlisted-patent shards.
All outputs are LF text; absent patent rows remain missing.
"""
import csv
import gzip
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from collections import defaultdict,Counter
from statistics import median

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'实证结果/fiscal_fund_choice_round3_20261119'
OUT.mkdir(parents=True,exist_ok=True)
PREP=ROOT/'实证结果/choice_download_20261117/prepare'
PAT=ROOT/'原始数据打包_20260401/CNRDS专利数据包/非上市公司专利申请与获得'
MICRO_PATH = ROOT / '面板数据/micro_fiscal_round2_20261117.csv'
ASSOC_PATH = ROOT / '实证结果/fiscal_fund_design_round2_20261117/micro_firm_source_associations.csv'
PREP_INPUTS = [PREP / name for name in [
    'choice_events_normalized.csv.gz', 'choice_round_flags.csv.gz',
    'choice_investor_tokens.csv.gz', 'company_fullname_overlap.csv',
    'qingke_source_row_index.csv',
]]
for required in PREP_INPUTS + [MICRO_PATH, ASSOC_PATH]:
    if not required.is_file():
        raise FileNotFoundError(f'Required source file missing: {required}')
assert PAT.is_dir(), f'Nonlisted patent directory missing: {PAT}'
assert len(list(PAT.rglob('*.csv'))) == 20, 'Expected exactly 20 nonlisted patent CSV shards'

def read(p):
    opener = gzip.open if str(p).endswith('.gz') else open
    with opener(p, 'rt', encoding='utf-8-sig', newline='') as source:
        yield from csv.DictReader(source)
def norm(s):return re.sub(r'\s+','',unicodedata.normalize('NFKC',s))
def round_norm(s):
    s=norm(s).upper().replace('－','-').replace('—','-')
    s=re.sub(r'^PRE(?=[A-Z])','PRE-',s)
    return re.sub('轮$','',s)

def write_report(result):
    pre=result['preliminary'];rs=result['risksets'];main=rs['main_l1_round_exact'];link=result['event_linkage'];ps=result['patent_source_stats']
    core=link['core_financing'];all_labels=link['all_choice_labels']
    text=f'''# Choice 同期融资风险集可行性

现有数据可以形成**同期融资企业的候选风险集**。按融资年、省份、行业一级及精确轮次匹配，并要求双方 t−1、t+1 有明确发明申请值，能为 {main['treated_supported']} 家处理企业找到 {main['unique_control_firms']:,} 家不同候选企业，覆盖 {main['supported_treated_source_cities']} 个出资注册城市。它们是未在清科政府基金表观察到的候选企业，不据此标为私人 VC；企业同年出现 Choice 记录也尚不等于已经核实了清科那笔融资。

处理组沿用地市级基金、首个观察年 2016—2022、唯一初始注册城市、前一年财政 gap 可得且无更早清科基金年份的口径，共 {pre['eligible_2016_2022_unique_source_gap_no_earlier_qingke']} 家。{pre['main_apply_pair1_firms']} 家有 t±1 申请窗口，其中 {pre['main_same_year_choice_core']} 家有同年 Choice 核心融资记录；{main['treated_with_unique_stratum']} 家的这些记录只落入一个省份×行业一级×轮次层。获得专利窗口对照的 {main['treated_supported']} 家中，{main['treated_supported_unique_stratum']} 家属于单一层，其余采用多个候选层的并集，仅作覆盖诊断。

核心融资包含种子、天使、Pre-A、A、B、C 及以后轮次、Pre-IPO、股权投资和战略投资，排除上市、上市后融资、收购及转让。轮次只统一大小写、Unicode、空白、Pre- 写法及末尾“轮”字；不把股权投资推定为 A 轮，也不合并 A、A+、Pre-A。地区和行业沿用导出值，其历史有效期尚未核实。

| 预先限定的覆盖口径 | 获得对照的处理企业 | 不同对照候选企业 |
| --- | ---: | ---: |
'''
    labels={'main_l1_round_exact':'行业一级、申请 t±1','main_l2_round_exact':'行业二级、申请 t±1','main_l1_explicit_venture':'仅明确 VC 轮次标签、申请 t±1','main_l1_without_2020_april':'排除 2020 年 4 月记录的覆盖诊断','main_l1_grant_pair1':'行业一级、授权 t±1','main_l1_apply_continuous1':'申请 t−1 至 t+1 三年连续有值','main_l1_apply_pair3':'申请 t−3 与 t+3 两端有值','main_l1_apply_continuous3':'申请 t−3 至 t+3 七年连续有值'}
    for name,label in labels.items():
        r=rs[name];text+=f'| {label} | {r["treated_supported"]} | {r["unique_control_firms"]:,} |\n'
    text+=f'''
事件身份核验将 Choice 投资方 token 与**该企业初始地市级基金的实际法律全称**对应，而非与任意已知政府基金名字对应。结果如下，单位为处理企业数：

| 关联证据 | Choice 任意标签 | 核心融资标签 |
| --- | ---: | ---: |
| 同公司、同年、对应基金全称 | {all_labels['same_year_actual_fund_fullname_firms']} | {core['same_year_actual_fund_fullname_firms']} |
| 同公司、同日、对应基金全称 | {all_labels['same_day_actual_fund_fullname_firms']} | {core['same_day_actual_fund_fullname_firms']} |
| 同公司、同年、对应基金全称、同轮次 | {all_labels['same_year_fund_and_round_firms']} | {core['same_year_fund_and_round_firms']} |
| 同公司、同日、对应基金全称、同轮次 | {all_labels['same_day_fund_and_round_firms']} | {core['same_day_fund_and_round_firms']} |

因此，{main['treated_supported']} 家风险集不能整体表述为“清科同一笔基金融资的同轮对照”。基金品牌/简称尚未映射到法律实体，两库轮次也存在差异；缺少精确基金 token 不代表没有政府基金参与。需要保留上述两级定位：同期融资风险集可用于探索，具体同笔同轮事件的确认仍需逐项核验。

非上市专利申请与授权各 10 个分片，分别有 {ps['apply']['counts']['all_source_rows']:,}、{ps['grant']['counts']['all_source_rows']:,} 条有效年份记录，实际年份为 1985—2024。本次全部结果年固定截至 2023。Choice 2016—2022 核心融资涉及 {pre['choice_financing_core_firms']:,} 家公司，精确全名能在申请库找到 {ps['choice_core_firms_with_patents']['apply']:,} 家，在授权库找到 {ps['choice_core_firms_with_patents']['grant']:,} 家。

本次目标名称匹配到的申请 {ps['apply']['counts']['target_matched_rows_all_years']:,} 行、授权 {ps['grant']['counts']['target_matched_rows_all_years']:,} 行中，**总专利明确为零的行均为 0**，但发明指标明确为零分别有 {ps['apply']['counts']['target_explicit_zero_invention_rows']:,}、{ps['grant']['counts']['target_explicit_zero_invention_rows']:,} 行。这说明本次可用的发明零值来自仍有其他类型专利的企业年份；专利表缺行不能补零。要求事后 t+1 仍有专利行也会筛选结果可观测企业，因此覆盖样本不能代表全部获投企业。

对照主口径排除清科任一年出现的企业以及全部地市级处理样本。这是保守的身份覆盖诊断，也使用了事后历史；正式风险集应只按各队列年当时可得的身份信息确定，后续获投另行处理。已有 {main['treated_supported_prior_choice_history']} 家获支持的处理企业在 Choice 中有更早融资记录，首个清科观察年不能改称首次获投年。Choice 仅提供省级地区，尚不能为对照匹配与处理组一致的地市财政暴露。

本脚本不回归、不按显著性筛选，也不修改原始数据。复现命令为 `python3 scripts/audit_choice_risk_set_20261119.py`。数量及源文件哈希见 `risk_set_feasibility.json`；逐处理企业候选层和数量见 `risk_set_treated_details.json`；事件级基金核验线索见 `risk_set_event_linkage.json`。全部输出使用 LF，未复制全量专利源文件。
'''
    (OUT/'同期融资风险集可行性.md').write_text(text,encoding='utf-8',newline='\n')
flags={r['event_id']:r for r in read(PREP/'choice_round_flags.csv.gz')}
qfirst={r['firm_name_normalized']:int(r['qingke_first_observed_year']) for r in read(PREP/'company_fullname_overlap.csv') if r['qingke_first_observed_year']}
micro={r['firm_name']:r for r in read(MICRO_PATH) if r['scope']=='municipal'}
eligible={n:r for n,r in micro.items() if r['main_cohort_2016_2022']=='1' and r['n_initial_source_cities']=='1' and r['p_initial'] and r['earlier_other_fund_observed']=='0'}
treated_main={n:r for n,r in eligible.items() if r['apply_pair1']=='1'}
events = []
by_name = defaultdict(list)
strata = defaultdict(set)
first_choice = {}
anchors_all = defaultdict(list)
for r in read(PREP/'choice_events_normalized.csv.gz'):
    n=r['firm_name_normalized'];y=int(r['event_year']);fl=flags[r['event_id']]
    if n not in first_choice or y<first_choice[n]:first_choice[n]=y
    core=fl['is_explicit_venture_round_label']=='1' or fl['is_unspecified_equity_or_strategic_label']=='1' or fl['round_group']=='pre_ipo'
    if n in eligible and y==int(eligible[n]['first_year']):
        anchors_all[n].append({'event_id':r['event_id'],'year':y,'date':r['event_date'],
                              'key':(y,r['firm_region_raw'],r['industry_level1_raw'],round_norm(fl['round_normalized'])),
                              'core':core,'round':fl['round_normalized']})
    if not core or not 2016<=y<=2022:continue
    key=(y,r['firm_region_raw'],r['industry_level1_raw'],round_norm(fl['round_normalized']))
    if not all(key):continue
    rr={'firm':n,'year':y,'key':key,'date':r['event_date'],'explicit':fl['is_explicit_venture_round_label']=='1','level2':r['industry_level2_raw']}
    events.append(rr);by_name[n].append(rr);strata[key].add(n)
targets={r['firm'] for r in events}|set(eligible)
strata2=defaultdict(set)
for r in events:strata2[r['key']+(r['level2'],)].add(r['firm'])
pre={'municipal_firms':len(micro),'eligible_2016_2022_unique_source_gap_no_earlier_qingke':len(eligible),'main_apply_pair1_firms':len(treated_main),'choice_financing_core_events_2016_2022':len(events),'choice_financing_core_firms':len({r['firm'] for r in events}),
     'eligible_same_year_choice_core':sum(any(e['year']==int(r['first_year']) for e in by_name[n]) for n,r in eligible.items()),
     'main_same_year_choice_core':sum(any(e['year']==int(r['first_year']) for e in by_name[n]) for n,r in treated_main.items())}
print('PRE',json.dumps(pre,ensure_ascii=False),flush=True)

# Link the actual municipal first-year fund, rather than any government-related
# investor token in the company history, to the Choice source event.
initial_funds=defaultdict(set)
for r in read(ASSOC_PATH):
    if r['scope']=='municipal' and r['is_initial_year']=='1':initial_funds[r['firm_name']].add(norm(r['fund_name']))
qrows=defaultdict(list);qprecision=Counter()
for r in read(PREP/'qingke_source_row_index.csv'):
    qprecision[r['date_precision']]+=1
    n=r['firm_name_normalized']
    if n in eligible and r['year'] and int(r['year'])==int(eligible[n]['first_year']) and norm(r['fund_name_raw']) in initial_funds[n]:qrows[n].append(r)
anchor_ids={e['event_id'] for n in treated_main for e in anchors_all[n]}
tokens=defaultdict(set)
for r in read(PREP/'choice_investor_tokens.csv.gz'):
    if r['event_id'] in anchor_ids:tokens[r['event_id']].add(r['investor_token_normalized'])
link_rows=[]
for n in treated_main:
    for e in anchors_all[n]:
        yr=[q for q in qrows[n] if norm(q['fund_name_raw']) in tokens[e['event_id']]]
        day=[q for q in yr if q['date_precision']=='day' and q['event_date']==e['date']]
        yr_round=[q for q in yr if round_norm(q['round_raw'])==round_norm(e['round'])]
        day_round=[q for q in day if round_norm(q['round_raw'])==round_norm(e['round'])]
        link_rows.append({'firm_name':n,'choice_event_id':e['event_id'],'choice_event_date':e['date'],
                          'core_financing':e['core'],'choice_round':e['round'],'same_year_actual_fund_fullname':bool(yr),
                          'same_day_actual_fund_fullname':bool(day),
                          'same_year_fund_and_round':bool(yr_round),'same_day_fund_and_round':bool(day_round),
                          'matched_sameyear_qingke_rows':[q['source_row_id'] for q in yr],
                          'matched_qingke_date_precision':sorted({q['date_precision'] for q in yr}),
                          'sameyear_qingke_rounds':sorted({q['round_raw'] for q in yr})})
linkage={'treated_with_apply_pair1':len(treated_main),'qingke_all_date_precision':dict(qprecision)}
for scope in ['all_choice_labels','core_financing']:
    rs=[r for r in link_rows if scope=='all_choice_labels' or r['core_financing']]
    data={'choice_rows':len(rs),'treated_with_sameyear_choice':len({r['firm_name'] for r in rs})}
    for flag in ['same_year_actual_fund_fullname','same_day_actual_fund_fullname','same_year_fund_and_round','same_day_fund_and_round']:
        data[flag+'_firms']=len({r['firm_name'] for r in rs if r[flag]})
        data[flag+'_choice_rows']=sum(r[flag] for r in rs)
    linkage[scope]=data
print('LINKAGE',json.dumps(linkage,ensure_ascii=False),flush=True)

patents={};source_stats={};zeros={'0','0.0','0.00'};source_hashes={}
for outcome,prefix in [('apply','非上市公司专利申请情况'),('grant','非上市公司专利获得情况')]:
    pdata=defaultdict(dict);stats=Counter();years=Counter();matchedyrs=Counter()
    shard_paths = sorted(PAT.rglob(prefix + '_*.csv'))
    assert len(shard_paths) == 10, f'Expected 10 {outcome} patent shards, found {len(shard_paths)}'
    for p in shard_paths:
        source_hashes[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
        with p.open(encoding='utf-8-sig',newline='') as f:
            rows=csv.reader(f);header=next(rows)
            for row in rows:
                if len(row)<8 or not row[1].isdigit():stats['invalid_header_rows']+=1;continue
                y=int(row[1]);stats['all_source_rows']+=1;years[y]+=1
                vals=row[2:8]
                if all(v in zeros for v in vals):stats['all_source_total_explicit_zero_rows']+=1
                if vals[0] in zeros and vals[3] in zeros:stats['all_source_invention_explicit_zero_rows']+=1
                n=norm(row[0])
                if n not in targets:continue
                stats['target_matched_rows_all_years']+=1;matchedyrs[y]+=1
                vs=tuple(int(float(v)) if re.fullmatch(r'\d+(?:\.0+)?',v) else None for v in vals)
                total=sum(vs) if None not in vs else None
                inv=vs[0]+vs[3] if vs[0] is not None and vs[3] is not None else None
                if y in pdata[n]:
                    stats['duplicate_target_firm_year']+=1
                    if pdata[n][y]!=(total,inv):stats['conflicting_target_firm_year']+=1
                else:pdata[n][y]=(total,inv)
                stats['target_explicit_zero_total_rows']+=total==0
                stats['target_explicit_zero_invention_rows']+=inv==0
                stats['target_missing_total_numeric_rows']+=total is None
        print('READ',p.name,'matched firms',len(pdata),flush=True)
    patents[outcome]=pdata
    for metric in ['all_source_total_explicit_zero_rows','target_explicit_zero_total_rows','duplicate_target_firm_year','conflicting_target_firm_year']:
        stats.setdefault(metric,0)
    assert not stats['conflicting_target_firm_year'], 'Conflicting patent outcomes must be reviewed before feasibility is reported'
    source_stats[outcome]={'counts':dict(stats),'all_source_years':dict(sorted(years.items())),'matched_target_years':dict(sorted(matchedyrs.items())),'matched_target_firms':len(pdata)}

def has(n,y,outcome,width=1,continuous=False):
    requested=list(range(y-width,y+width+1)) if continuous else [y-width,y+width]
    if max(requested)>2023:return False
    return all(k in patents[outcome].get(n,{}) and patents[outcome][n][k][1] is not None for k in requested)
def assessment(pool,exclude_mode='ever_known_qingke',industry_level=1,explicit_only=False,drop_april2020=False,outcome='apply',width=1,continuous=False):
    out=Counter();allcontrols=set();cellcounts=[];details=[]
    for n,m in pool.items():
        y=int(m['first_year']);out['treated_input']+=1
        if not has(n,y,outcome,width,continuous):continue
        out['treated_with_patent_window']+=1
        anchors=[e for e in by_name[n] if e['year']==y and (not explicit_only or e['explicit']) and (not drop_april2020 or not e['date'].startswith('2020-04'))]
        if not anchors:continue
        out['treated_with_sameyear_choice_anchor']+=1
        keys={e['key'] if industry_level==1 else e['key']+(e['level2'],) for e in anchors}
        out['treated_with_unique_stratum']+=len(keys)==1
        possible=set()
        for key in keys:possible.update((strata if industry_level==1 else strata2)[key])
        possible.discard(n)
        possible={c for c in possible if c not in micro}
        if exclude_mode=='ever_known_qingke':possible={c for c in possible if c not in qfirst}
        else:possible={c for c in possible if qfirst.get(c,9999)>y+1}
        # The candidate event itself must meet optional date/explicit restrictions.
        if explicit_only or drop_april2020:
            possible={c for c in possible if any(e['year']==y and (e['key'] if industry_level==1 else e['key']+(e['level2'],)) in keys and (not explicit_only or e['explicit']) and (not drop_april2020 or not e['date'].startswith('2020-04')) for e in by_name[c])}
        out['treated_with_any_candidate_before_patents']+=bool(possible)
        controls={c for c in possible if has(c,y,outcome,width,continuous)}
        if controls:
            out['treated_supported']+=1;out['treated_supported_unique_stratum']+=len(keys)==1;allcontrols.update(controls);cellcounts.append(len(controls))
            out['treated_supported_prior_choice_history']+=first_choice[n]<y
        details.append({'treated_firm':n,'year':y,'n_strata':len(keys),'n_candidates_before_patents':len(possible),'n_controls_with_patents':len(controls),'source_city':m['source_city'],'strata':sorted(keys)})
    out['unique_control_firms']=len(allcontrols)
    supported=[r for r in details if r['n_controls_with_patents']]
    out['supported_treated_source_cities']=len({r['source_city'] for r in supported})
    out['supported_treated_years']=dict(Counter(r['year'] for r in supported))
    out['controls_per_supported_treated_min']=min(cellcounts) if cellcounts else 0
    out['controls_per_supported_treated_median']=median(cellcounts) if cellcounts else 0
    return dict(out),details

assess={};details={}
for name,kwargs in [
    ('main_l1_round_exact',{}),('main_l2_round_exact',{'industry_level':2}),
    ('main_l1_not_known_gvc_through_tplus1',{'exclude_mode':'prior_and_window'}),
    ('main_l1_explicit_venture',{'explicit_only':True}),('main_l1_without_2020_april',{'drop_april2020':True}),
    ('main_l1_grant_pair1',{'outcome':'grant'}),('main_l1_apply_continuous1',{'continuous':True}),
    ('main_l1_apply_pair3',{'width':3}),('main_l1_apply_continuous3',{'width':3,'continuous':True})]:
    assess[name],details[name]=assessment(eligible,**kwargs)
source_stats['choice_core_firms_with_patents']={o:sum(n in v for n in {r['firm'] for r in events}) for o,v in patents.items()}
allchoiceyearpairs={(r['firm'],r['year']) for r in events}
source_stats['choice_core_firm_years_2016_2022']=len(allchoiceyearpairs)
source_stats['choice_core_firm_years_with_pair1']={o:sum(has(n,y,o) for n,y in allchoiceyearpairs) for o in ['apply','grant']}
assert assess['main_l1_round_exact']['treated_with_patent_window']==len(treated_main)
for p in PREP_INPUTS + [MICRO_PATH, ASSOC_PATH]:
    source_hashes[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
result={'preliminary':pre,'patent_source_stats':source_stats,'risksets':assess,'event_linkage':linkage,'source_sha256':source_hashes,
        'rules':['Only exact full-name matching after NFKC and whitespace normalization.','Treated: municipal first observed 2016-2022, unique initial registration city, observed prior fiscal gap, no earlier observed Qingke government-fund year.','Same-year Choice core-financing anchors and exact province/industry level/normalized round; ambiguous multiple strata union reported separately from unique strata.','Core financing includes explicit seed/angel/pre-A/A/B/C+ round labels, unspecified equity, strategic investment and pre-IPO; excludes listings, listed financing, transfers and acquisitions.','Primary candidates exclude every municipal treated firm and every company ever overlapping Qingke; this is observed-government-history exclusion, not private-VC certification.','Patent row absence remains missing; pair1 needs explicit numeric invention values at t-1 and t+1; all outcome years are capped at 2023.','Alternative not-known-GVC-through-t+1 still excludes all 939 municipal sample companies and does not prove no government treatment.','Same-day event links require actual day-level Qingke dates; month-level dates cannot establish same-day correspondence.','Sameyear+fund checks match a token to the actual initial municipal fund legal name on a company-specific Qingke row.','Controls without firm-city data cannot yet be assigned common prefecture fiscal exposure.']}
for filename, payload in [
    ('risk_set_feasibility.json', result),
    ('risk_set_treated_details.json', details),
    ('risk_set_event_linkage.json', link_rows),
]:
    (OUT / filename).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n',
                                encoding='utf-8', newline='\n')
write_report(result)
print('RESULT',json.dumps(result,ensure_ascii=False),flush=True)
