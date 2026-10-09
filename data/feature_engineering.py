import os
import pandas as pd
import numpy as np
from itertools import combinations


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(
    BASE_DIR,
    "analysis_output",
    "all_questionnaires.csv"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "analysis_output"
)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "pair_level_features.csv"
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_text(value):
    """
    Standardize text values.

    Missing values remain as NaN.
    """
    if pd.isna(value):
        return np.nan

    value = str(value).strip().lower()

    if value in ["", "nan", "none", "null"]:
        return np.nan

    return value


def smoking_compatibility(person_a, person_b):
    """
    HARD CONSTRAINT:
    Check smoking compatibility between two people.

    Rules:
    - If A does not accept smoking and B smokes, incompatible.
    - If B does not accept smoking and A smokes, incompatible.
    - Missing smoking information = UNKNOWN.
    """

    smoking_a = clean_text(person_a.get("qa_smoking"))
    smoking_b = clean_text(person_b.get("qa_smoking"))

    partner_smoking_a = clean_text(
        person_a.get("qa_partner_smoking")
    )

    partner_smoking_b = clean_text(
        person_b.get("qa_partner_smoking")
    )

    # If actual smoking information is missing,
    # we cannot make a definite decision.
    if pd.isna(smoking_a) or pd.isna(smoking_b):
        return np.nan

    # A does not accept smoking, but B smokes
    if (
        partner_smoking_a == "not compatible for me"
        and smoking_b in ["yes", "occasionally"]
    ):
        return 0

    # B does not accept smoking, but A smokes
    if (
        partner_smoking_b == "not compatible for me"
        and smoking_a in ["yes", "occasionally"]
    ):
        return 0

    return 1


def children_compatibility(person_a, person_b):
    """
    HARD CONSTRAINT:
    Check compatibility based on existing children.

    Rules:
    - If A prefers not to be with someone who has children
      and B has children, incompatible.
    - Same logic in the opposite direction.
    - Missing actual children information = UNKNOWN.
    """

    children_a = clean_text(person_a.get("qa_has_children"))
    children_b = clean_text(person_b.get("qa_has_children"))

    partner_children_a = clean_text(
        person_a.get("qa_partner_children")
    )

    partner_children_b = clean_text(
        person_b.get("qa_partner_children")
    )

    # We need actual children information
    if pd.isna(children_a) or pd.isna(children_b):
        return np.nan

    # A prefers not to have a partner with children
    if (
        partner_children_a == "prefer not to"
        and children_b == "yes"
    ):
        return 0

    # B prefers not to have a partner with children
    if (
        partner_children_b == "prefer not to"
        and children_a == "yes"
    ):
        return 0

    return 1


def schedule_overlap_count(person_a, person_b):
    """
    Calculate the number of common available schedule slots.

    Example:

    A:
        weekday_evening
        weekend_day

    B:
        weekday_evening
        weekend_evening

    Result:
        1

    Missing schedule information = NaN.
    """

    schedule_a = clean_text(person_a.get("qa_schedule"))
    schedule_b = clean_text(person_b.get("qa_schedule"))

    if pd.isna(schedule_a) or pd.isna(schedule_b):
        return np.nan

    # Convert possible separators into a common format
    schedule_a = (
        str(schedule_a)
        .replace("|", ",")
        .replace(";", ",")
    )

    schedule_b = (
        str(schedule_b)
        .replace("|", ",")
        .replace(";", ",")
    )

    slots_a = {
        x.strip()
        for x in schedule_a.split(",")
        if x.strip()
    }

    slots_b = {
        x.strip()
        for x in schedule_b.split(",")
        if x.strip()
    }

    if not slots_a or not slots_b:
        return np.nan

    return len(slots_a.intersection(slots_b))


def location_compatibility(person_a, person_b):
    """
    Geography compatibility.

    Current implementation:
    - Same location = 1
    - Different location = 0
    - Missing location = UNKNOWN

    This is kept as a feature rather than automatically
    eliminating different-location pairs.
    """

    location_a = clean_text(person_a.get("qa_location"))
    location_b = clean_text(person_b.get("qa_location"))

    if pd.isna(location_a) or pd.isna(location_b):
        return np.nan

    return int(location_a == location_b)


def relationship_goal_compatibility(person_a, person_b):
    """
    SOFT CONSTRAINT:

    Same relationship goal = 1
    Different relationship goal = 0
    Missing information = UNKNOWN
    """

    goal_a = clean_text(
        person_a.get("qa_relationship_goal")
    )

    goal_b = clean_text(
        person_b.get("qa_relationship_goal")
    )

    if pd.isna(goal_a) or pd.isna(goal_b):
        return np.nan

    return float(goal_a == goal_b)


def calculate_soft_score(
    location_score,
    schedule_score,
    relationship_score
):
    """
    Calculate the average of available soft features.

    Missing values are ignored.

    Example:

    Location = 1
    Schedule = 1
    Goal = NaN

    Score = 1.0
    """

    values = [
        location_score,
        schedule_score,
        relationship_score
    ]

    valid_values = [
        float(value)
        for value in values
        if not pd.isna(value)
    ]

    if not valid_values:
        return np.nan

    return round(
        sum(valid_values) / len(valid_values),
        3
    )


def determine_hard_compatibility(
    smoking_score,
    children_score
):
    """
    Determine compatibility using HARD constraints.

    0 = incompatible
    1 = compatible
    NaN = unknown
    """

    values = [
        smoking_score,
        children_score
    ]

    # If any hard constraint definitely fails
    if any(value == 0 for value in values):
        return 0

    # If information is incomplete
    if any(pd.isna(value) for value in values):
        return np.nan

    return 1


def determine_time_compatibility(time_overlap_count):
    """
    Time compatibility:

    overlap > 0  -> compatible
    overlap == 0 -> incompatible
    missing       -> unknown
    """

    if pd.isna(time_overlap_count):
        return np.nan

    if time_overlap_count > 0:
        return 1

    return 0


def determine_match_status(
    hard_compatible,
    time_compatible
):
    """
    Final classification.

    INCOMPATIBLE:
        A hard constraint fails OR there is no time overlap.

    UNKNOWN:
        Required information is missing.

    FEASIBLE:
        Hard constraints pass and time is compatible.
    """

    if hard_compatible == 0:
        return "INCOMPATIBLE"

    if time_compatible == 0:
        return "INCOMPATIBLE"

    if pd.isna(hard_compatible):
        return "UNKNOWN"

    if pd.isna(time_compatible):
        return "UNKNOWN"

    return "FEASIBLE"


# ============================================================
# MAIN PROGRAM
# ============================================================

print("=" * 60)
print("FEATURE ENGINEERING")
print("=" * 60)


# ------------------------------------------------------------
# CHECK INPUT
# ------------------------------------------------------------

if not os.path.exists(INPUT_FILE):
    print()
    print("ERROR: Input file not found:")
    print(INPUT_FILE)
    print()
    print("Please run analysis.py first.")
    raise SystemExit(1)


# ------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------

df = pd.read_csv(INPUT_FILE)

print(f"Total members: {len(df)}")
print()


# ------------------------------------------------------------
# STANDARDIZE TEXT COLUMNS
# ------------------------------------------------------------

text_columns = [
    "gender",
    "city",
    "qa_age_range",
    "qa_conversations",
    "qa_emotional_availability",
    "qa_gender",
    "qa_has_children",
    "qa_lifestyle",
    "qa_location",
    "qa_partner_children",
    "qa_partner_smoking",
    "qa_relationship_goal",
    "qa_relationship_pace",
    "qa_relationship_structure",
    "qa_relocate",
    "qa_schedule",
    "qa_smoking",
    "qa_space_for_relationship",
    "qa_wants_children",
    "qa_who_to_meet"
]

for column in text_columns:
    if column in df.columns:
        df[column] = df[column].apply(clean_text)


# ------------------------------------------------------------
# CHECK MEMBER ID
# ------------------------------------------------------------

if "member_id" not in df.columns:
    print("ERROR: member_id column is missing.")
    raise SystemExit(1)


# ------------------------------------------------------------
# START PAIR GENERATION
# ------------------------------------------------------------

print("Creating pair-level features...")

all_pairs = []


# ------------------------------------------------------------
# PROCESS EACH DATASET SEPARATELY
# ------------------------------------------------------------

if "source_dataset" in df.columns:

    dataset_groups = df.groupby(
        "source_dataset",
        dropna=False
    )

else:

    # Fallback if source_dataset is not available
    df["source_dataset"] = "combined"

    dataset_groups = df.groupby(
        "source_dataset",
        dropna=False
    )


for dataset_name, dataset_df in dataset_groups:

    dataset_df = dataset_df.reset_index(drop=True)

    print(
        f"Processing {dataset_name}: "
        f"{len(dataset_df)} members"
    )

    # --------------------------------------------------------
    # CREATE ALL UNIQUE PAIRS
    # --------------------------------------------------------

    for index_a, index_b in combinations(
        range(len(dataset_df)),
        2
    ):

        person_a = dataset_df.iloc[index_a]
        person_b = dataset_df.iloc[index_b]

        # ----------------------------------------------------
        # MEMBER IDs
        # ----------------------------------------------------

        member_a = person_a["member_id"]
        member_b = person_b["member_id"]

        # ----------------------------------------------------
        # HARD CONSTRAINTS
        # ----------------------------------------------------

        smoking_score = smoking_compatibility(
            person_a,
            person_b
        )

        children_score = children_compatibility(
            person_a,
            person_b
        )

        hard_score = determine_hard_compatibility(
            smoking_score,
            children_score
        )

        # ----------------------------------------------------
        # TIME
        # ----------------------------------------------------

        time_overlap_count = schedule_overlap_count(
            person_a,
            person_b
        )

        time_score = determine_time_compatibility(
            time_overlap_count
        )

        # ----------------------------------------------------
        # GEOGRAPHY
        # ----------------------------------------------------

        location_score = location_compatibility(
            person_a,
            person_b
        )

        # ----------------------------------------------------
        # RELATIONSHIP GOAL
        # ----------------------------------------------------

        relationship_goal_score = (
            relationship_goal_compatibility(
                person_a,
                person_b
            )
        )

        # ----------------------------------------------------
        # SOFT SCORE
        # ----------------------------------------------------

        soft_score = calculate_soft_score(
            location_score,
            time_score,
            relationship_goal_score
        )

        # ----------------------------------------------------
        # FINAL STATUS
        # ----------------------------------------------------

        match_status = determine_match_status(
            hard_score,
            time_score
        )

        # ----------------------------------------------------
        # STORE PAIR
        # ----------------------------------------------------

        pair_record = {

            "source_dataset": dataset_name,

            "member_a": member_a,

            "member_b": member_b,

            # Hard constraints
            "smoking_compatible": smoking_score,

            "children_compatible": children_score,

            "hard_compatible": hard_score,

            # Time
            "time_overlap_count": time_overlap_count,

            "time_compatible": time_score,

            # Geography
            "location_compatible": location_score,

            # Soft preference
            "relationship_goal_score": (
                relationship_goal_score
            ),

            "soft_score": soft_score,

            # Final classification
            "match_status": match_status
        }

        all_pairs.append(pair_record)


# ============================================================
# CREATE DATAFRAME
# ============================================================

pair_df = pd.DataFrame(all_pairs)


# ============================================================
# ADD CANDIDATE INFORMATION
# ============================================================

print()
print("Calculating candidate statistics...")


# A pair is considered a feasible candidate when:
# match_status == FEASIBLE

feasible_pairs = pair_df[
    pair_df["match_status"] == "FEASIBLE"
].copy()


# Count feasible candidates for each member

candidate_counts_a = (
    feasible_pairs
    .groupby(
        ["source_dataset", "member_a"]
    )
    .size()
    .reset_index(
        name="candidate_count"
    )
    .rename(
        columns={
            "member_a": "member_id"
        }
    )
)

candidate_counts_b = (
    feasible_pairs
    .groupby(
        ["source_dataset", "member_b"]
    )
    .size()
    .reset_index(
        name="candidate_count"
    )
    .rename(
        columns={
            "member_b": "member_id"
        }
    )
)


# Combine both sides

candidate_counts = pd.concat(
    [
        candidate_counts_a,
        candidate_counts_b
    ],
    ignore_index=True
)


# If a person appears multiple times,
# add their candidate counts.

candidate_counts = (
    candidate_counts
    .groupby(
        ["source_dataset", "member_id"],
        as_index=False
    )["candidate_count"]
    .sum()
)


# ------------------------------------------------------------
# Add candidate count to original members
# ------------------------------------------------------------

member_candidate_df = df[
    [
        "source_dataset",
        "member_id"
    ]
].copy()


member_candidate_df = member_candidate_df.merge(
    candidate_counts,
    on=[
        "source_dataset",
        "member_id"
    ],
    how="left"
)


# People with no feasible candidate get 0

member_candidate_df["candidate_count"] = (
    member_candidate_df["candidate_count"]
    .fillna(0)
    .astype(int)
)


# N indicator:
# 1 = at least one candidate
# 0 = no candidate

member_candidate_df["has_candidate"] = (
    member_candidate_df["candidate_count"] > 0
).astype(int)


# ============================================================
# SAVE MEMBER-LEVEL CANDIDATE SUMMARY
# ============================================================

member_candidate_output = os.path.join(
    OUTPUT_DIR,
    "member_candidate_summary.csv"
)

member_candidate_df.to_csv(
    member_candidate_output,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 60)
print("FEATURE ENGINEERING COMPLETE")
print("=" * 60)

print(
    f"Total pair combinations: {len(pair_df)}"
)

print()

print("Match status:")
print(
    pair_df["match_status"]
    .value_counts(dropna=False)
)

print()

print("Hard compatibility:")
print(
    pair_df["hard_compatible"]
    .value_counts(dropna=False)
)

print()

print("Time compatibility:")
print(
    pair_df["time_compatible"]
    .value_counts(dropna=False)
)

print()

print("Members with at least one candidate (N):")

total_members = len(member_candidate_df)

members_with_candidate = (
    member_candidate_df["has_candidate"]
    .sum()
)

members_without_candidate = (
    total_members - members_with_candidate
)

print(
    f"Members with candidate: "
    f"{members_with_candidate}"
)

print(
    f"Members without candidate: "
    f"{members_without_candidate}"
)

print()

print("Average candidate count:")

print(
    round(
        member_candidate_df[
            "candidate_count"
        ].mean(),
        2
    )
)


# ============================================================
# SAVE OUTPUT
# ============================================================

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


pair_df.to_csv(
    OUTPUT_FILE,
    index=False
)


print()
print("Output files created:")
print()
print(
    "1.",
    OUTPUT_FILE
)

print(
    "2.",
    member_candidate_output
)

print()
print("=" * 60)