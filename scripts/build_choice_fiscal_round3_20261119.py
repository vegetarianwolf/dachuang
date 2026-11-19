"""Join audited Choice financing histories to the round-two municipal cohorts."""

import csv
import json
import math
from collections import defaultdict
from pathlib import Path

from check_choice_round2_cohort_20261117 import CHANGES, CHOICE, FLAGS, SAMPLE, SUMMARY, norm, rows, sha

ROOT = Path(__file__).resolve().parents[1]
MICRO = ROOT / "面板数据/micro_fiscal_round2_20261117.csv"
DATA = ROOT / "面板数据/firm_choice_fiscal_round3_20261119.csv"
OUT = ROOT / "实证结果/fiscal_fund_choice_round3_20261119"


def fiscal_cohort(firm):
    return (
        2016 <= int(firm["year"]) <= 2022
        and firm["n_initial_source_cities"] == "1"
        and firm["earlier_other_fund_observed"] == "0"
        and all(firm[key] and math.isfinite(float(firm[key])) for key in ("p", "l_gdp", "l_secondary"))
    )


def financing_windows(events, year):
    prior = [event for event in events if event["explicit"] and int(event["event_year"]) < year]
    before = [event["event_id"] for event in prior if int(event["event_year"]) >= year - 2]
    after = [
        event["event_id"]
        for event in events
        if event["explicit"] and year < int(event["event_year"]) <= year + 2
    ]
    return {
        "entry_rows": sum(int(event["event_year"]) == year for event in events),
        "history": int(bool(prior)) if events else "",
        "pre2_round": int(bool(before)) if events else "",
        "follow2": int(bool(after)) if events else "",
        "prior_ids": json.dumps([event["event_id"] for event in prior], separators=(",", ":")),
        "follow_ids": json.dumps(after, separators=(",", ":")),
    }


def main():
    prepared = json.loads(SUMMARY.read_text(encoding="utf-8"))
    assert prepared["download_completeness"]["passed"]
    inputs = {str(path.relative_to(ROOT)): sha(path) for path in (CHANGES, CHOICE, FLAGS, MICRO, SAMPLE, SUMMARY)}
    for path in (CHOICE, FLAGS):
        assert prepared["outputs_sha256"][path.name] == inputs[str(path.relative_to(ROOT))]
    firms = [firm for firm in rows(CHANGES) if fiscal_cohort(firm)]
    firm_ids = {firm["unit_id"] for firm in firms}
    names = {norm(firm["unit_name"]) for firm in firms}
    assert len(firms) == len(firm_ids) == len(names)
    patent_sample = {firm["obs_id"]: firm for firm in rows(SAMPLE)}
    assert set(patent_sample) == {firm["obs_id"] for firm in firms if firm["use_M1"] == "1"}

    meta = {}
    for row in rows(MICRO):
        if row["scope"] == "municipal" and row["relative_year"] == "0" and row["firm_id"] in firm_ids:
            assert row["firm_id"] not in meta
            meta[row["firm_id"]] = row
    assert set(meta) == firm_ids

    events = defaultdict(list)
    event_lookup = {}
    for row in rows(CHOICE):
        name = row["firm_name_normalized"]
        if name in names:
            assert row["government_status"] == "unknown"
            event = {key: row[key] for key in ("event_id", "event_year", "event_date")}
            assert event["event_id"] not in event_lookup
            events[name].append(event)
            event_lookup[event["event_id"]] = event
    for flag in rows(FLAGS):
        if flag["event_id"] in event_lookup:
            event_lookup[flag["event_id"]]["explicit"] = flag["is_explicit_venture_round_label"] == "1"
    assert all("explicit" in event for event in event_lookup.values())

    joined = []
    for firm in firms:
        uid, year = firm["unit_id"], int(firm["year"])
        if firm["obs_id"] in patent_sample:
            old = patent_sample[firm["obs_id"]]
            assert all(firm[key] == old[key] for key in ("unit_name", "unit_id", "year", "source_id", "source_city"))
            assert all(
                math.isclose(float(firm[key]), float(old[key]), rel_tol=1e-12, abs_tol=1e-14)
                for key in ("p", "l_gdp", "l_secondary", "change1")
            )
        matched = sorted(events[norm(firm["unit_name"])], key=lambda event: (event["event_date"], event["event_id"]))
        no_april = [event for event in matched if not event["event_date"].startswith("2020-04-")]
        full, filtered = financing_windows(matched, year), financing_windows(no_april, year)
        first = min((int(event["event_year"]) for event in matched), default=None)
        debt = meta[uid]["initial_debt_ratio"]
        assert not debt or math.isfinite(float(debt))
        assert meta[uid]["first_year"] == firm["year"]
        joined.append({
            **{key: firm[key] for key in ("obs_id", "unit_id", "unit_name", "source_id", "source_city",
                                          "year", "p", "l_gdp", "l_secondary", "pre1", "change1")},
            "patent_m1": int(firm["obs_id"] in patent_sample),
            "debt": debt,
            "choice_match": int(bool(matched)),
            "choice_first_year": first,
            "choice_visible_by_entry": int(first is not None and first <= year),
            **full,
            **{f"{key}_noapr": value for key, value in filtered.items()},
        })

    patent = [row for row in joined if row["patent_m1"]]
    linked = [row for row in patent if row["choice_match"]]
    follow = [row for row in joined if row["entry_rows"]]
    follow_noapr = [row for row in follow if row["entry_rows_noapr"]]
    follow_debt = [row for row in follow if row["debt"]]
    assert len(patent) == 159 and len(linked) == 143 and sum(row["history"] for row in linked) == 37
    assert follow and follow_noapr and follow_debt
    with DATA.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(joined[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(joined)
    audit = {
        "input_sha256": inputs,
        "panel_sha256": sha(DATA),
        "cohort_firms": len(joined),
        "patent_m1_firms": len(patent),
        "patent_linked_firms": len(linked),
        "patent_linked_by_entry_firms": sum(row["choice_visible_by_entry"] for row in patent),
        "patent_prior_explicit_firms": sum(row["history"] for row in linked),
        "follow_firms": len(follow),
        "follow_source_cities": len({row["source_id"] for row in follow}),
        "follow_observed_explicit_firms": sum(row["follow2"] for row in follow),
        "follow_prior_explicit_firms": sum(row["pre2_round"] for row in follow),
        "follow_no_april_firms": len(follow_noapr),
        "follow_no_april_same_sample_full_outcome_ones": sum(row["follow2"] for row in follow_noapr),
        "follow_no_april_outcome_ones": sum(row["follow2_noapr"] for row in follow_noapr),
        "follow_debt_firms": len(follow_debt),
        "follow_debt_outcome_ones": sum(row["follow2"] for row in follow_debt),
    }
    (OUT / "data_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
