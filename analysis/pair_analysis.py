"""Pair-Level Analysis Module for The Sequential Matching Problem.
Constructs pair-level Cartesian datasets (199,000 within-pool combinations)
and computes reciprocal feasibility, failure causes, and soft similarity.
"""

from itertools import combinations
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np

from analysis.feature_engineering import evaluate_pair_compatibility


def run_pair_level_analysis(dfs: Dict[str, pd.DataFrame], output_dir: Path) -> Dict[str, Any]:
    """Analyze all within-pool pairs across the 10 benchmark datasets."""
    output_dir.mkdir(parents=True, exist_ok=True)
    members_df = dfs["members"]

    dataset_groups = members_df.groupby("dataset")
    all_pair_summaries = []
    status_counts_by_ds = []
    incompatibility_reasons = {}

    sample_pairs = []

    total_pairs_evaluated = 0
    feasible_count = 0
    incompatible_count = 0
    needs_clarification_count = 0

    print("Evaluating pair-level combinations across 10 pools...")

    for ds_name, group in dataset_groups:
        members_list = group.to_dict(orient="records")
        n_members = len(members_list)
        n_pairs = n_members * (n_members - 1) // 2

        ds_feasible = 0
        ds_incompatible = 0
        ds_clarification = 0

        for a, b in combinations(members_list, 2):
            res = evaluate_pair_compatibility(a, b)
            status = res["status"]

            if status == "feasible":
                ds_feasible += 1
                feasible_count += 1
            elif status == "infeasible":
                ds_incompatible += 1
                incompatible_count += 1
                for r in res["failed_reasons"]:
                    incompatibility_reasons[r] = incompatibility_reasons.get(r, 0) + 1
            else:  # needs_clarification
                ds_clarification += 1
                needs_clarification_count += 1

            # Keep first 50 sample pairs for inspectability
            if len(sample_pairs) < 50:
                sample_pairs.append({
                    "dataset": ds_name,
                    "member_a": a["member_id"],
                    "member_b": b["member_id"],
                    "status": status.upper(),
                    "soft_score": res["soft_score"],
                    "failed_reasons": "|".join(res["failed_reasons"]) if res["failed_reasons"] else "None",
                    "unknown_count": len(res["unknown_reasons"])
                })

        total_pairs_evaluated += n_pairs
        status_counts_by_ds.append({
            "dataset": ds_name,
            "total_pairs": n_pairs,
            "feasible_pairs": ds_feasible,
            "feasible_pct": round(ds_feasible / n_pairs * 100, 2),
            "needs_clarification_pairs": ds_clarification,
            "needs_clarification_pct": round(ds_clarification / n_pairs * 100, 2),
            "incompatible_pairs": ds_incompatible,
            "incompatible_pct": round(ds_incompatible / n_pairs * 100, 2)
        })

    # Overall Summary Table
    overall_summary = pd.DataFrame([
        {
            "Metric": "Total Pair Combinations Evaluated",
            "Value": f"{total_pairs_evaluated:,}",
            "Percentage": "100.0%",
            "Interpretation": "10 disjoint pools * (200 * 199 / 2) candidate edges"
        },
        {
            "Metric": "Fully Feasible Pairs (Confirmed)",
            "Value": f"{feasible_count:,}",
            "Percentage": f"{(feasible_count / total_pairs_evaluated * 100):.2f}%",
            "Interpretation": "All 11 hard constraints verified in both directions with zero unobserved fields"
        },
        {
            "Metric": "Uncertain Pairs (Needs Clarification)",
            "Value": f"{needs_clarification_count:,}",
            "Percentage": f"{(needs_clarification_count / total_pairs_evaluated * 100):.2f}%",
            "Interpretation": "Zero hard violations observed so far, but at least 1 hard field is unasked"
        },
        {
            "Metric": "Confirmed Incompatible Pairs",
            "Value": f"{incompatible_count:,}",
            "Percentage": f"{(incompatible_count / total_pairs_evaluated * 100):.2f}%",
            "Interpretation": "At least one reciprocal hard rule violated (gender, age, geography, etc.)"
        }
    ])
    overall_summary.to_csv(output_dir / "01_pair_compatibility_summary.csv", index=False)

    # Incompatibility Causes Table
    total_incompatible_events = sum(incompatibility_reasons.values())
    reasons_records = [
        {
            "failure_reason": k,
            "occurrence_count": v,
            "percentage_of_incompatible_pairs": round(v / incompatible_count * 100, 2) if incompatible_count else 0.0,
            "rule_type": "Reciprocal Filter"
        }
        for k, v in sorted(incompatibility_reasons.items(), key=lambda x: x[1], reverse=True)
    ]
    reasons_df = pd.DataFrame(reasons_records)
    reasons_df.to_csv(output_dir / "02_incompatibility_reasons_distribution.csv", index=False)

    # Dataset-wise Breakdown Table
    ds_df = pd.DataFrame(status_counts_by_ds)
    ds_df.to_csv(output_dir / "03_dataset_wise_pair_breakdown.csv", index=False)

    # Sample Pairs Table
    sample_df = pd.DataFrame(sample_pairs)
    sample_df.to_csv(output_dir / "04_sample_pair_features.csv", index=False)

    return {
        "summary": overall_summary,
        "reasons": reasons_df,
        "dataset_breakdown": ds_df,
        "sample_pairs": sample_df
    }


if __name__ == "__main__":
    from analysis.data_loader import load_all_datasets
    dfs = load_all_datasets()
    res = run_pair_level_analysis(dfs, Path("analysis_output/pair_results"))
    print("Pair analysis complete.")
    print(res["summary"])
