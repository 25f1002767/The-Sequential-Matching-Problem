from pathlib import Path
import json
import pandas as pd
from collections import Counter, defaultdict

# ============================================================
# CONFIG
# ============================================================

DATA_ROOT = Path(r"C:\Users\monus\OneDrive\Desktop\data")
V2_ROOT = DATA_ROOT / "analysis_output" / "sequential_v2"

DATASETS = [f"public_{i:02d}" for i in range(1, 11)]

# ============================================================
# HELPERS
# ============================================================

def load_jsonl(path):
    rows = []

    if not path.exists():
        return rows

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            try:
                rows.append(json.loads(line))
            except Exception:
                pass

    return rows


def flatten_member(member):
    """
    Convert nested member structure into a simple dictionary.
    """

    fields = member.get("fields", {})
    statuses = member.get("field_status", {})
    observed_days = member.get("field_observed_day", {})

    result = {
        "member_id": member.get("member_id"),
        "gender": member.get("gender"),
        "age": member.get("age"),
        "zone": member.get("zone"),
        "pool_id": member.get("pool_id"),
        "arrived_day": member.get("arrived_day"),
    }

    for field in [
        "age_min",
        "age_max",
        "who_to_meet",
        "relationship_structure",
        "smoking",
        "partner_smoking",
        "has_children",
        "partner_children",
        "wants_children",
        "acceptable_zones",
        "schedule",
        "relationship_goal",
        "relationship_pace",
        "lifestyle",
        "conversations",
        "emotional_availability",
        "space_for_relationship",
    ]:
        result[field] = fields.get(field)
        result[f"{field}_status"] = statuses.get(field)
        result[f"{field}_observed_day"] = observed_days.get(field)

    return result


def value_to_string(value):
    if value is None:
        return "MISSING"

    if isinstance(value, list):
        return " | ".join(str(x) for x in value)

    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)

    return str(value)


# ============================================================
# 1. CHECK V2 OUTPUT FILES
# ============================================================

print("\n" + "=" * 70)
print("V2 OUTPUT AUDIT")
print("=" * 70)

required_files = [
    "episode_summary_v2.csv",
    "member_candidate_summary_v2.csv",
    "pair_decision_analysis_v2.csv",
    "introduction_lifecycle_v2.csv",
    "sequential_summary_v2.csv",
    "dataset_wise_N_v2.csv",
]

for filename in required_files:
    path = V2_ROOT / filename

    if path.exists():
        df = pd.read_csv(path)

        print(
            f"OK   {filename:<35} "
            f"rows={len(df):,} cols={len(df.columns)}"
        )
    else:
        print(f"MISS {filename}")


# ============================================================
# 2. READ V2 SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("OVERALL V2 NUMBERS")
print("=" * 70)

summary_path = V2_ROOT / "sequential_summary_v2.csv"

if summary_path.exists():
    summary = pd.read_csv(summary_path)

    print(summary.to_string(index=False))

else:
    print("sequential_summary_v2.csv not found.")


# ============================================================
# 3. DATASET-WISE V2 ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("DATASET-WISE V2 RESULTS")
print("=" * 70)

dataset_path = V2_ROOT / "dataset_wise_N_v2.csv"

if dataset_path.exists():

    dataset_df = pd.read_csv(dataset_path)

    print(dataset_df.to_string(index=False))

else:
    print("dataset_wise_N_v2.csv not found.")


# ============================================================
# 4. CHECK RAW MEMBER DATA
# ============================================================

print("\n" + "=" * 70)
print("RAW MEMBER VALUE AUDIT")
print("=" * 70)

all_members = []

for dataset in DATASETS:

    path = DATA_ROOT / dataset / "members.jsonl"

    members = load_jsonl(path)

    print(
        f"{dataset}: {len(members)} members"
    )

    for member in members:

        row = flatten_member(member)
        row["source_dataset"] = dataset

        all_members.append(row)


members_df = pd.DataFrame(all_members)

print(
    f"\nTotal raw members loaded: {len(members_df):,}"
)


# ============================================================
# 5. VALUE DISTRIBUTIONS
# ============================================================

fields_to_check = [
    "smoking",
    "partner_smoking",
    "has_children",
    "partner_children",
    "wants_children",
    "relationship_structure",
    "who_to_meet",
    "acceptable_zones",
    "schedule",
    "relationship_goal",
    "relationship_pace",
]


for field in fields_to_check:

    print("\n" + "-" * 70)
    print(f"FIELD: {field}")
    print("-" * 70)

    counter = Counter()

    for value in members_df[field]:

        counter[value_to_string(value)] += 1

    for value, count in counter.most_common(20):

        print(f"{count:>5}  {value}")


# ============================================================
# 6. DATA TYPES CHECK
# ============================================================

print("\n" + "=" * 70)
print("DATA TYPE CHECK")
print("=" * 70)

for field in fields_to_check:

    type_counter = Counter()

    for value in members_df[field]:

        if value is None:
            value_type = "None"

        elif isinstance(value, list):
            value_type = "list"

        elif isinstance(value, dict):
            value_type = "dict"

        elif isinstance(value, bool):
            value_type = "bool"

        elif isinstance(value, (int, float)):
            value_type = "number"

        else:
            value_type = "string"

        type_counter[value_type] += 1

    print(
        f"{field:<30} "
        f"{dict(type_counter)}"
    )


# ============================================================
# 7. MISSINGNESS CHECK
# ============================================================

print("\n" + "=" * 70)
print("MISSING / UNKNOWN DATA")
print("=" * 70)

for field in fields_to_check:

    missing = 0
    observed = 0

    for value in members_df[field]:

        if value is None or value == [] or value == "":
            missing += 1
        else:
            observed += 1

    total = missing + observed

    percentage = (
        missing / total * 100
        if total
        else 0
    )

    print(
        f"{field:<30} "
        f"missing={missing:>5} "
        f"observed={observed:>5} "
        f"missing%={percentage:>6.2f}"
    )


# ============================================================
# 8. V2 CANDIDATE SUMMARY ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("CANDIDATE COUNT ANALYSIS")
print("=" * 70)

candidate_path = V2_ROOT / "member_candidate_summary_v2.csv"

if candidate_path.exists():

    candidate_df = pd.read_csv(candidate_path)

    print(
        f"Rows: {len(candidate_df):,}"
    )

    if "candidate_count" in candidate_df.columns:

        print(
            "\nCandidate count statistics:"
        )

        print(
            candidate_df["candidate_count"]
            .describe()
            .to_string()
        )

    if "has_candidate" in candidate_df.columns:

        print(
            "\nHas candidate:"
        )

        print(
            candidate_df["has_candidate"]
            .value_counts(dropna=False)
            .to_string()
        )

    if "source_dataset" in candidate_df.columns:

        print(
            "\nDataset-wise candidate statistics:"
        )

        dataset_candidate = (
            candidate_df
            .groupby("source_dataset")
            .agg(
                member_episodes=("member_id", "count"),
                with_candidate=("has_candidate", "sum"),
                total_candidates=("candidate_count", "sum"),
            )
            .reset_index()
        )

        dataset_candidate["N_percentage"] = (
            dataset_candidate["with_candidate"]
            / dataset_candidate["member_episodes"]
            * 100
        )

        print(
            dataset_candidate.to_string(index=False)
        )

else:
    print(
        "member_candidate_summary_v2.csv not found."
    )


# ============================================================
# 9. PAIR DECISION ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("PAIR DECISION ANALYSIS")
print("=" * 70)

pair_path = V2_ROOT / "pair_decision_analysis_v2.csv"

if pair_path.exists():

    pair_df = pd.read_csv(pair_path)

    print(
        f"Pair decision rows: {len(pair_df):,}"
    )

    if "decision" in pair_df.columns:

        print(
            "\nDecision distribution:"
        )

        print(
            pair_df["decision"]
            .value_counts(dropna=False)
            .to_string()
        )

    if "source_dataset" in pair_df.columns:

        print(
            "\nDataset-wise pair decisions:"
        )

        print(
            pd.crosstab(
                pair_df["source_dataset"],
                pair_df["decision"]
            ).to_string()
        )

else:

    print(
        "pair_decision_analysis_v2.csv not found."
    )


# ============================================================
# 10. INTRODUCTION LIFECYCLE
# ============================================================

print("\n" + "=" * 70)
print("INTRODUCTION LIFECYCLE")
print("=" * 70)

intro_path = V2_ROOT / "introduction_lifecycle_v2.csv"

if intro_path.exists():

    intro_df = pd.read_csv(intro_path)

    print(
        f"Introduction records: {len(intro_df):,}"
    )

    if "lifecycle_status" in intro_df.columns:

        print(
            intro_df["lifecycle_status"]
            .value_counts(dropna=False)
            .to_string()
        )

    if "response_time_days" in intro_df.columns:

        response_time = pd.to_numeric(
            intro_df["response_time_days"],
            errors="coerce"
        )

        print(
            "\nResponse time:"
        )

        print(
            response_time.describe()
            .to_string()
        )

else:

    print(
        "introduction_lifecycle_v2.csv not found."
    )


# ============================================================
# 11. CHECK FOR REPEATED BASELINE MATCHES
# ============================================================

print("\n" + "=" * 70)
print("REPEATED BASELINE MATCH CHECK")
print("=" * 70)

if pair_path.exists():

    pair_df = pd.read_csv(pair_path)

    selected_col = None

    for col in [
        "selected",
        "selected_match",
        "baseline_selected",
    ]:

        if col in pair_df.columns:

            selected_col = col
            break

    if selected_col:

        selected = pair_df[
            pair_df[selected_col].astype(str).str.lower()
            .isin(["1", "true", "yes"])
        ].copy()

        print(
            f"Selected pair records: {len(selected):,}"
        )

        if {
            "user_a",
            "user_b"
        }.issubset(selected.columns):

            selected["pair_key"] = (
                selected["user_a"].astype(str)
                + "||"
                + selected["user_b"].astype(str)
            )

            repeated = (
                selected["pair_key"]
                .value_counts()
            )

            repeated = repeated[
                repeated > 1
            ]

            print(
                f"Repeated pair selections: "
                f"{len(repeated):,}"
            )

            if len(repeated) > 0:

                print(
                    "\nTop repeated pairs:"
                )

                print(
                    repeated.head(20)
                    .to_string()
                )

    else:

        print(
            "Could not identify selected-match column."
        )


# ============================================================
# 12. FINAL DIAGNOSIS
# ============================================================

print("\n" + "=" * 70)
print("AUDIT COMPLETE")
print("=" * 70)

print(
    """
What we are looking for:

1. Unexpected raw values
   Example:
   partner_smoking = "Open to it"
   while V2 expects = "no_smoking"

2. Very high missingness in hard constraints.

3. A constraint that eliminates almost every pair.

4. Very low feasible-candidate percentage.

5. Repeated baseline matches across episodes.

6. WAITING_OR_EXPIRED being used without a real expiry calculation.

7. Relationship structure being too restrictive.

Do NOT change the matching code yet.

First use this audit to identify the actual bottleneck.
"""
)

print("=" * 70)