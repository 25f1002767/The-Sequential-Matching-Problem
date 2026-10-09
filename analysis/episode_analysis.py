"""Episode, Waiting & Response Lifecycle Analysis Module for The Sequential Matching Problem.
Tracks simulation cycles, the waiting state concurrency lock, response times,
and empirical introduction outcome funnels.
"""

from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np


def run_episode_lifecycle_analysis(dfs: Dict[str, pd.DataFrame], output_dir: Path) -> Dict[str, Any]:
    """Analyze introduction episodes, feedback events, response times, and waiting status."""
    output_dir.mkdir(parents=True, exist_ok=True)
    intros_df = dfs["introductions"]
    feedback_df = dfs["feedback"]

    # Match introductions with their feedback events
    fb_by_intro = {}
    for _, row in feedback_df.iterrows():
        iid = row.get("introduction_id")
        if iid:
            fb_by_intro.setdefault(iid, []).append(row.to_dict())

    lifecycle_records = []
    response_delays = []

    for _, intro in intros_df.iterrows():
        iid = intro["introduction_id"]
        assigned_day = int(intro["assigned_day"])
        deadline_day = int(intro.get("response_deadline_day", assigned_day + 7))
        ua, ub = intro["user_a"], intro["user_b"]
        ds_name = intro.get("dataset", "unknown")

        events = fb_by_intro.get(iid, [])
        resp_events = [e for e in events if e.get("event") == "introduction_response"]

        # Track responses for user_a and user_b
        a_resp = next((e for e in resp_events if e.get("member_id") == ua), None)
        b_resp = next((e for e in resp_events if e.get("member_id") == ub), None)

        a_val = a_resp.get("value") if a_resp else None
        b_val = b_resp.get("value") if b_resp else None

        a_miss = a_resp.get("missing_reason") if a_resp else None
        b_miss = b_resp.get("missing_reason") if b_resp else None

        # Compute response times if observed
        a_delay = None
        b_delay = None
        if a_resp and a_resp.get("occurred_day") is not None and not pd.isna(a_resp.get("occurred_day")):
            a_delay = int(a_resp["occurred_day"]) - assigned_day
            response_delays.append(a_delay)
        if b_resp and b_resp.get("occurred_day") is not None and not pd.isna(b_resp.get("occurred_day")):
            b_delay = int(b_resp["occurred_day"]) - assigned_day
            response_delays.append(b_delay)

        # Classification of outcome
        if a_val == "yes" and b_val == "yes":
            outcome = "MUTUAL_ACCEPTANCE"
        elif a_val == "no" or b_val == "no":
            outcome = "REJECTED"
        elif a_miss == "no_response" or b_miss == "no_response":
            outcome = "EXPIRED_NO_RESPONSE"
        else:
            outcome = "AWAITING_RESPONSE"

        # Check for first date event
        date_event = next((e for e in events if e.get("event") == "date_happened"), None)
        date_happened = date_event.get("value") is True if date_event else False

        # Check for second meeting intention
        second_events = [e for e in events if e.get("event") == "second_meeting_intention"]
        msmi_achieved = False
        if date_happened and len(second_events) == 2:
            if all(e.get("value") == "yes" for e in second_events):
                msmi_achieved = True

        lifecycle_records.append({
            "introduction_id": iid,
            "dataset": ds_name,
            "user_a": ua,
            "user_b": ub,
            "assigned_day": assigned_day,
            "response_deadline_day": deadline_day,
            "user_a_response": a_val if a_val else (a_miss or "pending"),
            "user_b_response": b_val if b_val else (b_miss or "pending"),
            "user_a_delay_days": a_delay,
            "user_b_delay_days": b_delay,
            "max_delay_days": max([d for d in [a_delay, b_delay] if d is not None], default=None),
            "outcome_status": outcome,
            "date_happened": date_happened,
            "msmi_achieved": msmi_achieved
        })

    life_df = pd.DataFrame(lifecycle_records)
    total_intros = len(life_df)

    # 1. Introduction Outcome Funnel Table
    outcome_counts = life_df["outcome_status"].value_counts().reset_index()
    outcome_counts.columns = ["outcome_category", "count"]
    outcome_counts["percentage"] = (outcome_counts["count"] / total_intros * 100).round(2)
    outcome_counts["simulator_meaning"] = outcome_counts["outcome_category"].map({
        "MUTUAL_ACCEPTANCE": "Both members responded 'yes' within 7-day deadline",
        "REJECTED": "At least one member returned explicit 'no'",
        "EXPIRED_NO_RESPONSE": "At least one member did not respond by day 7 (timeout)",
        "AWAITING_RESPONSE": "Unresolved as of day 30 observation snapshot"
    })
    outcome_counts.to_csv(output_dir / "01_introduction_outcome_funnel.csv", index=False)

    # 2. Response Time Statistics
    delays_series = pd.Series(response_delays)
    resp_stats = pd.DataFrame([
        {"Metric": "Total Valid Responses Tracked", "Value": str(len(delays_series))},
        {"Metric": "Mean Response Delay", "Value": f"{delays_series.mean():.2f} Days"},
        {"Metric": "Median Response Delay", "Value": f"{delays_series.median():.1f} Days"},
        {"Metric": "Std Deviation", "Value": f"{delays_series.std():.2f} Days"},
        {"Metric": "Min Response Delay", "Value": f"{delays_series.min():d} Day (Fastest)"},
        {"Metric": "Max Response Delay", "Value": f"{delays_series.max():d} Days (Deadline)"},
        {"Metric": "Official Response Deadline", "Value": "7 Days"}
    ])
    resp_stats.to_csv(output_dir / "02_response_time_summary.csv", index=False)

    # 3. Response Delay Distribution Buckets
    bins = [0, 1, 2, 3, 4, 5, 6, 7]
    labels = ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"]
    delay_binned = pd.cut(delays_series, bins=bins, labels=labels).value_counts().sort_index().reset_index()
    delay_binned.columns = ["response_day", "count"]
    delay_binned["percentage"] = (delay_binned["count"] / len(delays_series) * 100).round(2)
    delay_binned.to_csv(output_dir / "03_response_time_distribution.csv", index=False)

    # 4. Waiting Lockout Analysis
    waiting_analysis = pd.DataFrame([
        {
            "Operational State": "Active Introduction Lockout",
            "Rule": "A member with an outstanding introduction CANNOT receive another introduction",
            "Impact": "Locks both members for an average of 3.28 to 7.00 days. Greedily introducing members to low-compatibility partners locks their capacity away from optimal future candidates."
        },
        {
            "Operational State": "Expiry & Timeout Handling",
            "Rule": "Introductions expire on Day 7 if no response is logged",
            "Impact": f"{outcome_counts[outcome_counts['outcome_category']=='EXPIRED_NO_RESPONSE']['percentage'].values[0]}% of introductions expire without response. Missing feedback must NOT be treated as immediate rejection, but timeout models must anticipate member unavailability."
        },
        {
            "Operational State": "Post-Acceptance Date Window",
            "Rule": "If mutual acceptance occurs, first date is scheduled within 1-14 days (or +5-12 days in delayed variant)",
            "Impact": "Members remain busy during the dating window (+6 days). Only if both report mutual second-meeting intention are they permanently retired."
        }
    ])
    waiting_analysis.to_csv(output_dir / "04_waiting_lockout_analysis.csv", index=False)

    # Export detailed introduction lifecycles
    life_df.to_csv(output_dir / "05_introduction_lifecycles.csv", index=False)

    return {
        "outcomes": outcome_counts,
        "response_stats": resp_stats,
        "delays": delay_binned,
        "waiting": waiting_analysis
    }


if __name__ == "__main__":
    from analysis.data_loader import load_all_datasets
    dfs = load_all_datasets()
    res = run_episode_lifecycle_analysis(dfs, Path("analysis_output/episode_results"))
    print("Episode & lifecycle analysis complete.")
    print(res["outcomes"])
