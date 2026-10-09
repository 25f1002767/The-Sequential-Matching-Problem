"""Feature Engineering & Feature Dictionary Module for The Sequential Matching Problem.
Defines official feature transformations, metadata dictionary, and pair-level
reciprocal eligibility evaluators conforming strictly to kit.py contract.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np

from analysis.data_loader import HARD_FIELDS, SOFT_FIELDS


def get_feature_dictionary() -> pd.DataFrame:
    """Build the official comprehensive feature dictionary."""
    records = [
        # Hard constraints
        {
            "Raw Field": "who_to_meet, gender",
            "Engineered Feature": "reciprocal_gender_compat",
            "Feature Type": "Binary / Categorical",
            "Constraint Class": "HARD CONSTRAINT",
            "Handling of Unknown": "If unasked, returns UNKNOWN (needs_clarification); blocks matching until clarified. If declined, remains permanently blocked.",
            "Mathematical Definition": "a.gender in b.who_to_meet AND b.gender in a.who_to_meet",
            "Used in Policy": "Yes (Mandatory filter)",
            "Used in Evaluator": "Yes (Raises hard error if violated)",
            "Strategic Purpose": "Ensures reciprocal demographic orientation alignment."
        },
        {
            "Raw Field": "age_min, age_max, age",
            "Engineered Feature": "reciprocal_age_compat",
            "Feature Type": "Binary / Continuous Interval",
            "Constraint Class": "HARD CONSTRAINT",
            "Handling of Unknown": "Treated as UNKNOWN if unasked. Never imputed.",
            "Mathematical Definition": "b.age_min <= a.age <= b.age_max AND a.age_min <= b.age <= a.age_max",
            "Used in Policy": "Yes (Mandatory filter)",
            "Used in Evaluator": "Yes (Raises hard error if violated)",
            "Strategic Purpose": "Enforces mutual age preference bounds."
        },
        {
            "Raw Field": "acceptable_zones, zone",
            "Engineered Feature": "reciprocal_geography_compat",
            "Feature Type": "Set Membership",
            "Constraint Class": "HARD CONSTRAINT",
            "Handling of Unknown": "Treated as UNKNOWN if unasked. Blocks edge feasibility.",
            "Mathematical Definition": "b.zone in a.acceptable_zones AND a.zone in b.acceptable_zones",
            "Used in Policy": "Yes (Mandatory filter)",
            "Used in Evaluator": "Yes (Raises hard error if violated)",
            "Strategic Purpose": "Guarantees practical geographical feasibility for offline dates."
        },
        {
            "Raw Field": "smoking, partner_smoking",
            "Engineered Feature": "reciprocal_smoking_compat",
            "Feature Type": "Categorical Constraint",
            "Constraint Class": "HARD CONSTRAINT",
            "Handling of Unknown": "Treated as UNKNOWN. If either partner is unasked, edge is marked NEEDS_CLARIFICATION.",
            "Mathematical Definition": "NOT (a.partner_smoking=='no_smoking' and b.smoking in ['yes','occasionally']) AND reciprocal",
            "Used in Policy": "Yes (Mandatory filter)",
            "Used in Evaluator": "Yes (Raises hard error if violated)",
            "Strategic Purpose": "Prevents severe lifestyle incompatibility."
        },
        {
            "Raw Field": "has_children, partner_children",
            "Engineered Feature": "reciprocal_children_compat",
            "Feature Type": "Categorical / Boolean Constraint",
            "Constraint Class": "HARD CONSTRAINT",
            "Handling of Unknown": "Treated as UNKNOWN. Blocks edge.",
            "Mathematical Definition": "NOT (a.partner_children=='no_children' and b.has_children==True) AND reciprocal",
            "Used in Policy": "Yes (Mandatory filter)",
            "Used in Evaluator": "Yes (Raises hard error if violated)",
            "Strategic Purpose": "Protects parental boundaries and family acceptance preferences."
        },
        {
            "Raw Field": "wants_children",
            "Engineered Feature": "wants_children_alignment",
            "Feature Type": "Categorical Compatibility",
            "Constraint Class": "HARD CONSTRAINT",
            "Handling of Unknown": "Treated as UNKNOWN if either is None. Mutually conflicting only if set is {'yes', 'no'}.",
            "Mathematical Definition": "NOT ({a.wants_children, b.wants_children} == {'yes', 'no'})",
            "Used in Policy": "Yes (Mandatory filter)",
            "Used in Evaluator": "Yes (Raises hard error if violated)",
            "Strategic Purpose": "Ensures future family planning non-contradiction."
        },
        {
            "Raw Field": "relationship_structure",
            "Engineered Feature": "structure_compat",
            "Feature Type": "Categorical Equality",
            "Constraint Class": "HARD CONSTRAINT",
            "Handling of Unknown": "Treated as UNKNOWN if unasked.",
            "Mathematical Definition": "a.relationship_structure == b.relationship_structure",
            "Used in Policy": "Yes (Mandatory filter)",
            "Used in Evaluator": "Yes (Raises hard error if violated)",
            "Strategic Purpose": "Aligns monogamous vs non-monogamous commitments."
        },
        {
            "Raw Field": "schedule",
            "Engineered Feature": "schedule_overlap_compat",
            "Feature Type": "Set Intersection",
            "Constraint Class": "HARD CONSTRAINT",
            "Handling of Unknown": "Treated as UNKNOWN if unasked.",
            "Mathematical Definition": "len(set(a.schedule).intersection(set(b.schedule))) > 0",
            "Used in Policy": "Yes (Mandatory filter)",
            "Used in Evaluator": "Yes (Raises hard error if violated)",
            "Strategic Purpose": "Verifies that both members have at least one shared availability window."
        },
        # Soft preferences
        {
            "Raw Field": "relationship_goal",
            "Engineered Feature": "goal_alignment",
            "Feature Type": "Soft Similarity (0/1)",
            "Constraint Class": "SOFT PREFERENCE",
            "Handling of Unknown": "Does NOT block. Treated as neutral / Laplacian smoothed.",
            "Mathematical Definition": "1.0 if a.goal == b.goal else 0.0 (Latent weight: +0.70 first date, +0.40 MSMI)",
            "Used in Policy": "Yes (Core ranking component)",
            "Used in Evaluator": "Latent ground-truth driver of mutual acceptance & MSMI",
            "Strategic Purpose": "Decisive driver of first date acceptance and mutual second-meeting intention."
        },
        {
            "Raw Field": "relationship_pace",
            "Engineered Feature": "pace_alignment",
            "Feature Type": "Soft Similarity (0/1)",
            "Constraint Class": "SOFT PREFERENCE",
            "Handling of Unknown": "Does NOT block.",
            "Mathematical Definition": "1.0 if a.pace == b.pace else 0.0 (Latent weight: +0.40 first date)",
            "Used in Policy": "Yes (Core ranking component)",
            "Used in Evaluator": "Latent ground-truth driver of mutual acceptance",
            "Strategic Purpose": "Controls relationship escalation speed compatibility."
        },
        {
            "Raw Field": "lifestyle",
            "Engineered Feature": "lifestyle_alignment",
            "Feature Type": "Soft Similarity (0/1)",
            "Constraint Class": "SOFT PREFERENCE",
            "Handling of Unknown": "Does NOT block.",
            "Mathematical Definition": "1.0 if a.lifestyle == b.lifestyle else 0.0 (Latent weight: +0.25 first date)",
            "Used in Policy": "Yes (Secondary ranking)",
            "Used in Evaluator": "Latent ground-truth driver of mutual acceptance",
            "Strategic Purpose": "Measures day-to-day energy and free time alignment (quiet/mixed/social)."
        },
        {
            "Raw Field": "conversations",
            "Engineered Feature": "conversation_alignment",
            "Feature Type": "Soft Similarity (0/1)",
            "Constraint Class": "SOFT PREFERENCE",
            "Handling of Unknown": "Does NOT block.",
            "Mathematical Definition": "1.0 if a.conversations == b.conversations else 0.0 (Latent weight: +0.20 first date)",
            "Used in Policy": "Yes (Secondary ranking)",
            "Used in Evaluator": "Latent ground-truth driver of mutual acceptance",
            "Strategic Purpose": "Measures conversational style preference (ideas/stories/practical/playful)."
        },
        {
            "Raw Field": "SOFT_FIELDS (7 fields)",
            "Engineered Feature": "composite_soft_fit",
            "Feature Type": "Continuous [0.0, 1.0]",
            "Constraint Class": "COMPOSITE SOFT SCORE",
            "Handling of Unknown": "Calculated over observed overlap only. Neutral 0.0 if no shared known fields.",
            "Mathematical Definition": "sum(a[k] == b[k] for k in known_soft) / len(known_soft)",
            "Used in Policy": "Yes (Direct linear term in V2.2 scoring)",
            "Used in Evaluator": "Directly correlates with simulator acceptance probability",
            "Strategic Purpose": "Normalized pairwise compatibility metric under partial observability."
        },
        {
            "Raw Field": "Candidate graph degrees",
            "Engineered Feature": "degree_scarcity_bonus",
            "Feature Type": "Graph Centrality Heuristic",
            "Constraint Class": "ALLOCATION HEURISTIC",
            "Handling of Unknown": "Computed over current feasible graph.",
            "Mathematical Definition": "(1 / (deg(a) + 1) + 1 / (deg(b) + 1)) * 0.10",
            "Used in Policy": "Yes (Protects scarce members from being stranded)",
            "Used in Evaluator": "Improves overall pool coverage without sacrificing MSMI",
            "Strategic Purpose": "Allocates candidates with single options first to maximize total coverage."
        }
    ]
    return pd.DataFrame(records)


def parse_field_val(val: Any) -> Any:
    """Parse stringified JSON or raw field."""
    if val is None or pd.isna(val):
        return None
    if isinstance(val, str) and (val.startswith("[") or val.startswith("{")):
        try:
            return json.loads(val)
        except Exception:
            return val
    return val


def evaluate_pair_compatibility(a_row: Any, b_row: Any) -> Dict[str, Any]:
    """Evaluate reciprocal compatibility for two member profiles conforming to kit.py contract.
    Accepts either dictionaries or pandas Series.
    """
    aid = a_row["member_id"]
    bid = b_row["member_id"]

    if aid == bid:
        return {"status": "infeasible", "failed_reasons": ["same_member"], "unknown_reasons": [], "soft_score": 0.0}
    if a_row.get("pool_id") != b_row.get("pool_id"):
        return {"status": "infeasible", "failed_reasons": ["different_pool"], "unknown_reasons": [], "soft_score": 0.0}
    if min(a_row["age"], b_row["age"]) < 18:
        return {"status": "infeasible", "failed_reasons": ["underage"], "unknown_reasons": [], "soft_score": 0.0}

    # Extract pre-parsed fields directly
    fa = {}
    fb = {}
    for k in HARD_FIELDS + SOFT_FIELDS:
        va = a_row.get(f"raw_{k}")
        if va is None:
            va = parse_field_val(a_row.get(f"val_{k}"))
        fa[k] = va

        vb = b_row.get(f"raw_{k}")
        if vb is None:
            vb = parse_field_val(b_row.get(f"val_{k}"))
        fb[k] = vb

    missing_hard = []
    failed_hard = []

    # Track missing hard fields
    for m_id, f in ((aid, fa), (bid, fb)):
        for k in HARD_FIELDS:
            if f.get(k) is None:
                missing_hard.append(f"{m_id}:{k}")

    # Bidirectional checks
    for x, y, fx, fy in ((a_row, b_row, fa, fb), (b_row, a_row, fb, fa)):
        # Gender / who_to_meet
        if fx.get("who_to_meet") is not None and y["gender"] not in fx["who_to_meet"]:
            failed_hard.append("gender_preference")
        # Age
        if fx.get("age_min") is not None and y["age"] < fx["age_min"]:
            failed_hard.append("age_under_min")
        if fx.get("age_max") is not None and y["age"] > fx["age_max"]:
            failed_hard.append("age_over_max")
        # Geography
        if fx.get("acceptable_zones") is not None and y["zone"] not in fx["acceptable_zones"]:
            failed_hard.append("geography")
        # Smoking
        if fx.get("partner_smoking") == "no_smoking" and fy.get("smoking") in ("yes", "occasionally"):
            failed_hard.append("smoking")
        # Children presence
        if fx.get("partner_children") == "no_children" and fy.get("has_children") is True:
            failed_hard.append("children_present")

    # Symmetric checks
    if fa.get("relationship_structure") is not None and fb.get("relationship_structure") is not None:
        if fa["relationship_structure"] != fb["relationship_structure"]:
            failed_hard.append("relationship_structure")

    if {fa.get("wants_children"), fb.get("wants_children")} == {"yes", "no"}:
        failed_hard.append("children_plans")

    if fa.get("schedule") is not None and fb.get("schedule") is not None:
        if not set(fa["schedule"]).intersection(set(fb["schedule"])):
            failed_hard.append("schedule")

    failed_reasons = sorted(set(failed_hard))

    # A known hard failure takes precedence over missing information
    if failed_reasons:
        status = "infeasible"
    elif missing_hard:
        status = "needs_clarification"
    else:
        status = "feasible"

    # Soft compatibility calculation
    soft_matches = 0
    soft_evaluated = 0
    for k in SOFT_FIELDS:
        va, vb = fa.get(k), fb.get(k)
        if va is not None and vb is not None:
            soft_evaluated += 1
            if va == vb:
                soft_matches += 1

    soft_score = round(soft_matches / soft_evaluated, 3) if soft_evaluated > 0 else 0.0

    return {
        "status": status,
        "failed_reasons": failed_reasons,
        "unknown_reasons": missing_hard,
        "soft_score": soft_score,
        "soft_matches": soft_matches,
        "soft_evaluated": soft_evaluated,
        "soft_unknown": len(SOFT_FIELDS) - soft_evaluated
    }


if __name__ == "__main__":
    df_dict = get_feature_dictionary()
    print("Feature dictionary generated with", len(df_dict), "features.")
    print(df_dict[["Engineered Feature", "Constraint Class", "Handling of Unknown"]].head(8))

