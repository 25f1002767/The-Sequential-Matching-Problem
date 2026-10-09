import pandas as pd
from pathlib import Path

# =========================================================
# SETTINGS
# =========================================================

INPUT_FILE = Path("analysis_output/all_questionnaires.csv")
OUTPUT_DIR = Path("analysis_output")

OUTPUT_DIR.mkdir(exist_ok=True)

df = pd.read_csv(INPUT_FILE)

print("=" * 60)
print("DETAILED DESCRIPTIVE ANALYSIS")
print("=" * 60)

print("\nTotal participants:", len(df))


# =========================================================
# 1. DATA QUALITY
# =========================================================

print("\n" + "=" * 60)
print("1. DATA QUALITY")
print("=" * 60)

print("\nDuplicate rows:")
print(df.duplicated().sum())

print("\nDuplicate member IDs:")
print(df["member_id"].duplicated().sum())

print("\nMissing values:")

missing = pd.DataFrame({
    "column": df.columns,
    "missing_count": df.isna().sum(),
    "missing_percentage":
        (df.isna().sum() / len(df) * 100).round(2)
})

missing = missing.sort_values(
    "missing_percentage",
    ascending=False
)

print(missing.to_string(index=False))

missing.to_csv(
    OUTPUT_DIR / "detailed_missing_report.csv",
    index=False
)


# =========================================================
# 2. AGE ANALYSIS
# =========================================================

print("\n" + "=" * 60)
print("2. AGE ANALYSIS")
print("=" * 60)

print(df["age"].describe())

age_bins = [20, 25, 30, 35, 40, 45, 50]
age_labels = [
    "21-25",
    "26-30",
    "31-35",
    "36-40",
    "41-45",
    "46-50"
]

df["age_group"] = pd.cut(
    df["age"],
    bins=age_bins,
    labels=age_labels,
    include_lowest=True
)

age_distribution = (
    df["age_group"]
    .value_counts()
    .sort_index()
    .reset_index()
)

age_distribution.columns = [
    "age_group",
    "count"
]

print("\nAge groups:")
print(age_distribution)

age_distribution.to_csv(
    OUTPUT_DIR / "age_group_distribution.csv",
    index=False
)


# =========================================================
# 3. GENDER
# =========================================================

print("\n" + "=" * 60)
print("3. GENDER")
print("=" * 60)

gender = (
    df["gender"]
    .value_counts(dropna=False)
    .reset_index()
)

gender.columns = [
    "gender",
    "count"
]

print(gender)

gender.to_csv(
    OUTPUT_DIR / "gender_distribution.csv",
    index=False
)


# =========================================================
# 4. SMOKING
# =========================================================

print("\n" + "=" * 60)
print("4. SMOKING")
print("=" * 60)

smoking_columns = [
    "qa_smoking",
    "qa_partner_smoking"
]

for column in smoking_columns:

    if column in df.columns:

        print("\n", column)

        result = (
            df[column]
            .value_counts(dropna=False)
            .reset_index()
        )

        result.columns = [
            column,
            "count"
        ]

        print(result)

        result.to_csv(
            OUTPUT_DIR / f"{column}_analysis.csv",
            index=False
        )


# =========================================================
# 5. CHILDREN
# =========================================================

print("\n" + "=" * 60)
print("5. CHILDREN PREFERENCES")
print("=" * 60)

children_columns = [
    "qa_has_children",
    "qa_partner_children",
    "qa_wants_children"
]

for column in children_columns:

    if column in df.columns:

        print("\n", column)

        result = (
            df[column]
            .value_counts(dropna=False)
            .reset_index()
        )

        result.columns = [
            column,
            "count"
        ]

        print(result)

        result.to_csv(
            OUTPUT_DIR / f"{column}_analysis.csv",
            index=False
        )


# =========================================================
# 6. SCHEDULE
# =========================================================

print("\n" + "=" * 60)
print("6. SCHEDULE / TIME AVAILABILITY")
print("=" * 60)

if "qa_schedule" in df.columns:

    schedule = (
        df["qa_schedule"]
        .value_counts(dropna=False)
        .reset_index()
    )

    schedule.columns = [
        "schedule",
        "count"
    ]

    print(schedule)

    schedule.to_csv(
        OUTPUT_DIR / "schedule_analysis.csv",
        index=False
    )


# =========================================================
# 7. LOCATION
# =========================================================

print("\n" + "=" * 60)
print("7. LOCATION")
print("=" * 60)

if "qa_location" in df.columns:

    location = (
        df["qa_location"]
        .value_counts(dropna=False)
        .reset_index()
    )

    location.columns = [
        "location",
        "count"
    ]

    print(location)

    location.to_csv(
        OUTPUT_DIR / "location_analysis.csv",
        index=False
    )


# =========================================================
# 8. RELATIONSHIP GOAL
# =========================================================

print("\n" + "=" * 60)
print("8. RELATIONSHIP GOAL")
print("=" * 60)

if "qa_relationship_goal" in df.columns:

    goal = (
        df["qa_relationship_goal"]
        .value_counts(dropna=False)
        .reset_index()
    )

    goal.columns = [
        "relationship_goal",
        "count"
    ]

    print(goal)

    goal.to_csv(
        OUTPUT_DIR / "relationship_goal_analysis.csv",
        index=False
    )


# =========================================================
# 9. CROSS ANALYSIS
# =========================================================

print("\n" + "=" * 60)
print("9. CROSS ANALYSIS")
print("=" * 60)


# Smoking vs partner smoking

if (
    "qa_smoking" in df.columns
    and
    "qa_partner_smoking" in df.columns
):

    smoking_cross = pd.crosstab(
        df["qa_smoking"],
        df["qa_partner_smoking"],
        dropna=False
    )

    print("\nSmoking vs Partner Smoking:")
    print(smoking_cross)

    smoking_cross.to_csv(
        OUTPUT_DIR / "smoking_partner_smoking_cross.csv"
    )


# Children vs partner children

if (
    "qa_has_children" in df.columns
    and
    "qa_partner_children" in df.columns
):

    children_cross = pd.crosstab(
        df["qa_has_children"],
        df["qa_partner_children"],
        dropna=False
    )

    print("\nHas Children vs Partner Children:")
    print(children_cross)

    children_cross.to_csv(
        OUTPUT_DIR / "children_partner_children_cross.csv"
    )


# Children vs wants children

if (
    "qa_has_children" in df.columns
    and
    "qa_wants_children" in df.columns
):

    wants_children_cross = pd.crosstab(
        df["qa_has_children"],
        df["qa_wants_children"],
        dropna=False
    )

    print("\nHas Children vs Wants Children:")
    print(wants_children_cross)

    wants_children_cross.to_csv(
        OUTPUT_DIR / "children_wants_children_cross.csv"
    )


# =========================================================
# 10. DATASET-WISE ANALYSIS
# =========================================================

print("\n" + "=" * 60)
print("10. DATASET-WISE PARTICIPANT COUNT")
print("=" * 60)

dataset_counts = (
    df["source_dataset"]
    .value_counts()
    .sort_index()
    .reset_index()
)

dataset_counts.columns = [
    "dataset",
    "participants"
]

print(dataset_counts)

dataset_counts.to_csv(
    OUTPUT_DIR / "dataset_participant_counts.csv",
    index=False
)


# =========================================================
# FINAL
# =========================================================

print("\n" + "=" * 60)
print("DETAILED ANALYSIS COMPLETED")
print("=" * 60)

print("\nNo rows were removed.")

print("\nAnalysis files saved in:")
print(OUTPUT_DIR)