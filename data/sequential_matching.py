# ============================================================
# SEQUENTIAL MATCHING PROBLEM
# Sequential Matching Algorithm
# ============================================================

import os
import pandas as pd
import numpy as np


# ============================================================
# 1. PATH CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ANALYSIS_DIR = os.path.join(
    BASE_DIR,
    "analysis_output"
)

EPISODE_DIR = os.path.join(
    ANALYSIS_DIR,
    "episode_results"
)

OUTPUT_DIR = os.path.join(
    ANALYSIS_DIR,
    "sequential_results"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)


QUESTIONNAIRE_FILE = os.path.join(
    ANALYSIS_DIR,
    "all_questionnaires.csv"
)

INTRODUCTION_FILE = os.path.join(
    EPISODE_DIR,
    "introduction_episode_analysis.csv"
)


# ============================================================
# 2. HELPER FUNCTIONS
# ============================================================

def clean_text(value):
    """
    Standardize text values.
    Missing values become None.
    """

    if pd.isna(value):
        return None

    value = str(value).strip().lower()

    if value in [
        "",
        "nan",
        "none",
        "null"
    ]:
        return None

    return value


def safe_number(value, default=0.0):
    """
    Safely convert a value to number.
    """

    try:

        if pd.isna(value):
            return default

        return float(value)

    except Exception:

        return default


def normalize_schedule(value):
    """
    Convert schedule information into a set.

    Example:
        weekday_evening, weekend_day
        ->
        {"weekday_evening", "weekend_day"}
    """

    if pd.isna(value):
        return set()

    text = str(value).lower().strip()

    if not text:
        return set()

    for separator in [
        "|",
        ";",
        "/"
    ]:
        text = text.replace(
            separator,
            ","
        )

    parts = []

    for item in text.split(","):

        item = item.strip()

        if item:
            parts.append(item)

    return set(parts)


# ============================================================
# 3. HARD CONSTRAINT: SMOKING
# ============================================================

def smoking_compatible(person_a, person_b):

    a_smoking = clean_text(
        person_a.get("qa_smoking")
    )

    b_smoking = clean_text(
        person_b.get("qa_smoking")
    )

    a_partner_preference = clean_text(
        person_a.get("qa_partner_smoking")
    )

    b_partner_preference = clean_text(
        person_b.get("qa_partner_smoking")
    )

    # Missing information = UNKNOWN
    if (
        a_smoking is None
        or b_smoking is None
        or a_partner_preference is None
        or b_partner_preference is None
    ):
        return None

    # A does not accept a smoking partner
    if (
        a_partner_preference == "not compatible for me"
        and b_smoking in [
            "yes",
            "occasionally"
        ]
    ):
        return False

    # B does not accept a smoking partner
    if (
        b_partner_preference == "not compatible for me"
        and a_smoking in [
            "yes",
            "occasionally"
        ]
    ):
        return False

    return True


# ============================================================
# 4. HARD CONSTRAINT: CHILDREN
# ============================================================

def children_compatible(person_a, person_b):

    a_children = clean_text(
        person_a.get("qa_has_children")
    )

    b_children = clean_text(
        person_b.get("qa_has_children")
    )

    a_partner_preference = clean_text(
        person_a.get("qa_partner_children")
    )

    b_partner_preference = clean_text(
        person_b.get("qa_partner_children")
    )

    # Missing information = UNKNOWN
    if (
        a_children is None
        or b_children is None
        or a_partner_preference is None
        or b_partner_preference is None
    ):
        return None

    # A prefers not to date someone with children
    if (
        a_partner_preference == "prefer not to"
        and b_children == "yes"
    ):
        return False

    # B prefers not to date someone with children
    if (
        b_partner_preference == "prefer not to"
        and a_children == "yes"
    ):
        return False

    return True


# ============================================================
# 5. HARD CONSTRAINT: GEOGRAPHY
# ============================================================

def geography_compatible(person_a, person_b):

    a_zone = clean_text(
        person_a.get("qa_location")
    )

    b_zone = clean_text(
        person_b.get("qa_location")
    )

    if (
        a_zone is None
        or b_zone is None
    ):
        return None

    # Same geographical zone
    if a_zone == b_zone:
        return True

    # Try acceptable zones
    a_acceptable = clean_text(
        person_a.get("field_acceptable_zones")
    )

    b_acceptable = clean_text(
        person_b.get("field_acceptable_zones")
    )

    a_accepts_b = False
    b_accepts_a = False

    if a_acceptable:

        a_accepts_b = (
            b_zone in a_acceptable
        )

    if b_acceptable:

        b_accepts_a = (
            a_zone in b_acceptable
        )

    if (
        a_accepts_b
        or b_accepts_a
    ):
        return True

    return False


# ============================================================
# 6. HARD CONSTRAINT: TIME
# ============================================================

def schedule_compatible(person_a, person_b):

    a_schedule = normalize_schedule(
        person_a.get("qa_schedule")
    )

    b_schedule = normalize_schedule(
        person_b.get("qa_schedule")
    )

    if (
        not a_schedule
        or not b_schedule
    ):
        return None

    overlap = (
        a_schedule.intersection(
            b_schedule
        )
    )

    if len(overlap) > 0:
        return True

    return False


# ============================================================
# 7. SOFT FEATURE: RELATIONSHIP GOAL
# ============================================================

def relationship_goal_score(
    person_a,
    person_b
):

    a_goal = clean_text(
        person_a.get(
            "qa_relationship_goal"
        )
    )

    b_goal = clean_text(
        person_b.get(
            "qa_relationship_goal"
        )
    )

    if (
        a_goal is None
        or b_goal is None
    ):
        return 0.5

    if a_goal == b_goal:
        return 1.0

    return 0.0


# ============================================================
# 8. SOFT FEATURE: LOCATION
# ============================================================

def location_score(
    person_a,
    person_b
):

    a_zone = clean_text(
        person_a.get(
            "qa_location"
        )
    )

    b_zone = clean_text(
        person_b.get(
            "qa_location"
        )
    )

    if (
        a_zone is None
        or b_zone is None
    ):
        return 0.5

    if a_zone == b_zone:
        return 1.0

    return 0.0


# ============================================================
# 9. SOFT FEATURE: TIME OVERLAP
# ============================================================

def schedule_score(
    person_a,
    person_b
):

    a_schedule = normalize_schedule(
        person_a.get(
            "qa_schedule"
        )
    )

    b_schedule = normalize_schedule(
        person_b.get(
            "qa_schedule"
        )
    )

    if (
        not a_schedule
        or not b_schedule
    ):
        return 0.5

    overlap = len(
        a_schedule.intersection(
            b_schedule
        )
    )

    if overlap == 0:
        return 0.0

    return min(
        overlap
        / max(
            len(a_schedule),
            len(b_schedule)
        ),
        1.0
    )


# ============================================================
# 10. SOFT FEATURE: CHILDREN FUTURE PREFERENCE
# ============================================================

def children_goal_score(
    person_a,
    person_b
):

    a_wants = clean_text(
        person_a.get(
            "qa_wants_children"
        )
    )

    b_wants = clean_text(
        person_b.get(
            "qa_wants_children"
        )
    )

    if (
        a_wants is None
        or b_wants is None
    ):
        return 0.5

    if a_wants == b_wants:
        return 1.0

    if (
        a_wants == "unsure"
        or b_wants == "unsure"
    ):
        return 0.5

    return 0.0


# ============================================================
# 11. EVALUATE ONE PAIR
# ============================================================

def evaluate_pair(
    person_a,
    person_b
):

    smoking = smoking_compatible(
        person_a,
        person_b
    )

    children = children_compatible(
        person_a,
        person_b
    )

    geography = geography_compatible(
        person_a,
        person_b
    )

    schedule = schedule_compatible(
        person_a,
        person_b
    )

    hard_constraints = [
        smoking,
        children,
        geography,
        schedule
    ]

    # --------------------------------------------------------
    # HARD FAILURE
    # --------------------------------------------------------

    if any(
        value is False
        for value in hard_constraints
    ):

        return {
            "hard_status": "INCOMPATIBLE",
            "feasible": 0,
            "smoking_compatible": smoking,
            "children_compatible": children,
            "geography_compatible": geography,
            "schedule_compatible": schedule,
            "relationship_goal_score": np.nan,
            "location_score": np.nan,
            "schedule_score": np.nan,
            "children_goal_score": np.nan,
            "soft_score": np.nan
        }

    # --------------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------------

    if any(
        value is None
        for value in hard_constraints
    ):

        return {
            "hard_status": "UNKNOWN",
            "feasible": 0,
            "smoking_compatible": smoking,
            "children_compatible": children,
            "geography_compatible": geography,
            "schedule_compatible": schedule,
            "relationship_goal_score": np.nan,
            "location_score": np.nan,
            "schedule_score": np.nan,
            "children_goal_score": np.nan,
            "soft_score": np.nan
        }

    # --------------------------------------------------------
    # SOFT FEATURES
    # --------------------------------------------------------

    goal = relationship_goal_score(
        person_a,
        person_b
    )

    location = location_score(
        person_a,
        person_b
    )

    schedule = schedule_score(
        person_a,
        person_b
    )

    children_goal = children_goal_score(
        person_a,
        person_b
    )

    # --------------------------------------------------------
    # FINAL SOFT SCORE
    # --------------------------------------------------------

    soft_score = (
        0.40 * goal
        + 0.25 * location
        + 0.20 * schedule
        + 0.15 * children_goal
    )

    return {
        "hard_status": "FEASIBLE",
        "feasible": 1,
        "smoking_compatible": smoking,
        "children_compatible": children,
        "geography_compatible": geography,
        "schedule_compatible": True,
        "relationship_goal_score": goal,
        "location_score": location,
        "schedule_score": schedule,
        "children_goal_score": children_goal,
        "soft_score": soft_score
    }


# ============================================================
# 12. LOAD QUESTIONNAIRE DATA
# ============================================================

print("=" * 70)
print("SEQUENTIAL MATCHING ANALYSIS")
print("=" * 70)

print("\nLoading questionnaire data...")

if not os.path.exists(
    QUESTIONNAIRE_FILE
):

    raise FileNotFoundError(
        f"Questionnaire file not found:\n"
        f"{QUESTIONNAIRE_FILE}"
    )

questionnaires = pd.read_csv(
    QUESTIONNAIRE_FILE
)

print(
    f"Questionnaire records: "
    f"{len(questionnaires)}"
)


# ============================================================
# 13. LOAD INTRODUCTION DATA
# ============================================================

if os.path.exists(
    INTRODUCTION_FILE
):

    introductions = pd.read_csv(
        INTRODUCTION_FILE
    )

    print(
        f"Introduction records: "
        f"{len(introductions)}"
    )

else:

    introductions = pd.DataFrame()

    print(
        "Introduction analysis file not found."
    )


# ============================================================
# 14. STANDARDIZE MEMBER IDs
# ============================================================

questionnaires[
    "member_id"
] = questionnaires[
    "member_id"
].astype(str)

questionnaires[
    "source_dataset"
] = questionnaires[
    "source_dataset"
].astype(str)


questionnaires[
    "member_key"
] = (
    questionnaires[
        "source_dataset"
    ]
    + "_"
    + questionnaires[
        "member_id"
    ]
)


# ============================================================
# 15. INITIAL MEMBER STATUS
# ============================================================

questionnaires[
    "status"
] = pd.Series(
    ["AVAILABLE"]
    * len(questionnaires),
    index=questionnaires.index,
    dtype="object"
)


# IMPORTANT:
# matched_with must be object/string because it will contain
# member IDs and also missing values.

questionnaires[
    "matched_with"
] = pd.Series(
    [None]
    * len(questionnaires),
    index=questionnaires.index,
    dtype="object"
)


questionnaires[
    "waiting_since"
] = pd.Series(
    [None]
    * len(questionnaires),
    index=questionnaires.index,
    dtype="object"
)


questionnaires[
    "response_day"
] = np.nan


questionnaires[
    "response_time"
] = np.nan


questionnaires[
    "candidate_count"
] = 0


questionnaires[
    "has_candidate"
] = 0


# ============================================================
# 16. CREATE EPISODES
# ============================================================

if not introductions.empty:

    if "assigned_day" in introductions.columns:

        introductions[
            "assigned_day"
        ] = pd.to_numeric(
            introductions[
                "assigned_day"
            ],
            errors="coerce"
        )

        introductions[
            "episode_id"
        ] = (
            introductions[
                "source_dataset"
            ]
            .astype(str)
            + "_day_"
            + introductions[
                "assigned_day"
            ]
            .fillna(-1)
            .astype(int)
            .astype(str)
        )

    else:

        introductions[
            "episode_id"
        ] = (
            introductions[
                "source_dataset"
            ].astype(str)
            + "_episode_1"
        )

else:

    introductions = pd.DataFrame(
        columns=[
            "episode_id",
            "source_dataset",
            "assigned_day"
        ]
    )


# ============================================================
# 17. BUILD EPISODE LIST
# ============================================================

episode_records = []


if not introductions.empty:

    for dataset in sorted(
        questionnaires[
            "source_dataset"
        ].unique()
    ):

        dataset_intro = introductions[
            introductions[
                "source_dataset"
            ] == dataset
        ].copy()

        if dataset_intro.empty:
            continue

        days = sorted(
            dataset_intro[
                "assigned_day"
            ]
            .dropna()
            .unique()
        )

        for day in days:

            episode_records.append(
                {
                    "source_dataset": dataset,
                    "day": int(day),
                    "episode_id":
                        f"{dataset}_day_{int(day)}"
                }
            )

else:

    for dataset in sorted(
        questionnaires[
            "source_dataset"
        ].unique()
    ):

        episode_records.append(
            {
                "source_dataset": dataset,
                "day": 0,
                "episode_id":
                    f"{dataset}_day_0"
            }
        )


episodes = pd.DataFrame(
    episode_records
)

print(
    f"Episodes found: "
    f"{len(episodes)}"
)


# ============================================================
# 18. OUTPUT STORAGE
# ============================================================

status_history = []

match_results = []

episode_candidate_results = []


# ============================================================
# 19. PROCESS EPISODES SEQUENTIALLY
# ============================================================

for _, episode in episodes.iterrows():

    dataset = episode[
        "source_dataset"
    ]

    day = episode[
        "day"
    ]

    episode_id = episode[
        "episode_id"
    ]

    print()
    print(
        f"Processing {episode_id}"
    )

    # --------------------------------------------------------
    # Get users belonging to this dataset
    # --------------------------------------------------------

    members = questionnaires[
        questionnaires[
            "source_dataset"
        ] == dataset
    ].copy()

    # --------------------------------------------------------
    # Only AVAILABLE users
    # --------------------------------------------------------

    available_members = members[
        members[
            "status"
        ] == "AVAILABLE"
    ].copy()

    print(
        f"Available members: "
        f"{len(available_members)}"
    )

    # --------------------------------------------------------
    # Generate candidate pairs
    # --------------------------------------------------------

    candidate_rows = []

    available_count = len(
        available_members
    )

    for i in range(
        available_count
    ):

        person_a = (
            available_members.iloc[i]
        )

        for j in range(
            i + 1,
            available_count
        ):

            person_b = (
                available_members.iloc[j]
            )

            result = evaluate_pair(
                person_a,
                person_b
            )

            if result[
                "feasible"
            ] == 1:

                candidate_rows.append(
                    {
                        "episode_id":
                            episode_id,

                        "source_dataset":
                            dataset,

                        "day":
                            day,

                        "user_a":
                            person_a[
                                "member_key"
                            ],

                        "user_b":
                            person_b[
                                "member_key"
                            ],

                        **result
                    }
                )

    candidate_df = pd.DataFrame(
        candidate_rows
    )

    # --------------------------------------------------------
    # Candidate counts
    # --------------------------------------------------------

    candidate_count = {}

    for key in (
        available_members[
            "member_key"
        ]
    ):

        candidate_count[
            key
        ] = 0

    if not candidate_df.empty:

        for _, row in (
            candidate_df.iterrows()
        ):

            candidate_count[
                row["user_a"]
            ] += 1

            candidate_count[
                row["user_b"]
            ] += 1

    # --------------------------------------------------------
    # N
    # --------------------------------------------------------

    N = sum(
        1
        for count
        in candidate_count.values()
        if count > 0
    )

    no_candidate = (
        len(available_members)
        - N
    )

    print(
        f"N = {N} | "
        f"No candidate = "
        f"{no_candidate}"
    )

    episode_candidate_results.append(
        {
            "episode_id":
                episode_id,

            "source_dataset":
                dataset,

            "day":
                day,

            "eligible_users":
                len(available_members),

            "N_users_with_candidate":
                N,

            "users_without_candidate":
                no_candidate,

            "candidate_pairs":
                len(candidate_df)
        }
    )

    # --------------------------------------------------------
    # Save candidate counts to member table
    # --------------------------------------------------------

    for key, count in (
        candidate_count.items()
    ):

        mask = (
            questionnaires[
                "member_key"
            ] == key
        )

        questionnaires.loc[
            mask,
            "candidate_count"
        ] = int(count)

        questionnaires.loc[
            mask,
            "has_candidate"
        ] = int(
            count > 0
        )

    # --------------------------------------------------------
    # Record users without candidates
    # --------------------------------------------------------

    for key, count in (
        candidate_count.items()
    ):

        if count == 0:

            status_history.append(
                {
                    "episode_id":
                        episode_id,

                    "source_dataset":
                        dataset,

                    "day":
                        day,

                    "member_key":
                        key,

                    "status":
                        "UNMATCHED",

                    "matched_with":
                        None,

                    "candidate_count":
                        0
                }
            )

    # --------------------------------------------------------
    # No feasible pair
    # --------------------------------------------------------

    if candidate_df.empty:

        continue

    # --------------------------------------------------------
    # Rank candidate pairs
    # --------------------------------------------------------

    candidate_df = (
        candidate_df
        .sort_values(
            by="soft_score",
            ascending=False
        )
        .reset_index(
            drop=True
        )
    )

    used_members = set()

    # --------------------------------------------------------
    # SELECT MATCHES
    # --------------------------------------------------------

    for _, pair in (
        candidate_df.iterrows()
    ):

        user_a = pair[
            "user_a"
        ]

        user_b = pair[
            "user_b"
        ]

        # A member can only be matched once
        if user_a in used_members:
            continue

        if user_b in used_members:
            continue

        # ----------------------------------------------------
        # Exploration vs Exploitation
        # ----------------------------------------------------

        score = safe_number(
            pair[
                "soft_score"
            ]
        )

        if score >= 0.75:

            strategy = (
                "EXPLOITATION"
            )

        else:

            strategy = (
                "EXPLORATION"
            )

        # ----------------------------------------------------
        # Match ID
        # ----------------------------------------------------

        match_id = (
            f"{episode_id}_"
            f"match_"
            f"{len(match_results) + 1}"
        )

        # ----------------------------------------------------
        # Record match
        # ----------------------------------------------------

        match_results.append(
            {
                "match_id":
                    match_id,

                "episode_id":
                    episode_id,

                "source_dataset":
                    dataset,

                "day":
                    day,

                "user_a":
                    user_a,

                "user_b":
                    user_b,

                "strategy":
                    strategy,

                "soft_score":
                    score,

                "smoking_compatible":
                    pair[
                        "smoking_compatible"
                    ],

                "children_compatible":
                    pair[
                        "children_compatible"
                    ],

                "geography_compatible":
                    pair[
                        "geography_compatible"
                    ],

                "schedule_compatible":
                    pair[
                        "schedule_compatible"
                    ],

                "relationship_goal_score":
                    pair[
                        "relationship_goal_score"
                    ],

                "location_score":
                    pair[
                        "location_score"
                    ],

                "schedule_score":
                    pair[
                        "schedule_score"
                    ],

                "children_goal_score":
                    pair[
                        "children_goal_score"
                    ]
            }
        )

        # ----------------------------------------------------
        # Mark both users as MATCHED
        # ----------------------------------------------------

        mask_a = (
            questionnaires[
                "member_key"
            ] == user_a
        )

        mask_b = (
            questionnaires[
                "member_key"
            ] == user_b
        )

        questionnaires.loc[
            mask_a,
            "status"
        ] = "MATCHED"

        questionnaires.loc[
            mask_b,
            "status"
        ] = "MATCHED"

        questionnaires.loc[
            mask_a,
            "matched_with"
        ] = str(user_b)

        questionnaires.loc[
            mask_b,
            "matched_with"
        ] = str(user_a)

        # ----------------------------------------------------
        # Prevent them from being selected again
        # ----------------------------------------------------

        used_members.add(
            user_a
        )

        used_members.add(
            user_b
        )

        # ----------------------------------------------------
        # Status history
        # ----------------------------------------------------

        status_history.append(
            {
                "episode_id":
                    episode_id,

                "source_dataset":
                    dataset,

                "day":
                    day,

                "member_key":
                    user_a,

                "status":
                    "MATCHED",

                "matched_with":
                    str(user_b),

                "candidate_count":
                    candidate_count.get(
                        user_a,
                        0
                    )
            }
        )

        status_history.append(
            {
                "episode_id":
                    episode_id,

                "source_dataset":
                    dataset,

                "day":
                    day,

                "member_key":
                    user_b,

                "status":
                    "MATCHED",

                "matched_with":
                    str(user_a),

                "candidate_count":
                    candidate_count.get(
                        user_b,
                        0
                    )
            }
        )


# ============================================================
# 20. CREATE DATAFRAMES
# ============================================================

matches_df = pd.DataFrame(
    match_results
)

episode_candidate_df = pd.DataFrame(
    episode_candidate_results
)

status_history_df = pd.DataFrame(
    status_history
)


# ============================================================
# 21. SAVE MATCH RESULTS
# ============================================================

matches_file = os.path.join(
    OUTPUT_DIR,
    "sequential_matching_results.csv"
)

matches_df.to_csv(
    matches_file,
    index=False
)


# ============================================================
# 22. SAVE EPISODE CANDIDATE RESULTS
# ============================================================

episode_candidate_file = os.path.join(
    OUTPUT_DIR,
    "episode_candidate_counts.csv"
)

episode_candidate_df.to_csv(
    episode_candidate_file,
    index=False
)


# ============================================================
# 23. SAVE MEMBER STATUS HISTORY
# ============================================================

status_file = os.path.join(
    OUTPUT_DIR,
    "member_status_history.csv"
)

status_history_df.to_csv(
    status_file,
    index=False
)


# ============================================================
# 24. FINAL MEMBER SUMMARY
# ============================================================

summary_columns = [
    "member_key",
    "member_id",
    "source_dataset",
    "age",
    "gender",
    "qa_location",
    "status",
    "matched_with",
    "candidate_count",
    "has_candidate"
]

available_columns = [
    column
    for column in summary_columns
    if column in questionnaires.columns
]

member_summary = questionnaires[
    available_columns
].copy()


member_summary_file = os.path.join(
    OUTPUT_DIR,
    "final_member_summary.csv"
)

member_summary.to_csv(
    member_summary_file,
    index=False
)


# ============================================================
# 25. FINAL STATISTICS
# ============================================================

total_members = len(
    questionnaires
)

total_episodes = len(
    episodes
)

total_matches = len(
    matches_df
)

if not matches_df.empty:

    matched_users = len(
        set(
            matches_df[
                "user_a"
            ].tolist()
            +
            matches_df[
                "user_b"
            ].tolist()
        )
    )

else:

    matched_users = 0


unmatched_users = len(
    questionnaires[
        questionnaires[
            "status"
        ] == "UNMATCHED"
    ]
)


remaining_available = len(
    questionnaires[
        questionnaires[
            "status"
        ] == "AVAILABLE"
    ]
)


if not matches_df.empty:

    exploitation_count = int(
        (
            matches_df[
                "strategy"
            ]
            == "EXPLOITATION"
        ).sum()
    )

    exploration_count = int(
        (
            matches_df[
                "strategy"
            ]
            == "EXPLORATION"
        ).sum()
    )

else:

    exploitation_count = 0

    exploration_count = 0


if not episode_candidate_df.empty:

    total_candidate_pairs = int(
        episode_candidate_df[
            "candidate_pairs"
        ].sum()
    )

    total_N = int(
        episode_candidate_df[
            "N_users_with_candidate"
        ].sum()
    )

else:

    total_candidate_pairs = 0

    total_N = 0


# ============================================================
# 26. SUMMARY FILE
# ============================================================

summary = pd.DataFrame(
    [
        {
            "total_members":
                total_members,

            "total_episodes":
                total_episodes,

            "total_matches":
                total_matches,

            "matched_users":
                matched_users,

            "unmatched_users":
                unmatched_users,

            "remaining_available_users":
                remaining_available,

            "exploitation_matches":
                exploitation_count,

            "exploration_matches":
                exploration_count,

            "total_candidate_pairs":
                total_candidate_pairs,

            "sum_of_episode_N":
                total_N
        }
    ]
)


summary_file = os.path.join(
    OUTPUT_DIR,
    "sequential_summary.csv"
)

summary.to_csv(
    summary_file,
    index=False
)


# ============================================================
# 27. PRINT FINAL REPORT
# ============================================================

print()
print("=" * 70)
print("SEQUENTIAL MATCHING COMPLETE")
print("=" * 70)

print(
    f"Total members              : "
    f"{total_members}"
)

print(
    f"Total episodes             : "
    f"{total_episodes}"
)

print(
    f"Total matches              : "
    f"{total_matches}"
)

print(
    f"Matched users              : "
    f"{matched_users}"
)

print(
    f"Unmatched users            : "
    f"{unmatched_users}"
)

print(
    f"Remaining available users  : "
    f"{remaining_available}"
)

print(
    f"Exploitation matches       : "
    f"{exploitation_count}"
)

print(
    f"Exploration matches        : "
    f"{exploration_count}"
)

print(
    f"Total candidate pairs      : "
    f"{total_candidate_pairs}"
)

print(
    f"Sum of episode N           : "
    f"{total_N}"
)

print()
print("Files created:")
print(
    f"1. {matches_file}"
)
print(
    f"2. {episode_candidate_file}"
)
print(
    f"3. {status_file}"
)
print(
    f"4. {member_summary_file}"
)
print(
    f"5. {summary_file}"
)

print()
print("Sequential matching analysis finished successfully.")