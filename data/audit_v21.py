from pathlib import Path
import json
from collections import Counter

DATA_ROOT = Path(r"C:\Users\monus\OneDrive\Desktop\data")

DATASETS = [
    f"public_{i:02d}"
    for i in range(1, 11)
]


def load_jsonl(path):

    rows = []

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


def get_field(member, field):

    return member.get(
        "fields",
        {}
    ).get(field)


def observed(member, field, day):

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


def value(member, field, day):

    if not observed(
        member,
        field,
        day
    ):
        return None

    return get_field(
        member,
        field
    )


def check_unknowns(a, b, day):

    reasons = []

    # Smoking
    if (
        value(a, "partner_smoking", day)
        is None
        or
        value(b, "smoking", day)
        is None
    ):
        reasons.append(
            "smoking"
        )

    if (
        value(b, "partner_smoking", day)
        is None
        or
        value(a, "smoking", day)
        is None
    ):
        reasons.append(
            "smoking_reciprocal"
        )

    # Children
    if (
        value(a, "partner_children", day)
        is None
        or
        value(b, "has_children", day)
        is None
    ):
        reasons.append(
            "children"
        )

    if (
        value(b, "partner_children", day)
        is None
        or
        value(a, "has_children", day)
        is None
    ):
        reasons.append(
            "children_reciprocal"
        )

    # Wants children
    if (
        value(a, "wants_children", day)
        is None
        or
        value(b, "wants_children", day)
        is None
    ):
        reasons.append(
            "wants_children"
        )

    # Geography
    if (
        value(a, "acceptable_zones", day)
        is None
        or
        value(b, "acceptable_zones", day)
        is None
    ):
        reasons.append(
            "geography"
        )

    # Schedule
    if (
        value(a, "schedule", day)
        is None
        or
        value(b, "schedule", day)
        is None
    ):
        reasons.append(
            "schedule"
        )

    # Age
    if (
        value(a, "age_min", day)
        is None
        or
        value(a, "age_max", day)
        is None
        or
        value(b, "age_min", day)
        is None
        or
        value(b, "age_max", day)
        is None
    ):
        reasons.append(
            "age"
        )

    # Gender
    if (
        value(a, "who_to_meet", day)
        is None
        or
        value(b, "who_to_meet", day)
        is None
    ):
        reasons.append(
            "gender_preference"
        )

    return reasons


def main():

    print()
    print("=" * 70)
    print("V2.1 UNKNOWN-REASON AUDIT")
    print("=" * 70)

    total_pairs = 0

    reason_counter = Counter()

    dataset_counter = Counter()

    for dataset in DATASETS:

        members = load_jsonl(
            DATA_ROOT
            / dataset
            / "members.jsonl"
        )

        if not members:
            continue

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

        days = sorted(days)

        dataset_unknown_pairs = 0

        for day in days:

            available = [
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

            for i in range(
                len(available)
            ):

                a = available[i]

                for j in range(
                    i + 1,
                    len(available)
                ):

                    b = available[j]

                    reasons = check_unknowns(
                        a,
                        b,
                        day
                    )

                    if reasons:

                        total_pairs += 1

                        dataset_unknown_pairs += 1

                        for reason in set(
                            reasons
                        ):

                            reason_counter[
                                reason
                            ] += 1

                        dataset_counter[
                            dataset
                        ] += 1

        print(
            f"{dataset}: "
            f"{dataset_unknown_pairs:,} "
            f"pairs with missing information"
        )

    print()
    print("=" * 70)
    print("UNKNOWN REASON FREQUENCY")
    print("=" * 70)

    for reason, count in (
        reason_counter
        .most_common()
    ):

        percentage = (
            count
            / total_pairs
            * 100
            if total_pairs
            else 0
        )

        print(
            f"{reason:<25}"
            f"{count:>10,}"
            f"   {percentage:>6.2f}%"
        )

    print()
    print("=" * 70)
    print("DATASET UNKNOWN PAIRS")
    print("=" * 70)

    for dataset, count in (
        dataset_counter
        .most_common()
    ):

        print(
            f"{dataset:<15}"
            f"{count:>10,}"
        )

    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()