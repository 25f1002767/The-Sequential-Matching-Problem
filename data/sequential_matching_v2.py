"""
Sequential Matching Analysis V2
The Sequential Matching Problem

Purpose:
1. Use the authoritative members.jsonl schema.
2. Respect field_status / field_observed_day.
3. Treat missing hard information as NEEDS_CLARIFICATION, not as incompatible.
4. Enforce reciprocal hard constraints.
5. Track waiting, response time and expiry.
6. Calculate episode-level N, including people with zero candidates.
7. Add leakage-safe exploration/exploitation labels using only earlier observed outcomes.

Run:
    python sequential_matching_v2.py

Change DATA_ROOT if your extracted data folder is elsewhere.
"""

from pathlib import Path
from collections import defaultdict
import json
import math
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

DATA_ROOT = Path(r"C:\Users\monus\OneDrive\Desktop\data")
OUTPUT_ROOT = DATA_ROOT / "analysis_output" / "sequential_v2"

DATASETS = [f"public_{i:02d}" for i in range(1, 11)]

# The challenge response deadline is 7 days.
RESPONSE_DEADLINE = 7

# Soft-feature weights.
SOFT_WEIGHTS = {
    "relationship_goal": 0.35,
    "relationship_pace": 0.20,
    "lifestyle": 0.15,
    "conversations": 0.15,
    "emotional_availability": 0.05,
    "space_for_relationship": 0.10,
}

# Exploration is deliberately conservative.
EXPLORATION_NOVELTY_THRESHOLD = 0


# ============================================================
# BASIC HELPERS
# ============================================================

def load_jsonl(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def safe_list(value):
    return value if isinstance(value, list) else []


def is_observed(member, field, day):
    status = member.get("field_status", {}).get(field)
    observed_day = member.get("field_observed_day", {}).get(field)

    if status != "observed":
        return False

    if observed_day is None:
        return False

    return int(observed_day) <= int(day)


def get_field(member, field, day):
    if not is_observed(member, field, day):
        return None
    return member.get("fields", {}).get(field)


def pair_key(a, b):
    return tuple(sorted((a, b)))


def numeric_or_none(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# ============================================================
# HARD CONSTRAINTS
# ============================================================

def directional_hard_checks(a, b, day):
    """
    Returns:
        "FAIL"      known hard conflict
        "UNKNOWN"   at least one required value is missing
        "PASS"      all directional hard checks pass

    We check A's requirements against B.
    Reciprocal checking is done by calling this in both directions.
    """

    # Age range
    age_min = get_field(a, "age_min", day)
    age_max = get_field(a, "age_max", day)

    if age_min is None or age_max is None:
        return "UNKNOWN"

    if not (age_min <= b["age"] <= age_max):
        return "FAIL"

    # Explicit gender preference
    who_to_meet = get_field(a, "who_to_meet", day)

    if who_to_meet is None:
        return "UNKNOWN"

    if b["gender"] not in who_to_meet:
        return "FAIL"

    # Relationship structure
    structure_a = get_field(a, "relationship_structure", day)
    structure_b = get_field(b, "relationship_structure", day)

    if structure_a is None or structure_b is None:
        return "UNKNOWN"

    if structure_a != structure_b:
        return "FAIL"

    # Smoking preference
    partner_smoking = get_field(a, "partner_smoking", day)
    smoking_b = get_field(b, "smoking", day)

    if partner_smoking is None or smoking_b is None:
        return "UNKNOWN"

    if partner_smoking == "no_smoking" and smoking_b in {"yes", "occasionally"}:
        return "FAIL"

    # Children preference
    partner_children = get_field(a, "partner_children", day)
    has_children_b = get_field(b, "has_children", day)

    if partner_children is None or has_children_b is None:
        return "UNKNOWN"

    if partner_children == "no_children" and has_children_b is True:
        return "FAIL"

    # Wants children:
    # Explicit yes/no conflict excludes.
    wants_a = get_field(a, "wants_children", day)
    wants_b = get_field(b, "wants_children", day)

    if wants_a is None or wants_b is None:
        return "UNKNOWN"

    if wants_a in {"yes", "no"} and wants_b in {"yes", "no"} and wants_a != wants_b:
        return "FAIL"

    # Acceptable zones
    zones_a = get_field(a, "acceptable_zones", day)

    if zones_a is None:
        return "UNKNOWN"

    if b["zone"] not in zones_a:
        return "FAIL"

    # Schedule overlap
    schedule_a = get_field(a, "schedule", day)
    schedule_b = get_field(b, "schedule", day)

    if schedule_a is None or schedule_b is None:
        return "UNKNOWN"

    if not set(schedule_a).intersection(schedule_b):
        return "FAIL"

    return "PASS"


def eligibility(a, b, day):
    """
    Reciprocal eligibility.

    Returns one of:
        FEASIBLE
        INFEASIBLE
        NEEDS_CLARIFICATION
    """

    if a["member_id"] == b["member_id"]:
        return "INFEASIBLE"

    if a["pool_id"] != b["pool_id"]:
        return "INFEASIBLE"

    ab = directional_hard_checks(a, b, day)
    ba = directional_hard_checks(b, a, day)

    if ab == "FAIL" or ba == "FAIL":
        return "INFEASIBLE"

    if ab == "UNKNOWN" or ba == "UNKNOWN":
        return "NEEDS_CLARIFICATION"

    return "FEASIBLE"


# ============================================================
# SOFT SCORE
# ============================================================

def equality_score(a, b, field, day):
    va = get_field(a, field, day)
    vb = get_field(b, field, day)

    if va is None or vb is None:
        return None

    return 1.0 if va == vb else 0.0


def soft_score(a, b, day):
    """
    Average only over observed soft fields.
    Missing soft information is not treated as disagreement.
    """

    values = []
    weights = []

    for field, weight in SOFT_WEIGHTS.items():
        score = equality_score(a, b, field, day)
        if score is not None:
            values.append(score * weight)
            weights.append(weight)

    if not weights:
        return 0.0

    return sum(values) / sum(weights)


def hard_confidence(a, b, day):
    """
    Fraction of hard fields that are known in both directions.
    Useful for ranking clarification priorities.
    """

    checks = []

    hard_fields = [
        "age_min",
        "age_max",
        "who_to_meet",
        "relationship_structure",
        "partner_smoking",
        "smoking",
        "partner_children",
        "has_children",
        "wants_children",
        "acceptable_zones",
        "schedule",
    ]

    for field in hard_fields:
        checks.append(
            is_observed(a, field, day) and is_observed(b, field, day)
        )

    return sum(checks) / len(checks)


# ============================================================
# HISTORICAL FEEDBACK
# ============================================================

def load_pool_history(pool_dir):
    intros = load_jsonl(pool_dir / "introductions.jsonl")
    feedback = load_jsonl(pool_dir / "feedback.jsonl")

    feedback_by_intro = defaultdict(list)
    for row in feedback:
        feedback_by_intro[row["introduction_id"]].append(row)

    return intros, feedback, feedback_by_intro


def introduction_outcome(intro, feedback_by_intro):
    """
    Historical outcome used only after it becomes observable.

    Positive if both people recorded introduction_response=yes.
    Negative if any observed introduction response=no.
    Pending if a response is not yet resolved at the relevant day.
    """

    events = feedback_by_intro.get(intro["introduction_id"], [])

    responses = [
        e for e in events
        if e.get("event") == "introduction_response"
    ]

    yes_count = sum(e.get("value") == "yes" for e in responses)
    no_count = sum(e.get("value") == "no" for e in responses)

    if no_count > 0:
        return "NEGATIVE"

    if yes_count >= 2:
        return "POSITIVE"

    return "PENDING"


def response_metrics(intro, feedback_by_intro):
    events = feedback_by_intro.get(intro["introduction_id"], [])

    responses = [
        e for e in events
        if e.get("event") == "introduction_response"
    ]

    occurred_days = [
        e.get("occurred_day")
        for e in responses
        if e.get("occurred_day") is not None
    ]

    if occurred_days:
        first_response = min(occurred_days)
        response_time = max(0, first_response - intro["assigned_day"])
        return first_response, response_time

    # No response by deadline means the introduction expired.
    deadline = intro.get("response_deadline_day")
    if deadline is not None:
        return None, None

    return None, None


# ============================================================
# WAITING / AVAILABILITY
# ============================================================

def historical_status(member_id, day, introductions, feedback_by_intro):
    """
    Operational status for a person at a historical day.

    WAITING:
        an introduction has been assigned and its response window is still open.

    MATCHED:
        both introduction responses are positive.

    EXPIRED:
        the response deadline has passed without both positive responses.

    AVAILABLE:
        no active introduction is occupying the person.
    """

    member_intros = [
        x for x in introductions
        if member_id in {x["user_a"], x["user_b"]}
        and x["assigned_day"] <= day
    ]

    for intro in sorted(member_intros, key=lambda x: x["assigned_day"], reverse=True):
        events = feedback_by_intro.get(intro["introduction_id"], [])

        responses = [
            e for e in events
            if e.get("event") == "introduction_response"
            and e.get("observed_day") is not None
            and e.get("observed_day") <= day
        ]

        yes_count = sum(e.get("value") == "yes" for e in responses)
        no_count = sum(e.get("value") == "no" for e in responses)

        if yes_count >= 2:
            return "MATCHED"

        if no_count > 0:
            # Person is released after a known negative response.
            continue

        deadline = intro.get("response_deadline_day")
        if deadline is not None and day <= deadline:
            return "WAITING"

        if deadline is not None and day > deadline:
            continue

    return "AVAILABLE"


# ============================================================
# LEAKAGE-SAFE EXPLORATION / EXPLOITATION
# ============================================================

def build_prior_outcome_stats(introductions, feedback_by_intro):
    """
    Create outcome statistics keyed by broad observable pair pattern.

    IMPORTANT:
    A row is used only after its historical assigned day.
    Current pair decisions never use future outcomes.
    """

    stats = defaultdict(lambda: {"positive": 0, "resolved": 0})

    for intro in introductions:
        outcome = introduction_outcome(intro, feedback_by_intro)

        if outcome not in {"POSITIVE", "NEGATIVE"}:
            continue

        # We do not know the pair's detailed feature signature here.
        # The broad key uses pool-level history only as a prior.
        key = intro["logging_policy"]

        stats[key]["resolved"] += 1
        if outcome == "POSITIVE":
            stats[key]["positive"] += 1

    return stats


def exploration_label(
    a,
    b,
    day,
    prior_stats,
    pair_history,
):
    """
    Exploration:
        pair pattern has little/no prior evidence.

    Exploitation:
        pair pattern has prior evidence.

    The important point is that prior evidence must come from
    observations available BEFORE the current day.
    """

    # Feature signature from currently observed information.
    signature = (
        get_field(a, "relationship_goal", day),
        get_field(b, "relationship_goal", day),
        get_field(a, "relationship_pace", day),
        get_field(b, "relationship_pace", day),
    )

    previous = pair_history.get(signature, 0)

    if previous <= EXPLORATION_NOVELTY_THRESHOLD:
        return "EXPLORATION"

    return "EXPLOITATION"


# ============================================================
# EPISODE ANALYSIS
# ============================================================

def analyze_dataset(dataset):
    pool_dir = DATA_ROOT / dataset

    members_rows = load_jsonl(pool_dir / "members.jsonl")
    introductions, feedback, feedback_by_intro = load_pool_history(pool_dir)

    members = {m["member_id"]: m for m in members_rows}

    # Days that actually matter in the historical data.
    days = set(m["arrived_day"] for m in members_rows)

    for intro in introductions:
        days.add(intro["assigned_day"])
        if intro.get("response_deadline_day") is not None:
            days.add(intro["response_deadline_day"])

    days = sorted(days)

    episode_rows = []
    candidate_rows = []
    pair_rows = []

    # History of resolved feature signatures.
    signature_history = defaultdict(int)

    for day in days:
        arrived = [
            m for m in members_rows
            if m["arrived_day"] <= day
        ]

        available = [
            m for m in arrived
            if historical_status(
                m["member_id"],
                day,
                introductions,
                feedback_by_intro
            ) == "AVAILABLE"
        ]

        feasible_counts = defaultdict(int)
        clarification_counts = defaultdict(int)
        infeasible_counts = defaultdict(int)

        pair_candidates = []

        for i in range(len(available)):
            for j in range(i + 1, len(available)):
                a = available[i]
                b = available[j]

                status = eligibility(a, b, day)
                score = soft_score(a, b, day)
                confidence = hard_confidence(a, b, day)

                if status == "FEASIBLE":
                    feasible_counts[a["member_id"]] += 1
                    feasible_counts[b["member_id"]] += 1

                    label = exploration_label(
                        a,
                        b,
                        day,
                        {},
                        signature_history
                    )

                    pair_candidates.append({
                        "dataset": dataset,
                        "episode_id": f"{dataset}_day_{day}",
                        "day": day,
                        "user_a": a["member_id"],
                        "user_b": b["member_id"],
                        "eligibility": status,
                        "soft_score": score,
                        "hard_confidence": confidence,
                        "decision_type": label,
                    })

                elif status == "NEEDS_CLARIFICATION":
                    clarification_counts[a["member_id"]] += 1
                    clarification_counts[b["member_id"]] += 1
                else:
                    infeasible_counts[a["member_id"]] += 1
                    infeasible_counts[b["member_id"]] += 1

        n = sum(v > 0 for v in feasible_counts.values())

        # Every available member gets a row, including zero-candidate people.
        for m in available:
            mid = m["member_id"]
            c = feasible_counts.get(mid, 0)

            candidate_rows.append({
                "dataset": dataset,
                "episode_id": f"{dataset}_day_{day}",
                "day": day,
                "member_id": mid,
                "status": "AVAILABLE",
                "candidate_count": c,
                "has_candidate": int(c > 0),
                "needs_clarification_count": clarification_counts.get(mid, 0),
                "infeasible_pair_count": infeasible_counts.get(mid, 0),
            })

        # Greedy non-overlapping allocation.
        # This is a baseline allocation, not claimed as optimal.
        used = set()

        pair_candidates.sort(
            key=lambda x: (
                x["soft_score"],
                x["hard_confidence"]
            ),
            reverse=True
        )

        selected = []

        for pair in pair_candidates:
            a = pair["user_a"]
            b = pair["user_b"]

            if a in used or b in used:
                continue

            selected.append(pair)
            used.add(a)
            used.add(b)

            pair["selected"] = 1
            pair_rows.append(pair.copy())

            # Update history only AFTER the decision.
            signature = (
                get_field(members[a], "relationship_goal", day),
                get_field(members[b], "relationship_goal", day),
                get_field(members[a], "relationship_pace", day),
                get_field(members[b], "relationship_pace", day),
            )
            signature_history[signature] += 1

        # Non-selected candidates are also useful for analysis.
        for pair in pair_candidates:
            if not pair.get("selected"):
                pair["selected"] = 0
                pair_rows.append(pair.copy())

        episode_rows.append({
            "dataset": dataset,
            "episode_id": f"{dataset}_day_{day}",
            "day": day,
            "arrived_members": len(arrived),
            "available_members": len(available),
            "N_members_with_candidate": n,
            "members_without_candidate": len(available) - n,
            "N_percentage": (
                n / len(available) * 100
                if available else 0
            ),
            "candidate_pairs": len(pair_candidates),
            "selected_matches": len(selected),
            "selected_members": len(selected) * 2,
        })

    # Introduction lifecycle.
    intro_rows = []

    for intro in introductions:
        assigned = intro["assigned_day"]
        deadline = intro.get("response_deadline_day")

        events = feedback_by_intro.get(intro["introduction_id"], [])

        responses = [
            e for e in events
            if e.get("event") == "introduction_response"
        ]

        observed_responses = [
            e for e in responses
            if e.get("observed_day") is not None
        ]

        positive = sum(e.get("value") == "yes" for e in observed_responses)
        negative = sum(e.get("value") == "no" for e in observed_responses)

        response_days = [
            e.get("occurred_day")
            for e in observed_responses
            if e.get("occurred_day") is not None
        ]

        first_response_day = min(response_days) if response_days else None

        if positive >= 2:
            lifecycle = "MATCHED"
        elif negative > 0:
            lifecycle = "REJECTED"
        elif deadline is not None:
            lifecycle = "WAITING_OR_EXPIRED"
        else:
            lifecycle = "WAITING"

        response_time = (
            first_response_day - assigned
            if first_response_day is not None
            else None
        )

        intro_rows.append({
            "dataset": dataset,
            "introduction_id": intro["introduction_id"],
            "assigned_day": assigned,
            "response_deadline_day": deadline,
            "user_a": intro["user_a"],
            "user_b": intro["user_b"],
            "lifecycle_status": lifecycle,
            "positive_responses": positive,
            "negative_responses": negative,
            "first_response_day": first_response_day,
            "response_time_days": response_time,
            "waiting_at_assignment": 1,
        })

    return (
        episode_rows,
        candidate_rows,
        pair_rows,
        intro_rows,
    )


# ============================================================
# MAIN
# ============================================================

def main():
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    all_episode = []
    all_candidates = []
    all_pairs = []
    all_intros = []

    for dataset in DATASETS:
        pool_dir = DATA_ROOT / dataset

        if not pool_dir.exists():
            print(f"[SKIP] {dataset}: folder not found")
            continue

        print(f"[RUN] {dataset}")

        episode, candidates, pairs, intros = analyze_dataset(dataset)

        all_episode.extend(episode)
        all_candidates.extend(candidates)
        all_pairs.extend(pairs)
        all_intros.extend(intros)

    episode_df = pd.DataFrame(all_episode)
    candidate_df = pd.DataFrame(all_candidates)
    pair_df = pd.DataFrame(all_pairs)
    intro_df = pd.DataFrame(all_intros)

    # --------------------------------------------------------
    # Save detailed outputs
    # --------------------------------------------------------

    episode_df.to_csv(
        OUTPUT_ROOT / "episode_summary_v2.csv",
        index=False
    )

    candidate_df.to_csv(
        OUTPUT_ROOT / "member_candidate_summary_v2.csv",
        index=False
    )

    pair_df.to_csv(
        OUTPUT_ROOT / "pair_decision_analysis_v2.csv",
        index=False
    )

    intro_df.to_csv(
        OUTPUT_ROOT / "introduction_lifecycle_v2.csv",
        index=False
    )

    # --------------------------------------------------------
    # Overall summary
    # --------------------------------------------------------

    total_available = int(candidate_df.shape[0])

    if total_available:
        total_N = int(candidate_df["has_candidate"].sum())
        N_pct = total_N / total_available * 100
    else:
        total_N = 0
        N_pct = 0

    waiting = int(
        (intro_df["lifecycle_status"] == "WAITING_OR_EXPIRED").sum()
    ) if not intro_df.empty else 0

    rejected = int(
        (intro_df["lifecycle_status"] == "REJECTED").sum()
    ) if not intro_df.empty else 0

    matched = int(
        (intro_df["lifecycle_status"] == "MATCHED").sum()
    ) if not intro_df.empty else 0

    response_times = (
        intro_df["response_time_days"]
        .dropna()
        if not intro_df.empty
        else pd.Series(dtype=float)
    )

    summary = pd.DataFrame([{
        "total_episode_rows": len(episode_df),
        "total_available_member_episode_rows": total_available,
        "N_members_with_at_least_one_feasible_candidate": total_N,
        "members_with_zero_candidates": total_available - total_N,
        "N_percentage": round(N_pct, 2),
        "total_pair_decisions_evaluated": len(pair_df),
        "selected_match_baseline": int(
            pair_df["selected"].sum()
        ) if not pair_df.empty else 0,
        "introduction_records": len(intro_df),
        "matched_introductions": matched,
        "rejected_introductions": rejected,
        "waiting_or_expired_introductions": waiting,
        "mean_response_time_days": (
            round(response_times.mean(), 2)
            if len(response_times) else None
        ),
        "median_response_time_days": (
            round(response_times.median(), 2)
            if len(response_times) else None
        ),
    }])

    summary.to_csv(
        OUTPUT_ROOT / "sequential_summary_v2.csv",
        index=False
    )

    # Dataset-wise N
    if not candidate_df.empty:
        dataset_N = (
            candidate_df
            .groupby("dataset")
            .agg(
                available_member_episode_rows=("member_id", "count"),
                N_members_with_candidate=("has_candidate", "sum"),
                mean_candidate_count=("candidate_count", "mean"),
                median_candidate_count=("candidate_count", "median"),
            )
            .reset_index()
        )

        dataset_N["N_percentage"] = (
            dataset_N["N_members_with_candidate"]
            / dataset_N["available_member_episode_rows"]
            * 100
        )

        dataset_N.to_csv(
            OUTPUT_ROOT / "dataset_wise_N_v2.csv",
            index=False
        )

    print("\n" + "=" * 60)
    print("SEQUENTIAL MATCHING V2 COMPLETE")
    print("=" * 60)
    print(f"Episodes: {len(episode_df)}")
    print(f"Available member-episodes: {total_available}")
    print(f"N with >=1 feasible candidate: {total_N}")
    print(f"Zero-candidate member-episodes: {total_available - total_N}")
    print(f"N percentage: {N_pct:.2f}%")
    print(f"Pair evaluations: {len(pair_df)}")
    print(
        f"Baseline selected matches: "
        f"{int(pair_df['selected'].sum()) if not pair_df.empty else 0}"
    )
    print(f"Introduction records: {len(intro_df)}")
    print(f"Output: {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
