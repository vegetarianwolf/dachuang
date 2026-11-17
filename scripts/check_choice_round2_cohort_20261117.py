"""Connect the fixed 159-firm round-two M1 sample to final Choice history.

This diagnostic preserves the original sample, outcomes and estimates. Earlier
observed financing and first government entry are separate event definitions.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREP = ROOT / "实证结果/choice_download_20261117/prepare"
ROUND2 = ROOT / "实证结果/fiscal_fund_design_round2_20261117"
OUT = ROOT / "实证结果/choice_download_20261117/round2_cohort_history"
SAMPLE = ROUND2 / "samples/M1.csv"
CHANGES = ROOT / "面板数据/firm_changes_round2_20261117.csv"
CHOICE = PREP / "choice_events_normalized.csv.gz"
FLAGS = PREP / "choice_round_flags.csv.gz"
SUMMARY = PREP / "prepare_summary.json"
OVERLAP = PREP / "company_fullname_overlap.csv"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(value):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value))


def rows(path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8-sig", newline="") as stream:
        yield from csv.DictReader(stream)


def write_csv(path, records):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    input_paths = [SAMPLE, CHANGES, CHOICE, FLAGS, SUMMARY, OVERLAP, ROUND2 / "model_results.csv"]
    input_hashes = {str(path.relative_to(ROOT)): sha(path) for path in input_paths}
    prepared = json.loads(SUMMARY.read_text())
    assert prepared["download_snapshot"] == "final_download_files"
    assert prepared["download_completeness"]["passed"]
    for path in [CHOICE, FLAGS, OVERLAP]:
        assert prepared["outputs_sha256"][path.name] == sha(path)

    sample = list(rows(SAMPLE))
    assert len(sample) == 159
    assert len({r["unit_id"] for r in sample}) == len({norm(r["unit_name"]) for r in sample}) == 159
    changes = {r["obs_id"]: r for r in rows(CHANGES)}
    for r in sample:
        original = changes[r["obs_id"]]
        assert original["use_M1"] == "1"
        assert all(original[k] == r[k] for k in ["unit_id", "unit_name", "year", "source_city"])
        assert original["earlier_other_fund_observed"] == "0"
        assert original["first_any_observed_fund_year"] == r["year"]
    assert {r["obs_id"] for r in sample} == {r["obs_id"] for r in changes.values() if r["use_M1"] == "1"}

    targets = {norm(r["unit_name"]) for r in sample}
    choice = defaultdict(list)
    event_fields = ["event_id", "firm_legal_name", "firm_name_normalized", "event_date", "event_year", "round_raw",
                    "investor_list_raw", "source_file", "source_excel_row", "government_status"]
    total_choice = 0
    for r in rows(CHOICE):
        total_choice += 1
        if r["firm_name_normalized"] in targets:
            assert norm(r["firm_legal_name"]) == r["firm_name_normalized"]
            choice[r["firm_name_normalized"]].append({key: r[key] for key in event_fields})
    assert total_choice == prepared["source_rows"] == 360624
    matched_ids = {r["event_id"] for events in choice.values() for r in events}
    flags = {r["event_id"]: r for r in rows(FLAGS) if r["event_id"] in matched_ids}
    assert set(flags) == matched_ids
    overlap = {r["firm_name_normalized"]: r for r in rows(OVERLAP) if r["firm_name_normalized"] in targets}

    cohort, evidence = [], []
    for r in sorted(sample, key=lambda x: int(x["unit_id"])):
        name, year = norm(r["unit_name"]), int(r["year"])
        events = sorted(choice.get(name, []), key=lambda x: (x["event_date"], x["event_id"]))
        explicit = [event for event in events if flags[event["event_id"]]["is_explicit_venture_round_label"] == "1"]
        prior = [event for event in events if int(event["event_year"]) < year]
        prior_explicit = [event for event in explicit if int(event["event_year"]) < year]
        prior_groups = Counter(flags[event["event_id"]]["round_group"] for event in prior)
        first = min(int(event["event_year"]) for event in events) if events else ""
        first_explicit = min(int(event["event_year"]) for event in explicit) if explicit else ""
        if events:
            reference = overlap[name]
            assert int(reference["choice_source_rows"]) == len(events)
            assert int(reference["choice_first_observed_year"]) == first
            assert (int(reference["choice_first_explicit_venture_round_year"]) if reference["choice_first_explicit_venture_round_year"] else "") == first_explicit
        cohort.append(dict(m1_obs_id=int(r["obs_id"]), m1_unit_id=int(r["unit_id"]), firm_name=r["unit_name"],
                           firm_name_normalized=name, round2_first_observed_government_year=year,
                           round2_source_city=r["source_city"], choice_fullname_matched=int(bool(events)),
                           choice_literal_fullname_matched=int(any(event["firm_legal_name"] == r["unit_name"] for event in events)),
                           choice_observed_rows=len(events), choice_first_observed_year=first,
                           choice_first_explicit_venture_round_year=first_explicit,
                           choice_prior_any_observed=int(bool(prior)) if events else "",
                           choice_prior_explicit_venture_round_observed=int(bool(prior_explicit)) if events else "",
                           choice_prior_any_rows=len(prior) if events else "",
                           choice_prior_explicit_venture_round_rows=len(prior_explicit) if events else "",
                           choice_prior_round_groups_json=json.dumps(dict(sorted(prior_groups.items())), ensure_ascii=False),
                           choice_prior_any_source_row_ids=json.dumps([e["event_id"] for e in prior], ensure_ascii=False),
                           choice_prior_explicit_source_row_ids=json.dumps([e["event_id"] for e in prior_explicit], ensure_ascii=False),
                           history_status="observed_choice_history" if events else "unmatched_history_unknown",
                           choice_government_status="unknown"))
        for event in events:
            evidence.append(dict(m1_obs_id=int(r["obs_id"]), m1_unit_id=int(r["unit_id"]),
                                 round2_first_observed_government_year=year,
                                 before_government_cohort_year=int(int(event["event_year"]) < year),
                                 round_group=flags[event["event_id"]]["round_group"],
                                 is_explicit_venture_round_label=int(flags[event["event_id"]]["is_explicit_venture_round_label"]),
                                 **event))

    matched = sum(r["choice_fullname_matched"] for r in cohort)
    earlier = sum(r["choice_prior_any_observed"] == 1 for r in cohort)
    earlier_explicit = sum(r["choice_prior_explicit_venture_round_observed"] == 1 for r in cohort)
    neither = sum(r["choice_fullname_matched"] and r["choice_prior_any_observed"] == 0 for r in cohort)
    assert earlier_explicit <= earlier <= matched
    assert neither + earlier == matched
    assert all(r["government_status"] == "unknown" for r in evidence)
    assert all(input_hashes[str(path.relative_to(ROOT))] == sha(path) for path in input_paths)

    csv_path = OUT / "cohort_history_check.csv"
    evidence_path = OUT / "cohort_matched_choice_event_rows.csv"
    write_csv(csv_path, cohort)
    write_csv(evidence_path, evidence)
    summary = dict(passed=True, sample="round-two M1 fixed 159 firms", total_firms=len(cohort),
                   choice_fullname_matched_firms=matched, choice_unmatched_firms=len(cohort)-matched,
                   choice_matching_rate=matched/len(cohort), choice_matched_event_rows=len(evidence),
                   prior_any_event_firms=earlier, prior_explicit_venture_round_firms=earlier_explicit,
                   prior_only_other_event_labels_firms=earlier-earlier_explicit,
                   matched_without_observed_prior_event_firms=neither,
                   prior_any_rate_in_full_cohort=earlier/len(cohort),
                   prior_explicit_rate_in_full_cohort=earlier_explicit/len(cohort),
                   prior_any_rate_in_matched_firms=earlier/matched,
                   prior_explicit_rate_in_matched_firms=earlier_explicit/matched,
                   prior_any_event_rows=sum(e["before_government_cohort_year"] for e in evidence),
                   prior_explicit_event_rows=sum(e["before_government_cohort_year"] * e["is_explicit_venture_round_label"] for e in evidence),
                   prior_round_group_counts=dict(Counter(e["round_group"] for e in evidence if e["before_government_cohort_year"])),
                   original_round2_files_unchanged=True, input_sha256=input_hashes,
                   output_sha256={path.name: sha(path) for path in [csv_path, evidence_path]}, script_sha256=sha(Path(__file__)),
                   rules=dict(company_match="NFKC and whitespace removal, then complete-string equality; no aliases or parent/subsidiary substitution",
                              prior_history="Choice event year strictly less than the original M1 government cohort year; same-year ordering not classified",
                              explicit_rounds="Seed, angel, Pre-A, A/A+, B/Pre-B/B+, C and later lettered financing rounds; use the finalized separate Choice flags",
                              unmatched="Prior-history indicators remain missing for unmatched firms; no record does not establish no financing",
                              treatment_time="M1 uses the earliest observed municipal-fund year in the existing 2015–2024 government-fund export; the M1 exclusion of earlier observed other-scope funds is retained",
                              financing_vs_government_entry="First general financing and first government investment are distinct events. Earlier financing alone does not invalidate a first-government-entry cohort. Earlier investors need event-date fund/LP ownership evidence.",
                              no_private_imputation="All Choice government statuses remain unknown; neither match absence nor earlier timing establishes private VC status"))
    (OUT / "cohort_history_check.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    report = f"""# 第二轮 M1 企业与 Choice 融资历史衔接

第二轮 M1 的159家企业中，**{matched}家可按公司全名精确连接Choice（{matched/159:.1%}）**，{159-matched}家未匹配。在原第二轮首次观察政府基金年份之前，{earlier}家已有Choice事件记录，占全样本{earlier/159:.1%}；其中{earlier_explicit}家已有明确种子、天使、Pre-A、A、B或C及以后轮次标签，占全样本{earlier_explicit/159:.1%}。

| 原 M1 企业的新增历史信息 | 企业数 |
|---|---:|
| 较早事件中包含明确创投轮次标签 | {earlier_explicit} |
| 仅观察到其他较早事件标签 | {earlier-earlier_explicit} |
| 已匹配，首次政府样本年份前无Choice记录 | {neither} |
| 未匹配，历史未知 | {159-matched} |
| 合计 | 159 |

这些新记录把一般融资历史与政府基金进入时间分开。若研究围绕企业首轮一般融资构造前后窗口，更早的明确融资轮次是重新核验起点的重要线索；若研究围绕首次政府基金进入构造窗口，先前市场化融资属于企业的融资经历，可以作为处理前特征和可比性依据。更早私人融资本身不构成剔除首次政府进入样本的理由。Choice中的先前投资方仍需按事件当时的基金、LP和控制关系核验；政府背景维持unknown，名称未匹配也维持未知。

本次判定使用“Choice年份严格早于原M1政府样本年份”，同年内先后次序留待精确事件日期核对。原M1年份对应既有2015—2024政府基金导出中首次观察的地市级基金年份，原样本已剔除该表中观察到更早其他级别政府基金介入的企业。Choice的全部事件口径同时包含上市、并购、股权转让及未明确阶段的股权投资，明确轮次口径在独立flags中固定；两种历史口径分别展示。

cohort_history_check.csv保留159家企业及来源行ID；cohort_matched_choice_event_rows.csv保留其{len(evidence)}条匹配Choice记录，供逐条核验。cohort_history_check.json记录输入哈希、完整分母和规则。最终prepare文件、M1样本与第二轮回归结果保持原样，本次只新增历史诊断。
"""
    (OUT / "衔接诊断说明.md").write_text(report, encoding="utf-8")
    print(json.dumps({key: summary[key] for key in ["total_firms", "choice_fullname_matched_firms", "choice_unmatched_firms", "prior_any_event_firms", "prior_explicit_venture_round_firms", "prior_only_other_event_labels_firms", "matched_without_observed_prior_event_firms", "choice_matched_event_rows", "prior_any_event_rows", "prior_explicit_event_rows"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
