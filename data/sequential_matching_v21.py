from pathlib import Path
import json
import math
import pandas as pd
from collections import defaultdict

# ============================================================
# CONFIG
# ============================================================

DATA_ROOT = Path(r"C:\Users\monus\OneDrive\Desktop\data")

OUTPUT_ROOT = (
    DATA_ROOT
    / "analysis_output"
    / "sequential_v21"
)

DATASETS = [
    f"public_{i:02d}"
    for i in range(1, 11)
]

RESPONSE_DEADLINE = 7

# Soft preference weights
SOFT_WEIGHTS = {
    "relationship_goal": 0.35,
    "relationship_pace": 0.20,
    "lifestyle": 0.15,
    "conversations": 0.15,
    "emotional_availability": 0.05,
    "space_for_relationship": 0.10,
}

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
                continue

    return rows


def get_field(member, field):
    return member.get("fields", {}).get(field)


def is_observed(member, field, day):

    status = (
        member
        .get("field_status", {})
        .get(field)
    )

    observed_day = (
        member
        .get("field_observed_day", {})
        .get(field)
    )

    if status != "observed":
        return False

    if observed_day is None:
        return False

    try:
        return float(observed_day) <= float(day)
    except Exception:
        return False


def observed_value(member, field, day):

    if not is_observed(member, field, day):
        return None

    return get_field(member, field)


def normalize_string(value):

    if value is None:
        return None

    return str(value).strip().lower()


def normalize_list(value):

    if value is None:
        return None

    if isinstance(value, list):
        return [
            normalize_string(x)
            for x in value
            if x is not None
        ]

    return [normalize_string(value)]


def pair_key(a, b):

    ids = sorted([
        str(a["member_id"]),
        str(b["member_id"])
    ])

    return ids[0] + "||" + ids[1]


# ============================================================
# HARD CONSTRAINTS
# ============================================================

def smoking_check(a, b, day):

    a_preference = observed_value(
        a,
        "partner_smoking",
        day
    )

    b_smoking = observed_value(
        b,
        "smoking",
        day
    )

    if a_preference is None or b_smoking is None:
        return "UNKNOWN"

    a_preference = normalize_string(a_preference)
    b_smoking = normalize_string(b_smoking)

    if (
        a_preference == "no_smoking"
        and b_smoking in {
            "yes",
            "occasionally"
        }
    ):
        return "FAIL"

    return "PASS"


def children_check(a, b, day):

    a_preference = observed_value(
        a,
        "partner_children",
        day
    )

    b_children = observed_value(
        b,
        "has_children",
        day
    )

    if a_preference is None or b_children is None:
        return "UNKNOWN"

    a_preference = normalize_string(
        a_preference
    )

    if (
        a_preference == "no_children"
        and bool(b_children)
    ):
        return "FAIL"

    return "PASS"


def wants_children_check(a, b, day):

    a_wants = observed_value(
        a,
        "wants_children",
        day
    )

    b_wants = observed_value(
        b,
        "wants_children",
        day
    )

    if a_wants is None or b_wants is None:
        return "UNKNOWN"

    a_wants = normalize_string(a_wants)
    b_wants = normalize_string(b_wants)

    # Only clear yes/no conflict is hard.
    if (
        a_wants in {"yes", "no"}
        and
        b_wants in {"yes", "no"}
        and
        a_wants != b_wants
    ):
        return "FAIL"

    return "PASS"


# ============================================================
# GEOGRAPHY
# ============================================================

def geography_check(a, b, day):

    a_zones = observed_value(
        a,
        "acceptable_zones",
        day
    )

    b_zone = b.get("zone")

    if a_zones is None or b_zone is None:
        return "UNKNOWN"

    a_zones = normalize_list(a_zones)
    b_zone = normalize_string(b_zone)

    if b_zone not in a_zones:
        return "FAIL"

    return "PASS"


def reciprocal_geography_check(a, b, day):

    first = geography_check(
        a,
        b,
        day
    )

    second = geography_check(
        b,
        a,
        day
    )

    if "FAIL" in {first, second}:
        return "FAIL"

    if "UNKNOWN" in {first, second}:
        return "UNKNOWN"

    return "PASS"


# ============================================================
# TIME / SCHEDULE
# ============================================================

def schedule_check(a, b, day):

    a_schedule = observed_value(
        a,
        "schedule",
        day
    )

    b_schedule = observed_value(
        b,
        "schedule",
        day
    )

    if a_schedule is None or b_schedule is None:
        return "UNKNOWN"

    a_schedule = set(
        normalize_list(a_schedule)
    )

    b_schedule = set(
        normalize_list(b_schedule)
    )

    if len(
        a_schedule.intersection(b_schedule)
    ) == 0:
        return "FAIL"

    return "PASS"


# ============================================================
# GENDER PREFERENCE
# ============================================================

def gender_preference_check(a, b, day):

    preference = observed_value(
        a,
        "who_to_meet",
        day
    )

    b_gender = normalize_string(
        b.get("gender")
    )

    if preference is None:
        return "UNKNOWN"

    preference = normalize_list(
        preference
    )

    if b_gender not in preference:
        return "FAIL"

    return "PASS"


def reciprocal_gender_check(a, b, day):

    first = gender_preference_check(
        a,
        b,
        day
    )

    second = gender_preference_check(
        b,
        a,
        day
    )

    if "FAIL" in {first, second}:
        return "FAIL"

    if "UNKNOWN" in {first, second}:
        return "UNKNOWN"

    return "PASS"


# ============================================================
# AGE
# ============================================================

def age_check(a, b, day):

    minimum = observed_value(
        a,
        "age_min",
        day
    )

    maximum = observed_value(
        a,
        "age_max",
        day
    )

    b_age = b.get("age")

    if (
        minimum is None
        or maximum is None
        or b_age is None
    ):
        return "UNKNOWN"

    try:

        minimum = float(minimum)
        maximum = float(maximum)
        b_age = float(b_age)

    except Exception:

        return "UNKNOWN"

    if b_age < minimum or b_age > maximum:
        return "FAIL"

    return "PASS"


def reciprocal_age_check(a, b, day):

    first = age_check(
        a,
        b,
        day
    )

    second = age_check(
        b,
        a,
        day
    )

    if "FAIL" in {first, second}:
        return "FAIL"

    if "UNKNOWN" in {first, second}:
        return "UNKNOWN"

    return "PASS"


# ============================================================
# HARD + REGULATED ELIGIBILITY
# ============================================================

def evaluate_pair(a, b, day):

    checks = {}

    # Hard constraints
    checks["smoking"] = smoking_check(
        a,
        b,
        day
    )

    checks["smoking_reciprocal"] = smoking_check(
        b,
        a,
        day
    )

    checks["children"] = children_check(
        a,
        b,
        day
    )

    checks["children_reciprocal"] = children_check(
        b,
        a,
        day
    )

    # Children future preference
    checks["wants_children"] = wants_children_check(
        a,
        b,
        day
    )

    # Regulated constraints
    checks["geography"] = reciprocal_geography_check(
        a,
        b,
        day
    )

    checks["schedule"] = schedule_check(
        a,
        b,
        day
    )

    # Basic eligibility constraints
    checks["age"] = reciprocal_age_check(
        a,
        b,
        day
    )

    checks["gender"] = reciprocal_gender_check(
        a,
        b,
        day
    )

    # --------------------------------------------------------
    # HARD FAILURE
    # --------------------------------------------------------

    hard_checks = [
        checks["smoking"],
        checks["smoking_reciprocal"],
        checks["children"],
        checks["children_reciprocal"],
        checks["wants_children"],
    ]

    if "FAIL" in hard_checks:

        return {
            "status": "INFEASIBLE",
            "reason": "HARD_CONSTRAINT",
            "checks": checks
        }

    # --------------------------------------------------------
    # REGULATED FAILURE
    # --------------------------------------------------------

    regulated_checks = [
        checks["geography"],
        checks["schedule"],
        checks["age"],
        checks["gender"],
    ]

    if "FAIL" in regulated_checks:

        return {
            "status": "INFEASIBLE",
            "reason": "REGULATED_CONSTRAINT",
            "checks": checks
        }

    # --------------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------------

    all_checks = (
        hard_checks
        + regulated_checks
    )

    if "UNKNOWN" in all_checks:

        return {
            "status": "UNCERTAIN",
            "reason": "MISSING_INFORMATION",
            "checks": checks
        }

    return {
        "status": "FEASIBLE",
        "reason": "ALL_CONSTRAINTS_SATISFIED",
        "checks": checks
    }


# ============================================================
# SOFT SCORING
# ============================================================

def equality_score(a, b, field, day):

    a_value = observed_value(
        a,
        field,
        day
    )

    b_value = observed_value(
        b,
        field,
        day
    )

    if a_value is None or b_value is None:

        return None

    a_value = normalize_string(
        a_value
    )

    b_value = normalize_string(
        b_value
    )

    return 1.0 if a_value == b_value else 0.0


def soft_score(a, b, day):

    total = 0.0
    weight_total = 0.0

    details = {}

    for field, weight in SOFT_WEIGHTS.items():

        score = equality_score(
            a,
            b,
            field,
            day
        )

        details[field] = score

        if score is not None:

            total += score * weight
            weight_total += weight

    if weight_total == 0:

        return 0.0, details

    return (
        total / weight_total,
        details
    )


# ============================================================
# HISTORICAL INTRODUCTION STATUS
# ============================================================

def build_feedback_map(feedback):

    feedback_map = defaultdict(list)

    for row in feedback:

        intro_id = row.get(
            "introduction_id"
        )

        if intro_id is not None:

            feedback_map[
                str(intro_id)
            ].append(row)

    return feedback_map


def introduction_status(
    intro,
    feedback_map,
    current_day
):

    intro_id = str(
        intro.get("introduction_id")
    )

    events = feedback_map.get(
        intro_id,
        []
    )

    positive = 0
    negative = 0
    first_response_day = None

    for event in events:

        value = normalize_string(
            event.get("value")
        )

        event_name = normalize_string(
            event.get("event")
        )

        if (
            event_name
            == "introduction_response"
        ):

            if value in {
                "yes",
                "accept",
                "accepted",
                "interested"
            }:
                positive += 1

            elif value in {
                "no",
                "reject",
                "rejected",
                "decline",
                "declined"
            }:
                negative += 1

            response_day = (
                event.get("occurred_day")
                or event.get("observed_day")
            )

            if response_day is not None:

                try:

                    response_day = int(
                        response_day
                    )

                    if (
                        first_response_day
                        is None
                        or response_day
                        < first_response_day
                    ):
                        first_response_day = (
                            response_day
                        )

                except Exception:
                    pass

    assigned_day = intro.get(
        "assigned_day"
    )

    deadline = intro.get(
        "response_deadline_day"
    )

    try:
        assigned_day = int(
            assigned_day
        )
    except Exception:
        assigned_day = None

    try:
        deadline = int(
            deadline
        )
    except Exception:
        deadline = (
            assigned_day
            + RESPONSE_DEADLINE
            if assigned_day is not None
            else None
        )

    if positive >= 2:

        status = "MATCHED"

    elif negative > 0:

        status = "REJECTED"

    elif (
        deadline is not None
        and current_day > deadline
    ):

        status = "EXPIRED"

    else:

        status = "WAITING"

    response_time = None

    if (
        first_response_day is not None
        and assigned_day is not None
    ):

        response_time = (
            first_response_day
            - assigned_day
        )

        if response_time < 0:

            response_time = None

    return {
        "status": status,
        "response_time": response_time
    }


# ============================================================
# MEMBER STATUS
# ============================================================

def member_status(
    member_id,
    current_day,
    introductions,
    feedback_map
):

    relevant = []

    for intro in introductions:

        if (
            intro.get("user_a")
            == member_id
            or
            intro.get("user_b")
            == member_id
        ):

            try:

                assigned = int(
                    intro.get(
                        "assigned_day"
                    )
                )

            except Exception:

                continue

            if assigned <= current_day:

                relevant.append(intro)

    if not relevant:

        return "AVAILABLE"

    relevant.sort(
        key=lambda x: int(
            x.get(
                "assigned_day",
                0
            )
        ),
        reverse=True
    )

    for intro in relevant:

        result = introduction_status(
            intro,
            feedback_map,
            current_day
        )

        if result["status"] == "MATCHED":

            return "MATCHED"

        if result["status"] == "WAITING":

            return "WAITING"

    return "AVAILABLE"


# ============================================================
# DATASET ANALYSIS
# ============================================================

def analyze_dataset(dataset):

    print(
        f"[RUN] {dataset}"
    )

    dataset_root = (
        DATA_ROOT / dataset
    )

    members = load_jsonl(
        dataset_root
        / "members.jsonl"
    )

    introductions = load_jsonl(
        dataset_root
        / "introductions.jsonl"
    )

    feedback = load_jsonl(
        dataset_root
        / "feedback.jsonl"
    )

    feedback_map = build_feedback_map(
        feedback
    )

    if not members:

        return [], [], [], []

    # --------------------------------------------------------
    # DAYS
    # --------------------------------------------------------

    days = set()

    for member in members:

        arrived = member.get(
            "arrived_day"
        )

        if arrived is not None:

            try:
                days.add(
                    int(arrived)
                )
            except Exception:
                pass

    for intro in introductions:

        for field in [
            "assigned_day",
            "response_deadline_day"
        ]:

            value = intro.get(field)

            if value is not None:

                try:
                    days.add(
                        int(value)
                    )
                except Exception:
                    pass

    for event in feedback:

        for field in [
            "occurred_day",
            "observed_day"
        ]:

            value = event.get(field)

            if value is not None:

                try:
                    days.add(
                        int(value)
                    )
                except Exception:
                    pass

    days = sorted(days)

    episode_rows = []
    candidate_rows = []
    pair_rows = []
    match_rows = []

    # Prevent repeated matching across episodes
    matched_pairs = set()
    matched_members = set()

    # --------------------------------------------------------
    # EPISODES
    # --------------------------------------------------------

    for day in days:

        arrived_members = [
            m
            for m in members
            if (
                m.get("arrived_day")
                is not None
                and
                int(m["arrived_day"])
                <= day
            )
        ]

        available_members = []

        for member in arrived_members:

            status = member_status(
                member["member_id"],
                day,
                introductions,
                feedback_map
            )

            if status == "AVAILABLE":

                # Already matched in this simulation?
                if (
                    member["member_id"]
                    not in matched_members
                ):
                    available_members.append(
                        member
                    )

        feasible_count = defaultdict(int)
        uncertain_count = defaultdict(int)

        feasible_pairs = []

        pair_evaluated = 0

        # ----------------------------------------------------
        # PAIR EVALUATION
        # ----------------------------------------------------

        for i in range(
            len(available_members)
        ):

            a = available_members[i]

            for j in range(
                i + 1,
                len(available_members)
            ):

                b = available_members[j]

                result = evaluate_pair(
                    a,
                    b,
                    day
                )

                status = result["status"]

                if status == "FEASIBLE":

                    score, soft_details = (
                        soft_score(
                            a,
                            b,
                            day
                        )
                    )

                    feasible_count[
                        a["member_id"]
                    ] += 1

                    feasible_count[
                        b["member_id"]
                    ] += 1

                    feasible_pairs.append(
                        {
                            "user_a":
                                a["member_id"],

                            "user_b":
                                b["member_id"],

                            "score":
                                score,

                            "soft_details":
                                soft_details,

                            "day":
                                day,

                            "dataset":
                                dataset
                        }
                    )

                    pair_evaluated += 1

                elif status == "UNCERTAIN":

                    uncertain_count[
                        a["member_id"]
                    ] += 1

                    uncertain_count[
                        b["member_id"]
                    ] += 1

        # ----------------------------------------------------
        # N
        # ----------------------------------------------------

        N = sum(
            1
            for member in available_members
            if feasible_count[
                member["member_id"]
            ] > 0
        )

        uncertain_members = sum(
            1
            for member in available_members
            if (
                feasible_count[
                    member["member_id"]
                ] == 0
                and
                uncertain_count[
                    member["member_id"]
                ] > 0
            )
        )

        zero_candidate = sum(
            1
            for member in available_members
            if (
                feasible_count[
                    member["member_id"]
                ] == 0
                and
                uncertain_count[
                    member["member_id"]
                ] == 0
            )
        )

        # ----------------------------------------------------
        # CANDIDATE MEMBER ROWS
        # ----------------------------------------------------

        for member in available_members:

            member_id = member[
                "member_id"
            ]

            candidate_rows.append(
                {
                    "dataset":
                        dataset,

                    "day":
                        day,

                    "member_id":
                        member_id,

                    "candidate_count":
                        feasible_count[
                            member_id
                        ],

                    "uncertain_candidate_count":
                        uncertain_count[
                            member_id
                        ],

                    "has_candidate":
                        int(
                            feasible_count[
                                member_id
                            ] > 0
                        ),

                    "has_uncertain_candidate":
                        int(
                            uncertain_count[
                                member_id
                            ] > 0
                        ),

                    "status":
                        "AVAILABLE"
                }
            )

        # ----------------------------------------------------
        # GREEDY MATCHING
        # ----------------------------------------------------

        feasible_pairs.sort(
            key=lambda x:
                x["score"],
            reverse=True
        )

        used = set()

        selected_today = 0

        for pair in feasible_pairs:

            a_id = pair[
                "user_a"
            ]

            b_id = pair[
                "user_b"
            ]

            key = pair_key(
                {
                    "member_id": a_id
                },
                {
                    "member_id": b_id
                }
            )

            if key in matched_pairs:

                continue

            if (
                a_id in used
                or b_id in used
            ):

                continue

            # Match once
            matched_pairs.add(
                key
            )

            matched_members.add(
                a_id
            )

            matched_members.add(
                b_id
            )

            used.add(a_id)
            used.add(b_id)

            selected_today += 1

            match_rows.append(
                {
                    "dataset":
                        dataset,

                    "day":
                        day,

                    "user_a":
                        a_id,

                    "user_b":
                        b_id,

                    "pair_key":
                        key,

                    "soft_score":
                        pair["score"],

                    "match_type":
                        "BASELINE_EXPLOITATION"
                }
            )

        # ----------------------------------------------------
        # EPISODE SUMMARY
        # ----------------------------------------------------

        episode_rows.append(
            {
                "dataset":
                    dataset,

                "day":
                    day,

                "arrived_members":
                    len(arrived_members),

                "available_members":
                    len(available_members),

                "N_feasible":
                    N,

                "N_uncertain":
                    uncertain_members,

                "zero_candidate":
                    zero_candidate,

                "N_percentage":
                    (
                        N
                        / len(available_members)
                        * 100
                        if available_members
                        else 0
                    ),

                "uncertain_percentage":
                    (
                        uncertain_members
                        / len(available_members)
                        * 100
                        if available_members
                        else 0
                    ),

                "feasible_pair_evaluations":
                    pair_evaluated,

                "selected_matches":
                    selected_today
            }
        )

    # --------------------------------------------------------
    # INTRODUCTION LIFECYCLE
    # --------------------------------------------------------

    lifecycle_rows = []

    for intro in introductions:

        assigned_day = intro.get(
            "assigned_day"
        )

        try:
            assigned_day = int(
                assigned_day
            )
        except Exception:
            assigned_day = 0

        current_day = max(
            days
        ) if days else assigned_day

        result = introduction_status(
            intro,
            feedback_map,
            current_day
        )

        lifecycle_rows.append(
            {
                "dataset":
                    dataset,

                "introduction_id":
                    intro.get(
                        "introduction_id"
                    ),

                "assigned_day":
                    assigned_day,

                "response_deadline_day":
                    intro.get(
                        "response_deadline_day"
                    ),

                "user_a":
                    intro.get("user_a"),

                "user_b":
                    intro.get("user_b"),

                "status":
                    result["status"],

                "response_time_days":
                    result[
                        "response_time"
                    ]
            }
        )

    return (
        episode_rows,
        candidate_rows,
        lifecycle_rows,
        match_rows
    )


# ============================================================
# MAIN
# ============================================================

def main():

    OUTPUT_ROOT.mkdir(
        parents=True,
        exist_ok=True
    )

    all_episode_rows = []
    all_candidate_rows = []
    all_lifecycle_rows = []
    all_match_rows = []

    for dataset in DATASETS:

        (
            episode_rows,
            candidate_rows,
            lifecycle_rows,
            match_rows
        ) = analyze_dataset(
            dataset
        )

        all_episode_rows.extend(
            episode_rows
        )

        all_candidate_rows.extend(
            candidate_rows
        )

        all_lifecycle_rows.extend(
            lifecycle_rows
        )

        all_match_rows.extend(
            match_rows
        )

    # ========================================================
    # DATAFRAMES
    # ========================================================

    episode_df = pd.DataFrame(
        all_episode_rows
    )

    candidate_df = pd.DataFrame(
        all_candidate_rows
    )

    lifecycle_df = pd.DataFrame(
        all_lifecycle_rows
    )

    match_df = pd.DataFrame(
        all_match_rows
    )

    # ========================================================
    # DATASET N
    # ========================================================

    if not candidate_df.empty:

        dataset_N = (
            candidate_df
            .groupby("dataset")
            .agg(
                available_member_episodes=(
                    "member_id",
                    "count"
                ),

                N_feasible=(
                    "has_candidate",
                    "sum"
                ),

                N_uncertain=(
                    "has_uncertain_candidate",
                    "sum"
                ),

                mean_candidate_count=(
                    "candidate_count",
                    "mean"
                ),

                mean_uncertain_count=(
                    "uncertain_candidate_count",
                    "mean"
                )
            )
            .reset_index()
        )

        dataset_N[
            "N_percentage"
        ] = (
            dataset_N["N_feasible"]
            /
            dataset_N[
                "available_member_episodes"
            ]
            * 100
        )

    else:

        dataset_N = pd.DataFrame()

    # ========================================================
    # SUMMARY
    # ========================================================

    total_available = len(
        candidate_df
    )

    total_N = int(
        candidate_df[
            "has_candidate"
        ].sum()
    ) if not candidate_df.empty else 0

    total_uncertain = int(
        candidate_df[
            "has_uncertain_candidate"
        ].sum()
    ) if not candidate_df.empty else 0

    total_matches = len(
        match_df
    )

    unique_pairs = (
        match_df["pair_key"].nunique()
        if not match_df.empty
        else 0
    )

    summary = pd.DataFrame(
        [
            {
                "episodes":
                    len(episode_df),

                "available_member_episodes":
                    total_available,

                "N_feasible":
                    total_N,

                "N_uncertain":
                    total_uncertain,

                "N_percentage":
                    (
                        total_N
                        / total_available
                        * 100
                        if total_available
                        else 0
                    ),

                "baseline_match_events":
                    total_matches,

                "unique_baseline_pairs":
                    unique_pairs,

                "introduction_records":
                    len(lifecycle_df),

                "matched_introductions":
                    (
                        lifecycle_df[
                            "status"
                        ]
                        .eq("MATCHED")
                        .sum()
                        if not lifecycle_df.empty
                        else 0
                    ),

                "rejected_introductions":
                    (
                        lifecycle_df[
                            "status"
                        ]
                        .eq("REJECTED")
                        .sum()
                        if not lifecycle_df.empty
                        else 0
                    ),

                "waiting_introductions":
                    (
                        lifecycle_df[
                            "status"
                        ]
                        .eq("WAITING")
                        .sum()
                        if not lifecycle_df.empty
                        else 0
                    ),

                "expired_introductions":
                    (
                        lifecycle_df[
                            "status"
                        ]
                        .eq("EXPIRED")
                        .sum()
                        if not lifecycle_df.empty
                        else 0
                    )
            }
        ]
    )

    # ========================================================
    # SAVE
    # ========================================================

    episode_df.to_csv(
        OUTPUT_ROOT
        / "episode_summary_v21.csv",
        index=False
    )

    candidate_df.to_csv(
        OUTPUT_ROOT
        / "member_candidate_summary_v21.csv",
        index=False
    )

    lifecycle_df.to_csv(
        OUTPUT_ROOT
        / "introduction_lifecycle_v21.csv",
        index=False
    )

    match_df.to_csv(
        OUTPUT_ROOT
        / "baseline_matches_v21.csv",
        index=False
    )

    dataset_N.to_csv(
        OUTPUT_ROOT
        / "dataset_wise_N_v21.csv",
        index=False
    )

    summary.to_csv(
        OUTPUT_ROOT
        / "sequential_summary_v21.csv",
        index=False
    )

    # ========================================================
    # PRINT
    # ========================================================

    print("\n")
    print("=" * 70)
    print("SEQUENTIAL MATCHING V2.1 COMPLETE")
    print("=" * 70)

    print(
        f"Episodes: "
        f"{len(episode_df):,}"
    )

    print(
        f"Available member-episodes: "
        f"{total_available:,}"
    )

    print(
        f"N with feasible candidate: "
        f"{total_N:,}"
    )

    print(
        f"N with uncertain candidate: "
        f"{total_uncertain:,}"
    )

    print(
        f"N percentage: "
        f"{(
            total_N / total_available * 100
            if total_available
            else 0
        ):,.2f}%"
    )

    print(
        f"Baseline match events: "
        f"{total_matches:,}"
    )

    print(
        f"Unique baseline pairs: "
        f"{unique_pairs:,}"
    )

    print(
        f"Introductions: "
        f"{len(lifecycle_df):,}"
    )

    print(
        "\nOutput:"
    )

    print(
        OUTPUT_ROOT
    )

    print("=" * 70)


if __name__ == "__main__":
    main()