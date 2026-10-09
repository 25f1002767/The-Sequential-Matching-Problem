import os
import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "analysis_output",
    "episode_results"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_read_csv(path):
    """Read CSV safely."""
    if not os.path.exists(path):
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except Exception as error:
        print(f"Could not read {path}")
        print(error)
        return pd.DataFrame()


def clean_text(value):
    """Standardize text without converting missing data into a value."""

    if pd.isna(value):
        return np.nan

    value = str(value).strip().lower()

    if value in ["", "nan", "none", "null"]:
        return np.nan

    return value


def first_valid(series):
    """Return first non-missing value."""

    values = series.dropna()

    if len(values) == 0:
        return np.nan

    return values.iloc[0]


# ============================================================
# TITLE
# ============================================================

print("=" * 70)
print("EPISODE / CYCLE / WAITING STATUS ANALYSIS")
print("=" * 70)


# ============================================================
# DATASET DISCOVERY
# ============================================================

dataset_folders = []

for item in os.listdir(BASE_DIR):

    full_path = os.path.join(BASE_DIR, item)

    if (
        os.path.isdir(full_path)
        and item.startswith("public_")
    ):
        dataset_folders.append(item)


dataset_folders = sorted(dataset_folders)


print()
print(
    f"Datasets found: {len(dataset_folders)}"
)


# ============================================================
# STORAGE
# ============================================================

all_introductions = []
all_feedback = []
all_members = []


# ============================================================
# LOAD ALL DATASETS
# ============================================================

print()

for dataset_name in dataset_folders:

    dataset_path = os.path.join(
        BASE_DIR,
        dataset_name
    )

    print(
        f"Loading {dataset_name}..."
    )

    # --------------------------------------------------------
    # INTRODUCTIONS
    # --------------------------------------------------------

    introductions_path = os.path.join(
        dataset_path,
        "introductions.csv"
    )

    introductions = safe_read_csv(
        introductions_path
    )

    if not introductions.empty:

        introductions["source_dataset"] = (
            dataset_name
        )

        all_introductions.append(
            introductions
        )

    # --------------------------------------------------------
    # FEEDBACK
    # --------------------------------------------------------

    feedback_path = os.path.join(
        dataset_path,
        "feedback.csv"
    )

    feedback = safe_read_csv(
        feedback_path
    )

    if not feedback.empty:

        feedback["source_dataset"] = (
            dataset_name
        )

        all_feedback.append(
            feedback
        )

    # --------------------------------------------------------
    # MEMBERS
    # --------------------------------------------------------

    members_path = os.path.join(
        dataset_path,
        "members.csv"
    )

    members = safe_read_csv(
        members_path
    )

    if not members.empty:

        members["source_dataset"] = (
            dataset_name
        )

        all_members.append(
            members
        )


# ============================================================
# COMBINE DATA
# ============================================================

if all_introductions:

    introductions_df = pd.concat(
        all_introductions,
        ignore_index=True
    )

else:

    introductions_df = pd.DataFrame()


if all_feedback:

    feedback_df = pd.concat(
        all_feedback,
        ignore_index=True
    )

else:

    feedback_df = pd.DataFrame()


if all_members:

    members_df = pd.concat(
        all_members,
        ignore_index=True
    )

else:

    members_df = pd.DataFrame()


print()
print(
    f"Total introductions: "
    f"{len(introductions_df)}"
)

print(
    f"Total feedback records: "
    f"{len(feedback_df)}"
)

print(
    f"Total members: "
    f"{len(members_df)}"
)


# ============================================================
# CHECK INTRODUCTIONS
# ============================================================

if introductions_df.empty:

    print()
    print(
        "ERROR: No introduction data found."
    )

    raise SystemExit(1)


# ============================================================
# STANDARDIZE INTRODUCTION COLUMNS
# ============================================================

for column in introductions_df.columns:

    if introductions_df[column].dtype == "object":

        introductions_df[column] = (
            introductions_df[column]
            .apply(clean_text)
        )


# ============================================================
# STANDARDIZE FEEDBACK
# ============================================================

for column in feedback_df.columns:

    if feedback_df[column].dtype == "object":

        feedback_df[column] = (
            feedback_df[column]
            .apply(clean_text)
        )


# ============================================================
# EPISODE DEFINITION
# ============================================================

print()
print("Building episode / cycle representation...")


# ------------------------------------------------------------
# IMPORTANT DEFINITION
# ------------------------------------------------------------
#
# One introduction represents one matchmaking interaction.
#
# An episode/cycle is represented by the day on which the
# introduction was assigned, within a dataset.
#
# Therefore:
#
# source_dataset + assigned_day = episode
#
# This prevents information from different datasets being
# mixed together.
# ------------------------------------------------------------


if "assigned_day" in introductions_df.columns:

    introductions_df["episode_id"] = (
        introductions_df[
            "source_dataset"
        ].astype(str)
        + "_day_"
        + introductions_df[
            "assigned_day"
        ].astype(str)
    )

else:

    # Fallback if assigned_day does not exist
    introductions_df["episode_id"] = (
        introductions_df[
            "source_dataset"
        ].astype(str)
        + "_episode_"
        + introductions_df.index.astype(str)
    )


# ============================================================
# INTRODUCTION STATUS
# ============================================================

print(
    "Determining introduction response status..."
)


# ------------------------------------------------------------
# CREATE FEEDBACK LOOKUP
# ------------------------------------------------------------

feedback_by_intro = {}

if (
    not feedback_df.empty
    and "introduction_id" in feedback_df.columns
):

    for introduction_id, group in feedback_df.groupby(
        "introduction_id"
    ):

        feedback_by_intro[
            introduction_id
        ] = group.copy()


# ============================================================
# RESPONSE CLASSIFICATION
# ============================================================

def classify_feedback(group):
    """
    Convert feedback events into a high-level status.

    This is deliberately conservative.

    Missing feedback does NOT automatically mean rejection.
    """

    if group is None or group.empty:

        return "WAITING"

    events = []

    if "event" in group.columns:

        events = [
            clean_text(x)
            for x in group["event"].tolist()
        ]

    values = []

    if "value" in group.columns:

        values = [
            clean_text(x)
            for x in group["value"].tolist()
        ]

    combined = events + values

    combined = [
        x for x in combined
        if not pd.isna(x)
    ]

    text = " ".join(combined)

    # Positive / accepted type signals
    positive_words = [
        "accept",
        "accepted",
        "yes",
        "interested",
        "interest",
        "like",
        "liked",
        "match"
    ]

    # Negative / rejected type signals
    negative_words = [
        "reject",
        "rejected",
        "decline",
        "declined",
        "no",
        "not interested",
        "dislike"
    ]

    if any(word in text for word in positive_words):

        return "RESPONDED_POSITIVE"

    if any(word in text for word in negative_words):

        return "RESPONDED_NEGATIVE"

    # A feedback record exists but cannot be confidently
    # classified.
    return "RESPONDED_OTHER"


# ============================================================
# BUILD INTRODUCTION-LEVEL ANALYSIS
# ============================================================

episode_records = []


for index, row in introductions_df.iterrows():

    introduction_id = row.get(
        "introduction_id",
        f"intro_{index}"
    )

    source_dataset = row.get(
        "source_dataset"
    )

    user_a = row.get(
        "user_a"
    )

    user_b = row.get(
        "user_b"
    )

    assigned_day = row.get(
        "assigned_day"
    )

    response_deadline = row.get(
        "response_deadline_day"
    )

    logging_policy = row.get(
        "logging_policy"
    )

    propensity = row.get(
        "propensity"
    )

    # --------------------------------------------------------
    # FEEDBACK
    # --------------------------------------------------------

    feedback_group = feedback_by_intro.get(
        introduction_id
    )

    response_status = classify_feedback(
        feedback_group
    )

    # --------------------------------------------------------
    # RESPONSE DAY
    # --------------------------------------------------------

    response_day = np.nan

    if (
        feedback_group is not None
        and not feedback_group.empty
    ):

        if "occurred_day" in feedback_group.columns:

            valid_days = (
                feedback_group[
                    "occurred_day"
                ]
                .dropna()
            )

            if len(valid_days) > 0:

                response_day = valid_days.iloc[0]

        if pd.isna(response_day):

            if "observed_day" in feedback_group.columns:

                valid_days = (
                    feedback_group[
                        "observed_day"
                    ]
                    .dropna()
                )

                if len(valid_days) > 0:

                    response_day = valid_days.iloc[0]

    # --------------------------------------------------------
    # RESPONSE TIME
    # --------------------------------------------------------

    response_time = np.nan

    try:

        if (
            not pd.isna(assigned_day)
            and not pd.isna(response_day)
        ):

            response_time = (
                float(response_day)
                - float(assigned_day)
            )

            if response_time < 0:

                response_time = np.nan

    except Exception:

        response_time = np.nan

    # --------------------------------------------------------
    # WAITING FLAG
    # --------------------------------------------------------

    if response_status == "WAITING":

        waiting_flag = 1

    else:

        waiting_flag = 0

    # --------------------------------------------------------
    # RESOLVED FLAG
    # --------------------------------------------------------

    if response_status == "WAITING":

        resolved_flag = 0

    else:

        resolved_flag = 1

    # --------------------------------------------------------
    # EXPIRY
    # --------------------------------------------------------

    expired_flag = 0

    if response_status == "WAITING":

        try:

            if (
                not pd.isna(response_deadline)
                and not pd.isna(assigned_day)
            ):

                # If the current recorded data has moved beyond
                # the response deadline, mark as expired.
                if (
                    float(response_deadline)
                    < float(assigned_day)
                ):

                    expired_flag = 1

        except Exception:

            expired_flag = 0

    # --------------------------------------------------------
    # STORE
    # --------------------------------------------------------

    episode_records.append({

        "source_dataset": source_dataset,

        "episode_id": row.get(
            "episode_id"
        ),

        "introduction_id": introduction_id,

        "assigned_day": assigned_day,

        "response_deadline_day": response_deadline,

        "response_day": response_day,

        "response_time_days": response_time,

        "user_a": user_a,

        "user_b": user_b,

        "logging_policy": logging_policy,

        "propensity": propensity,

        "response_status": response_status,

        "waiting_flag": waiting_flag,

        "resolved_flag": resolved_flag,

        "expired_flag": expired_flag
    })


episode_df = pd.DataFrame(
    episode_records
)


# ============================================================
# SAVE INTRODUCTION-LEVEL DATA
# ============================================================

episode_file = os.path.join(
    OUTPUT_DIR,
    "introduction_episode_analysis.csv"
)

episode_df.to_csv(
    episode_file,
    index=False
)


# ============================================================
# EPISODE SUMMARY
# ============================================================

print(
    "Creating episode summaries..."
)


episode_summary = (
    episode_df
    .groupby(
        [
            "source_dataset",
            "episode_id"
        ],
        dropna=False
    )
    .agg(
        introductions=(
            "introduction_id",
            "count"
        ),

        waiting_introductions=(
            "waiting_flag",
            "sum"
        ),

        resolved_introductions=(
            "resolved_flag",
            "sum"
        ),

        positive_responses=(
            "response_status",
            lambda x: (
                x == "RESPONDED_POSITIVE"
            ).sum()
        ),

        negative_responses=(
            "response_status",
            lambda x: (
                x == "RESPONDED_NEGATIVE"
            ).sum()
        ),

        other_responses=(
            "response_status",
            lambda x: (
                x == "RESPONDED_OTHER"
            ).sum()
        ),

        average_response_time=(
            "response_time_days",
            "mean"
        )
    )
    .reset_index()
)


episode_summary[
    "resolution_rate"
] = (
    episode_summary[
        "resolved_introductions"
    ]
    / episode_summary[
        "introductions"
    ]
    * 100
).round(2)


episode_summary[
    "waiting_rate"
] = (
    episode_summary[
        "waiting_introductions"
    ]
    / episode_summary[
        "introductions"
    ]
    * 100
).round(2)


episode_summary.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "episode_summary.csv"
    ),
    index=False
)


# ============================================================
# WAITING STATUS ANALYSIS
# ============================================================

print(
    "Analyzing waiting status..."
)


waiting_summary = pd.DataFrame({

    "metric": [
        "Total introductions",
        "Waiting introductions",
        "Resolved introductions",
        "Waiting percentage",
        "Resolved percentage"
    ],

    "value": [

        len(episode_df),

        int(
            episode_df[
                "waiting_flag"
            ].sum()
        ),

        int(
            episode_df[
                "resolved_flag"
            ].sum()
        ),

        round(
            episode_df[
                "waiting_flag"
            ].mean()
            * 100,
            2
        ),

        round(
            episode_df[
                "resolved_flag"
            ].mean()
            * 100,
            2
        )
    ]
})


waiting_summary.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "waiting_status_summary.csv"
    ),
    index=False
)


# ============================================================
# RESPONSE STATUS DISTRIBUTION
# ============================================================

response_status_summary = (
    episode_df[
        "response_status"
    ]
    .value_counts(dropna=False)
    .reset_index()
)


response_status_summary.columns = [
    "response_status",
    "count"
]


response_status_summary[
    "percentage"
] = (
    response_status_summary[
        "count"
    ]
    / len(episode_df)
    * 100
).round(2)


response_status_summary.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "response_status_distribution.csv"
    ),
    index=False
)


# ============================================================
# RESPONSE TIME ANALYSIS
# ============================================================

print(
    "Analyzing response time..."
)


response_times = episode_df[
    "response_time_days"
].dropna()


if len(response_times) > 0:

    response_time_summary = (
        response_times
        .describe()
        .reset_index()
    )

    response_time_summary.columns = [
        "statistic",
        "value"
    ]

else:

    response_time_summary = pd.DataFrame({
        "statistic": [
            "count"
        ],
        "value": [
            0
        ]
    })


response_time_summary.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "response_time_summary.csv"
    ),
    index=False
)


# ============================================================
# MEMBER WAITING STATUS
# ============================================================

print(
    "Creating member-level waiting status..."
)


member_status_records = []


# Process users appearing in introductions

for dataset_name, group in episode_df.groupby(
    "source_dataset"
):

    users = set()

    if "user_a" in group.columns:

        users.update(
            group["user_a"]
            .dropna()
            .tolist()
        )

    if "user_b" in group.columns:

        users.update(
            group["user_b"]
            .dropna()
            .tolist()
        )

    for member_id in users:

        user_rows_a = group[
            group["user_a"] == member_id
        ]

        user_rows_b = group[
            group["user_b"] == member_id
        ]

        user_rows = pd.concat(
            [
                user_rows_a,
                user_rows_b
            ],
            ignore_index=True
        )

        total_introductions = len(
            user_rows
        )

        waiting_count = int(
            user_rows[
                "waiting_flag"
            ].sum()
        )

        resolved_count = int(
            user_rows[
                "resolved_flag"
            ].sum()
        )

        # A member is currently treated as waiting if
        # they have at least one unresolved introduction.
        currently_waiting = int(
            waiting_count > 0
        )

        member_status_records.append({

            "source_dataset": dataset_name,

            "member_id": member_id,

            "total_introductions": (
                total_introductions
            ),

            "waiting_introductions": (
                waiting_count
            ),

            "resolved_introductions": (
                resolved_count
            ),

            "currently_waiting": (
                currently_waiting
            )
        })


member_status_df = pd.DataFrame(
    member_status_records
)


member_status_df.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "member_waiting_status.csv"
    ),
    index=False
)


# ============================================================
# INTRODUCTIONS PER MEMBER
# ============================================================

introduction_counts = (
    member_status_df[
        "total_introductions"
    ]
    .value_counts()
    .sort_index()
    .reset_index()
)


introduction_counts.columns = [
    "number_of_introductions",
    "members"
]


introduction_counts.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "introductions_per_member.csv"
    ),
    index=False
)


# ============================================================
# DATASET-WISE SUMMARY
# ============================================================

dataset_summary = (
    episode_df
    .groupby(
        "source_dataset"
    )
    .agg(

        introductions=(
            "introduction_id",
            "count"
        ),

        waiting=(
            "waiting_flag",
            "sum"
        ),

        resolved=(
            "resolved_flag",
            "sum"
        ),

        positive=(
            "response_status",
            lambda x: (
                x == "RESPONDED_POSITIVE"
            ).sum()
        ),

        negative=(
            "response_status",
            lambda x: (
                x == "RESPONDED_NEGATIVE"
            ).sum()
        ),

        average_response_time=(
            "response_time_days",
            "mean"
        )
    )
    .reset_index()
)


dataset_summary[
    "waiting_percentage"
] = (
    dataset_summary[
        "waiting"
    ]
    / dataset_summary[
        "introductions"
    ]
    * 100
).round(2)


dataset_summary[
    "resolution_percentage"
] = (
    dataset_summary[
        "resolved"
    ]
    / dataset_summary[
        "introductions"
    ]
    * 100
).round(2)


dataset_summary.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "dataset_wise_episode_summary.csv"
    ),
    index=False
)


# ============================================================
# EPISODE DEFINITION DOCUMENT
# ============================================================

definition_df = pd.DataFrame({

    "concept": [
        "Episode",
        "Cycle",
        "Introduction",
        "Waiting",
        "Resolved",
        "Response Time",
        "Candidate",
        "N"
    ],

    "definition": [

        "A matchmaking decision period represented by source dataset and assigned day.",

        "One complete matchmaking cycle in which currently eligible people are considered for introductions and their resulting status is recorded.",

        "A proposed connection between user A and user B.",

        "An introduction whose response has not yet been observed. The member should not automatically be treated as available for another match.",

        "An introduction for which a response or outcome has been observed.",

        "Number of days between introduction assignment and the first recorded response.",

        "A feasible person-to-person match satisfying the current matching constraints.",

        "Number of members for whom at least one feasible candidate is available."
    ]
})


definition_df.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "episode_definitions.csv"
    ),
    index=False
)


# ============================================================
# FINAL REPORT
# ============================================================

print()
print("=" * 70)
print("EPISODE ANALYSIS COMPLETE")
print("=" * 70)

print()

print(
    f"Total introductions: "
    f"{len(episode_df)}"
)

print(
    f"Waiting introductions: "
    f"{int(episode_df['waiting_flag'].sum())}"
)

print(
    f"Resolved introductions: "
    f"{int(episode_df['resolved_flag'].sum())}"
)

print()

print("Response status:")

print(
    episode_df[
        "response_status"
    ].value_counts()
)

print()

print("Average response time:")

if len(response_times) > 0:

    print(
        f"{response_times.mean():.2f} days"
    )

else:

    print(
        "No valid response-time records available."
    )

print()

print("Episode count:")

print(
    episode_df[
        "episode_id"
    ].nunique()
)

print()

print("Output directory:")

print(
    OUTPUT_DIR
)

print()

print("Generated files:")

print(
    "1. introduction_episode_analysis.csv"
)

print(
    "2. episode_summary.csv"
)

print(
    "3. waiting_status_summary.csv"
)

print(
    "4. response_status_distribution.csv"
)

print(
    "5. response_time_summary.csv"
)

print(
    "6. member_waiting_status.csv"
)

print(
    "7. introductions_per_member.csv"
)

print(
    "8. dataset_wise_episode_summary.csv"
)

print(
    "9. episode_definitions.csv"
)

print()

print("=" * 70)