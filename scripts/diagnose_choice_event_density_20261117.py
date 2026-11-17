"""Read-only date-concentration diagnostic, separate from export acceptance.

Reads formal registered batches spanning 2012-01-01 through 2024-12-31. Original rows,
missing values, dates and round labels are preserved; no records are removed.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict

import openpyxl

from audit_choice_download_20261117 import RAW, OUT, REQUIRED, iso_date, unavailable


def summarize(rows: list[dict]) -> dict:
    counts = Counter(r['date'] for r in rows)
    missing_amount = sum(unavailable(r.get('获投金额(元)')) for r in rows)
    missing_title = sum(unavailable(r.get('相关新闻标题')) for r in rows)
    missing_link = sum(unavailable(r.get('相关新闻链接')) for r in rows)
    missing_both_news = sum(unavailable(r.get('相关新闻标题')) and unavailable(r.get('相关新闻链接')) for r in rows)
    missing_both_amount_news = sum(unavailable(r.get('获投金额(元)')) and unavailable(r.get('相关新闻标题')) and unavailable(r.get('相关新闻链接')) for r in rows)
    real_estate_names = sum(bool(re.search('房地产|地产|置业', str(r.get('公司名称') or ''))) for r in rows)
    real_estate_industry = sum(any('房地产' in str(r.get(f'行业{level}级') or '') for level in ['一','二','三','四']) for r in rows)
    return {'rows':len(rows),'unique_company_names':len({r.get('公司名称') for r in rows}),
            'observed_days':len(counts), 'amount_missing':missing_amount,
            'news_title_missing':missing_title,'news_link_missing':missing_link,
            'news_both_missing':missing_both_news,'amount_and_news_missing':missing_both_amount_news,
            'investor_missing':sum(unavailable(r.get('投资方')) for r in rows),
            'real_estate_name_keywords':real_estate_names,'real_estate_industry':real_estate_industry,
            'rounds':dict(Counter(str(r.get('获投轮次') or '[missing]') for r in rows).most_common()),
            'industries_level1':dict(Counter(str(r.get('行业一级') or '[missing]') for r in rows).most_common()),
            'top_dates':counts.most_common(10)}


def main():
    manifest=json.loads((OUT/'ui_expected_counts.json').read_text())
    registered={n:v for n,v in manifest.items() if n.startswith('choice_events_') and isinstance(v,dict)
                and v.get('date_from','')>='2012-01-01' and v.get('date_to','9999')<='2024-12-31'}
    audit=json.loads((OUT/'download_audit.json').read_text())
    audited={r['file']:r for r in audit['files']}
    by_year=defaultdict(list)
    by_date=defaultdict(list)
    batch_counts={}
    for filename in sorted(registered):
        path=RAW/filename
        before=path.stat()
        wb=openpyxl.load_workbook(path,read_only=True,data_only=False)
        count=0
        for sheet in wb:
            header=None
            for row_index,cells in enumerate(sheet.iter_rows(values_only=True),1):
                texts=[str(v).strip() if v is not None else '' for v in cells]
                if header is None:
                    if REQUIRED<=set(texts): header=texts
                    continue
                if not any(texts) or REQUIRED<=set(texts) or any(s.startswith('数据来源') for s in texts): continue
                row={k:cells[i] for i,k in enumerate(header) if k}
                date_value=iso_date(row.get('获投时间'))
                if not date_value: raise ValueError(f'{filename}:{row_index} invalid date')
                row.update(date=date_value,file=filename,excel_row=row_index)
                by_year[date_value[:4]].append(row)
                by_date[date_value].append(row)
                count+=1
        wb.close()
        after=path.stat()
        if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
            raise ValueError(f'{filename} changed during read')
        batch_counts[filename]={'rows':count,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        if count!=audited[filename]['actual_event_rows'] or batch_counts[filename]['sha256']!=audited[filename]['sha256']:
            raise ValueError(f'{filename} count/hash differs from acceptance audit')
    years={}
    peaks={}
    flat=[]
    examples=[]
    for year,rows in sorted(by_year.items()):
        summary=summarize(rows)
        peak_date,peak_count=summary['top_dates'][0]
        peak=summarize(by_date[peak_date])
        summary.update(peak_date=peak_date,peak_rows=peak_count,peak_share=peak_count/len(rows),
                       period=year)
        years[year]=summary
        peaks[peak_date]=peak
        flat.append({'period':summary['period'],'rows':len(rows),'peak_date':peak_date,
                     'peak_rows':peak_count,'peak_share':summary['peak_share'],
                     **{f'all_{k}':summary[k] for k in ['amount_missing','news_both_missing','amount_and_news_missing','investor_missing','real_estate_name_keywords','real_estate_industry']},
                     **{f'peak_{k}':peak[k] for k in ['amount_missing','news_both_missing','amount_and_news_missing','investor_missing','real_estate_name_keywords','real_estate_industry']}})
        examples.extend({k:r.get(k) for k in ['file','excel_row','date','公司名称','获投轮次','获投金额(元)','币种','投资方','行业一级','行业二级','相关新闻标题','相关新闻链接']} for r in by_date[peak_date][:10])
    months_2020={}
    days_april={}
    focus_columns=['rows','unique_company_names','amount_missing','news_both_missing','investor_missing','real_estate_name_keywords','real_estate_industry']
    for month in sorted({r['date'][:7] for r in by_year['2020']}):
        months_2020[month]=summarize([r for r in by_year['2020'] if r['date'].startswith(month)])
    for day in sorted(d for d in by_date if d.startswith('2020-04')):
        days_april[day]=summarize(by_date[day])
    result={'scope':'Formal registered queries from 2012-01-01 through 2024-12-31; all years complete, probe exports excluded.',
            'rules':{'missing_news':'Both news title and news link unavailable. Blank/explicit missing markers only; no news external searches.',
                     'real_estate_name_keywords':'房地产|地产|置业 exact substrings in company name; descriptive only.',
                     'real_estate_industry':'房地产 substring in any of four source industry fields.',
                     'interpretation':'Describes reported financing dates; does not establish source insertion dates, genuine event identity or database coverage.'},
            'batch_counts':batch_counts,'by_year':years,'peak_date_profiles':peaks,
            'focus_2020_by_month':months_2020,'focus_2020_april_by_day':days_april,
            'all_counts_and_hashes_match_acceptance_audit':True}
    (OUT/'date_density_diagnostic.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for name,data in [('date_density_by_year.csv',flat),('date_density_peak_examples.csv',examples),
                      ('date_density_2020_months.csv',[{'month':m,**{k:v[k] for k in focus_columns}} for m,v in months_2020.items()]),
                      ('date_density_2020_april_days.csv',[{'date':d,**{k:v[k] for k in focus_columns}} for d,v in days_april.items()])]:
        with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(data[0]))
            writer.writeheader();writer.writerows(data)
    for row in flat: print(json.dumps(row,ensure_ascii=False))


if __name__=='__main__':
    main()
