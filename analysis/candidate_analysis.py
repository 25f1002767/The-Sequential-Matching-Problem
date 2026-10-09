"""Candidate & N-Metric Analysis Module for The Sequential Matching Problem.
Computes candidate availability, degree distributions, zero-candidate root causes,
and scarcity indices across all participant profiles.
"""

from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np

from analysis.feature_engineering import evaluate_pair_compatibility


def run_candidate_analysis(dfs: Dict[str, pd.DataFrame], output_dir: Path) -> Dict[str, Any]:
    """Execute candidate degree and N analysis across the 10 pools."""
    output_dir.mkdir(parents=True, exist_ok=True)
    members_df = dfs["members"]

    member_degrees = defaultdict(int)
    member_potential_degrees = defaultdict(int)
    member_profiles = {m["member_id"]: m for m in members_df.to_dict(orient="records")}

    # Track degrees within each pool
    for ds_name, group in members_df.groupby("dataset"):
        m_list = group.to_dict(orient="records")
        for a, b in combinations(m_list, 2):
            res = evaluate_pair_compatibility(a, b)
            aid, bid = a["member_id"], b["member_id"]

            if res["status"] == "feasible":
                member_degrees[aid] += 1
                member_degrees[bid] += 1
                member_potential_degrees[aid] += 1
                member_potential_degrees[bid] += 1
            elif res["status"] == "needs_clarification":
                member_potential_degrees[aid] += 1
                member_potential_degrees[bid] += 1

    candidate_records = []
    for mid, m in member_profiles.items():
        deg = member_degrees[mid]
        pot_deg = member_potential_degrees[mid]
        candidate_records.append({
            "member_id": mid,
            "dataset": m["dataset"],
            "gender": m["gender"],
            "age": m["age"],
            "zone": m["zone"],
            "feasible_candidate_count": deg,
            "potential_candidate_count": pot_deg,
            "has_at_least_one_candidate": int(deg > 0),
            "has_potential_candidate": int(pot_deg > 0)
        })

    cand_df = pd.DataFrame(candidate_records)
    total_members = len(cand_df)
    n_with_cand = cand_df["has_at_least_one_candidate"].sum()
    n_zero_cand = total_members - n_with_cand
    n_with_pot = cand_df["has_potential_candidate"].sum()

    deg_series = cand_df["feasible_candidate_count"]

    # 1. N & Candidate Summary Table
    n_summary = pd.DataFrame([
        {
            "Metric": "Total Analyzed Members",
            "Value": f"{total_members:,}",
            "Meaning": "All synthetic members across 10 benchmark pools"
        },
        {
            "Metric": "Members with >= 1 Feasible Candidate (N)",
            "Value": f"{n_with_cand:,}",
            "Meaning": f"{round(n_with_cand / total_members * 100, 2)}% of the population has at least one verified candidate"
        },
        {
            "Metric": "Members with Zero Feasible Candidates",
            "Value": f"{n_zero_cand:,}",
            "Meaning": f"{round(n_zero_cand / total_members * 100, 2)}% have 0 confirmed candidates under strict current information"
        },
        {
            "Metric": "Members with >= 1 Potential Candidate (including Uncertain)",
            "Value": f"{n_with_pot:,}",
            "Meaning": f"{round(n_with_pot / total_members * 100, 2)}% could have candidates if unasked fields are clarified"
        },
        {
            "Metric": "Mean Candidates per Member",
            "Value": f"{deg_series.mean():.2f}",
            "Meaning": "Average candidate degree across all members"
        },
        {
            "Metric": "Median Candidates per Member",
            "Value": f"{deg_series.median():.1f}",
            "Meaning": "Median candidate degree"
        },
        {
            "Metric": "Max Candidates for a Single Member",
            "Value": f"{deg_series.max():d}",
            "Meaning": "Highest degree observed"
        },
        {
            "Metric": "Min Candidates for a Single Member",
            "Value": f"{deg_series.min():d}",
            "Meaning": "Lowest degree observed"
        }
    ])
    n_summary.to_csv(output_dir / "01_N_and_candidate_summary.csv", index=False)

    # 2. Candidate Count Distribution Buckets
    bins = [-1, 0, 5, 10, 20, 50, 100, 200]
    labels = ["0 Candidates", "1 - 5 Candidates", "6 - 10 Candidates", "11 - 20 Candidates", "21 - 50 Candidates", "51 - 100 Candidates", "101+ Candidates"]
    cand_df["degree_bracket"] = pd.cut(cand_df["feasible_candidate_count"], bins=bins, labels=labels)
    bracket_df = cand_df["degree_bracket"].value_counts().sort_index().reset_index()
    bracket_df.columns = ["candidate_bracket", "member_count"]
    bracket_df["percentage"] = (bracket_df["member_count"] / total_members * 100).round(2)
    bracket_df.to_csv(output_dir / "02_candidate_bracket_distribution.csv", index=False)

    # 3. Root Cause Analysis for Members with Zero Candidates
    zero_df = cand_df[cand_df["feasible_candidate_count"] == 0]
    reasons = []

    for _, r in zero_df.iterrows():
        mid = r["member_id"]
        pot = r["potential_candidate_count"]
        if pot > 0:
            reasons.append({
                "member_id": mid,
                "primary_root_cause": "Blocked by Unobserved Hard Information (Clarification Bottleneck)",
                "explanation": f"Has {pot} potential candidates who satisfy known rules, but unasked fields prevent confirmation."
            })
        else:
            reasons.append({
                "member_id": mid,
                "primary_root_cause": "Demographic / Geographic Supply Scarcity",
                "explanation": "Strict gender preferences or isolated geographic zone (e.g. Zone D) in this pool yields zero matches."
            })

    zero_reasons_df = pd.DataFrame(reasons)
    cause_summary = zero_reasons_df["primary_root_cause"].value_counts().reset_index()
    cause_summary.columns = ["root_cause", "affected_members_count"]
    cause_summary["percentage_of_zero_candidate_members"] = (cause_summary["affected_members_count"] / len(zero_df) * 100).round(2)
    cause_summary.to_csv(output_dir / "03_zero_candidate_root_cause_analysis.csv", index=False)

    # 4. Scarcity & Competition Analysis (Degrees 1 to 3)
    scarce_members = cand_df[(cand_df["feasible_candidate_count"] >= 1) & (cand_df["feasible_candidate_count"] <= 3)]
    scarcity_summary = pd.DataFrame([
        {
            "Metric": "Critically Scarce Members (1-3 candidates)",
            "Count": len(scarce_members),
            "Percentage": round(len(scarce_members) / total_members * 100, 2),
            "Algorithmic Risk": "Greedy algorithms easily strand these members by allocating their sole viable match to a high-degree partner."
        },
        {
            "Metric": "High-Degree Members (20+ candidates)",
            "Count": len(cand_df[cand_df["feasible_candidate_count"] >= 20]),
            "Percentage": round(len(cand_df[cand_df["feasible_candidate_count"] >= 20]) / total_members * 100, 2),
            "Algorithmic Risk": "Create severe competition and congestion; require rate limiting."
        }
    ])
    scarcity_summary.to_csv(output_dir / "04_candidate_scarcity_analysis.csv", index=False)

    # Detailed table export
    cand_df.to_csv(output_dir / "05_member_candidate_degrees.csv", index=False)

    return {
        "n_summary": n_summary,
        "brackets": bracket_df,
        "zero_causes": cause_summary,
        "scarcity": scarcity_summary
    }


if __name__ == "__main__":
    from analysis.data_loader import load_all_datasets
    dfs = load_all_datasets()
    res = run_candidate_analysis(dfs, Path("analysis_output/candidate_results"))
    print("Candidate & N analysis complete.")
    print(res["n_summary"])
