import os
import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_DIR = os.path.join(
    BASE_DIR,
    "analysis_output"
)

QUESTIONNAIRE_FILE = os.path.join(
    INPUT_DIR,
    "all_questionnaires.csv"
)

PAIR_FILE = os.path.join(
    INPUT_DIR,
    "pair_level_features.csv"
)

CANDIDATE_FILE = os.path.join(
    INPUT_DIR,
    "member_candidate_summary.csv"
)

OUTPUT_DIR = os.path.join(
    INPUT_DIR,
    "descriptive_results"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# TITLE
# ============================================================

print("=" * 70)
print("DESCRIPTIVE ANALYSIS")
print("=" * 70)


# ============================================================
# LOAD DATA
# ============================================================

print()
print("Loading datasets...")

questionnaire_df = pd.read_csv(
    QUESTIONNAIRE_FILE
)

pair_df = pd.read_csv(
    PAIR_FILE
)

candidate_df = pd.read_csv(
    CANDIDATE_FILE
)

print(
    f"Questionnaire records: {len(questionnaire_df)}"
)

print(
    f"Pair records: {len(pair_df)}"
)

print(
    f"Candidate records: {len(candidate_df)}"
)


# ============================================================
# 1. BASIC DATASET SUMMARY
# ============================================================

basic_summary = pd.DataFrame({
    "metric": [
        "Total members",
        "Total pair combinations",
        "Total datasets",
        "Members with at least one candidate",
        "Members without candidate",
        "Average candidate count"
    ],

    "value": [
        len(questionnaire_df),
        len(pair_df),
        questionnaire_df["source_dataset"].nunique(),
        int(candidate_df["has_candidate"].sum()),
        int(
            (candidate_df["has_candidate"] == 0).sum()
        ),
        round(
            candidate_df["candidate_count"].mean(),
            2
        )
    ]
})

basic_summary.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "01_basic_summary.csv"
    ),
    index=False
)


# ============================================================
# 2. AGE ANALYSIS
# ============================================================

print()
print("Analyzing age...")

age_summary = questionnaire_df["age"].describe()

age_summary_df = age_summary.reset_index()

age_summary_df.columns = [
    "statistic",
    "value"
]

age_summary_df.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "02_age_summary.csv"
    ),
    index=False
)


# Age groups

age_bins = [
    20,
    25,
    30,
    35,
    40,
    45,
    50
]

age_labels = [
    "21-25",
    "26-30",
    "31-35",
    "36-40",
    "41-45",
    "46-50"
]

questionnaire_df["age_group"] = pd.cut(
    questionnaire_df["age"],
    bins=age_bins,
    labels=age_labels,
    include_lowest=True
)

age_group_counts = (
    questionnaire_df["age_group"]
    .value_counts()
    .sort_index()
    .reset_index()
)

age_group_counts.columns = [
    "age_group",
    "count"
]

age_group_counts["percentage"] = (
    age_group_counts["count"]
    / len(questionnaire_df)
    * 100
).round(2)

age_group_counts.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "03_age_groups.csv"
    ),
    index=False
)


# ============================================================
# 3. GENDER ANALYSIS
# ============================================================

print("Analyzing gender...")

gender_counts = (
    questionnaire_df["gender"]
    .value_counts(dropna=False)
    .reset_index()
)

gender_counts.columns = [
    "gender",
    "count"
]

gender_counts["percentage"] = (
    gender_counts["count"]
    / len(questionnaire_df)
    * 100
).round(2)

gender_counts.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "04_gender_distribution.csv"
    ),
    index=False
)


# ============================================================
# 4. LOCATION ANALYSIS
# ============================================================

print("Analyzing location...")

location_counts = (
    questionnaire_df["qa_location"]
    .value_counts(dropna=False)
    .reset_index()
)

location_counts.columns = [
    "location",
    "count"
]

location_counts["percentage"] = (
    location_counts["count"]
    / len(questionnaire_df)
    * 100
).round(2)

location_counts.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "05_location_distribution.csv"
    ),
    index=False
)


# ============================================================
# 5. SMOKING ANALYSIS
# ============================================================

print("Analyzing smoking preferences...")

smoking_counts = (
    questionnaire_df["qa_smoking"]
    .value_counts(dropna=False)
    .reset_index()
)

smoking_counts.columns = [
    "smoking_status",
    "count"
]

smoking_counts["percentage"] = (
    smoking_counts["count"]
    / len(questionnaire_df)
    * 100
).round(2)

smoking_counts.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "06_smoking_distribution.csv"
    ),
    index=False
)


# Partner smoking preferences

partner_smoking_counts = (
    questionnaire_df["qa_partner_smoking"]
    .value_counts(dropna=False)
    .reset_index()
)

partner_smoking_counts.columns = [
    "partner_smoking_preference",
    "count"
]

partner_smoking_counts["percentage"] = (
    partner_smoking_counts["count"]
    / len(questionnaire_df)
    * 100
).round(2)

partner_smoking_counts.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "07_partner_smoking_preferences.csv"
    ),
    index=False
)


# ============================================================
# 6. CHILDREN ANALYSIS
# ============================================================

print("Analyzing children preferences...")

has_children_counts = (
    questionnaire_df["qa_has_children"]
    .value_counts(dropna=False)
    .reset_index()
)

has_children_counts.columns = [
    "has_children",
    "count"
]

has_children_counts["percentage"] = (
    has_children_counts["count"]
    / len(questionnaire_df)
    * 100
).round(2)

has_children_counts.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "08_existing_children.csv"
    ),
    index=False
)


partner_children_counts = (
    questionnaire_df["qa_partner_children"]
    .value_counts(dropna=False)
    .reset_index()
)

partner_children_counts.columns = [
    "partner_children_preference",
    "count"
]

partner_children_counts["percentage"] = (
    partner_children_counts["count"]
    / len(questionnaire_df)
    * 100
).round(2)

partner_children_counts.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "09_partner_children_preferences.csv"
    ),
    index=False
)


wants_children_counts = (
    questionnaire_df["qa_wants_children"]
    .value_counts(dropna=False)
    .reset_index()
)

wants_children_counts.columns = [
    "wants_children",
    "count"
]

wants_children_counts["percentage"] = (
    wants_children_counts["count"]
    / len(questionnaire_df)
    * 100
).round(2)

wants_children_counts.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "10_wants_children.csv"
    ),
    index=False
)


# ============================================================
# 7. RELATIONSHIP GOAL
# ============================================================

print("Analyzing relationship goals...")

relationship_counts = (
    questionnaire_df["qa_relationship_goal"]
    .value_counts(dropna=False)
    .reset_index()
)

relationship_counts.columns = [
    "relationship_goal",
    "count"
]

relationship_counts["percentage"] = (
    relationship_counts["count"]
    / len(questionnaire_df)
    * 100
).round(2)

relationship_counts.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "11_relationship_goals.csv"
    ),
    index=False
)


# ============================================================
# 8. RELATIONSHIP PACE
# ============================================================

pace_counts = (
    questionnaire_df["qa_relationship_pace"]
    .value_counts(dropna=False)
    .reset_index()
)

pace_counts.columns = [
    "relationship_pace",
    "count"
]

pace_counts["percentage"] = (
    pace_counts["count"]
    / len(questionnaire_df)
    * 100
).round(2)

pace_counts.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "12_relationship_pace.csv"
    ),
    index=False
)


# ============================================================
# 9. SCHEDULE ANALYSIS
# ============================================================

print("Analyzing schedule availability...")

schedule_counts = (
    questionnaire_df["qa_schedule"]
    .value_counts(dropna=False)
    .reset_index()
)

schedule_counts.columns = [
    "schedule",
    "count"
]

schedule_counts["percentage"] = (
    schedule_counts["count"]
    / len(questionnaire_df)
    * 100
).round(2)

schedule_counts.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "13_schedule_distribution.csv"
    ),
    index=False
)


# ============================================================
# 10. MISSING DATA ANALYSIS
# ============================================================

print("Analyzing missing data...")

missing_counts = (
    questionnaire_df.isna()
    .sum()
    .reset_index()
)

missing_counts.columns = [
    "column",
    "missing_count"
]

missing_counts["missing_percentage"] = (
    missing_counts["missing_count"]
    / len(questionnaire_df)
    * 100
).round(2)

missing_counts = missing_counts.sort_values(
    "missing_percentage",
    ascending=False
)

missing_counts.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "14_missing_data.csv"
    ),
    index=False
)


# ============================================================
# 11. PAIR-LEVEL MATCH STATUS
# ============================================================

print("Analyzing pair compatibility...")

match_status_counts = (
    pair_df["match_status"]
    .value_counts(dropna=False)
    .reset_index()
)

match_status_counts.columns = [
    "match_status",
    "count"
]

match_status_counts["percentage"] = (
    match_status_counts["count"]
    / len(pair_df)
    * 100
).round(2)

match_status_counts.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "15_match_status.csv"
    ),
    index=False
)


# ============================================================
# 12. HARD CONSTRAINT ANALYSIS
# ============================================================

hard_counts = (
    pair_df["hard_compatible"]
    .value_counts(dropna=False)
    .reset_index()
)

hard_counts.columns = [
    "hard_compatible",
    "count"
]

hard_counts["percentage"] = (
    hard_counts["count"]
    / len(pair_df)
    * 100
).round(2)

hard_counts.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "16_hard_compatibility.csv"
    ),
    index=False
)


# ============================================================
# 13. TIME COMPATIBILITY
# ============================================================

time_counts = (
    pair_df["time_compatible"]
    .value_counts(dropna=False)
    .reset_index()
)

time_counts.columns = [
    "time_compatible",
    "count"
]

time_counts["percentage"] = (
    time_counts["count"]
    / len(pair_df)
    * 100
).round(2)

time_counts.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "17_time_compatibility.csv"
    ),
    index=False
)


# ============================================================
# 14. CANDIDATE COUNT ANALYSIS
# ============================================================

print("Analyzing candidate availability...")

candidate_summary = candidate_df[
    "candidate_count"
].describe()

candidate_summary_df = (
    candidate_summary
    .reset_index()
)

candidate_summary_df.columns = [
    "statistic",
    "value"
]

candidate_summary_df.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "18_candidate_count_summary.csv"
    ),
    index=False
)


# Candidate count distribution

candidate_distribution = (
    candidate_df["candidate_count"]
    .value_counts()
    .sort_index()
    .reset_index()
)

candidate_distribution.columns = [
    "candidate_count",
    "members"
]

candidate_distribution.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "19_candidate_count_distribution.csv"
    ),
    index=False
)


# ============================================================
# 15. N CALCULATION
# ============================================================

total_members = len(candidate_df)

N = int(
    (
        candidate_df["candidate_count"] > 0
    ).sum()
)

zero_candidate = int(
    (
        candidate_df["candidate_count"] == 0
    ).sum()
)

N_percentage = round(
    N / total_members * 100,
    2
)

N_summary = pd.DataFrame({
    "metric": [
        "Total members",
        "N: members with at least one feasible candidate",
        "Members with zero feasible candidates",
        "N percentage"
    ],

    "value": [
        total_members,
        N,
        zero_candidate,
        N_percentage
    ]
})

N_summary.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "20_N_summary.csv"
    ),
    index=False
)


# ============================================================
# 16. DATASET-WISE N
# ============================================================

dataset_N = (
    candidate_df
    .groupby("source_dataset")
    .agg(
        total_members=(
            "member_id",
            "count"
        ),
        members_with_candidate=(
            "has_candidate",
            "sum"
        ),
        average_candidate_count=(
            "candidate_count",
            "mean"
        )
    )
    .reset_index()
)

dataset_N["members_without_candidate"] = (
    dataset_N["total_members"]
    - dataset_N["members_with_candidate"]
)

dataset_N["candidate_percentage"] = (
    dataset_N["members_with_candidate"]
    / dataset_N["total_members"]
    * 100
).round(2)

dataset_N["average_candidate_count"] = (
    dataset_N["average_candidate_count"]
    .round(2)
)

dataset_N.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "21_dataset_wise_N.csv"
    ),
    index=False
)


# ============================================================
# 17. DESCRIPTIVE CROSS-TABS
# ============================================================

print("Creating important cross-tabulations...")


# Smoking vs partner smoking

smoking_crosstab = pd.crosstab(
    questionnaire_df["qa_smoking"],
    questionnaire_df["qa_partner_smoking"],
    dropna=False
)

smoking_crosstab.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "22_smoking_cross_tab.csv"
    )
)


# Children vs partner children

children_crosstab = pd.crosstab(
    questionnaire_df["qa_has_children"],
    questionnaire_df["qa_partner_children"],
    dropna=False
)

children_crosstab.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "23_children_cross_tab.csv"
    )
)


# Children vs wants children

children_wants_crosstab = pd.crosstab(
    questionnaire_df["qa_has_children"],
    questionnaire_df["qa_wants_children"],
    dropna=False
)

children_wants_crosstab.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "24_children_wants_cross_tab.csv"
    )
)


# ============================================================
# 18. CONSOLE REPORT
# ============================================================

print()
print("=" * 70)
print("DESCRIPTIVE ANALYSIS COMPLETE")
print("=" * 70)

print()

print("DATASET:")
print(
    f"Total members: {total_members}"
)

print(
    f"Total pairs: {len(pair_df)}"
)

print()

print("N:")
print(
    f"Members with at least one candidate: {N}"
)

print(
    f"Members without candidate: {zero_candidate}"
)

print(
    f"N percentage: {N_percentage}%"
)

print()

print("AGE:")
print(
    f"Mean age: "
    f"{questionnaire_df['age'].mean():.2f}"
)

print(
    f"Median age: "
    f"{questionnaire_df['age'].median():.2f}"
)

print(
    f"Minimum age: "
    f"{questionnaire_df['age'].min()}"
)

print(
    f"Maximum age: "
    f"{questionnaire_df['age'].max()}"
)

print()

print("MATCH STATUS:")
print(
    pair_df["match_status"]
    .value_counts()
)

print()

print("OUTPUT DIRECTORY:")
print(OUTPUT_DIR)

print()

print("Generated analysis files:")
print("01_basic_summary.csv")
print("02_age_summary.csv")
print("03_age_groups.csv")
print("04_gender_distribution.csv")
print("05_location_distribution.csv")
print("06_smoking_distribution.csv")
print("07_partner_smoking_preferences.csv")
print("08_existing_children.csv")
print("09_partner_children_preferences.csv")
print("10_wants_children.csv")
print("11_relationship_goals.csv")
print("12_relationship_pace.csv")
print("13_schedule_distribution.csv")
print("14_missing_data.csv")
print("15_match_status.csv")
print("16_hard_compatibility.csv")
print("17_time_compatibility.csv")
print("18_candidate_count_summary.csv")
print("19_candidate_count_distribution.csv")
print("20_N_summary.csv")
print("21_dataset_wise_N.csv")
print("22_smoking_cross_tab.csv")
print("23_children_cross_tab.csv")
print("24_children_wants_cross_tab.csv")

print()
print("=" * 70)