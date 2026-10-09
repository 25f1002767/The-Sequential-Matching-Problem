"""Data Loader Module for The Sequential Matching Problem.
Loads and unifies all 10 benchmark public datasets (public_01 through public_10).
Preserves missingness semantics: missing values are kept as None / np.nan and
treated as UNCERTAIN / UNKNOWN, not rejection.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

HARD_FIELDS = [
    'age_min', 'age_max', 'who_to_meet', 'relationship_structure',
    'smoking', 'partner_smoking', 'has_children', 'partner_children',
    'wants_children', 'acceptable_zones', 'schedule'
]

SOFT_FIELDS = [
    'relationship_goal', 'relationship_pace', 'lifestyle', 'conversations',
    'emotional_availability', 'space_for_relationship', 'relocate'
]


def find_data_root() -> Path:
    """Locate data root directory across repo layouts."""
    cwd = Path(os.getcwd())
    candidates = [
        cwd / "data",
        cwd,
        cwd.parent / "data",
        Path(r"C:\Users\monus\OneDrive\Desktop\The-Sequential-Matching-Problem-a8e26b35118cfa8e886a02f93984923e43ab64f6\data"),
        Path(r"C:\Users\monus\OneDrive\Desktop\data")
    ]
    for c in candidates:
        if c.exists() and (c / "public_01").exists():
            return c
    raise FileNotFoundError("Could not locate directory containing public_01 ... public_10")


def load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """Safely load JSONL file."""
    if not file_path.exists():
        return []
    records = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def load_json(file_path: Path) -> Optional[Dict[str, Any]]:
    """Safely load JSON file."""
    if not file_path.exists():
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def flatten_member(member: Dict[str, Any], dataset_name: str) -> Dict[str, Any]:
    """Flatten nested member dictionary while strictly preserving observation metadata."""
    fields = member.get("fields", {}) or {}
    field_status = member.get("field_status", {}) or {}
    field_observed_day = member.get("field_observed_day", {}) or {}

    flat = {
        "dataset": dataset_name,
        "member_id": member.get("member_id"),
        "pool_id": member.get("pool_id", dataset_name),
        "age": member.get("age"),
        "gender": member.get("gender"),
        "zone": member.get("zone"),
        "arrived_day": member.get("arrived_day", 0),
        "available": member.get("available", True),
        "synthetic": member.get("synthetic", True),
        "source": member.get("source", "synthetic_questionnaire"),
    }

    # Add hard & soft field values
    for field in HARD_FIELDS + SOFT_FIELDS:
        val = fields.get(field)
        # Lists (zones, schedule, who_to_meet) serialized cleanly
        if isinstance(val, list):
            flat[f"val_{field}"] = json.dumps(val)
            flat[f"raw_{field}"] = val
        else:
            flat[f"val_{field}"] = val
            flat[f"raw_{field}"] = val

        flat[f"status_{field}"] = field_status.get(field, "not_asked")
        flat[f"observed_day_{field}"] = field_observed_day.get(field)

    return flat


def load_all_datasets(data_root: Optional[Path] = None) -> Dict[str, pd.DataFrame]:
    """Load all 10 public datasets into a structured dictionary of DataFrames."""
    if data_root is None:
        data_root = find_data_root()

    all_members = []
    all_questionnaires = []
    all_introductions = []
    all_feedback = []
    all_conversations = []
    all_ask_logs = []
    dataset_summaries = []

    for i in range(1, 11):
        ds_name = f"public_{i:02d}"
        ds_dir = data_root / ds_name
        if not ds_dir.exists():
            continue

        # 1. Members
        m_file = ds_dir / "members.jsonl"
        members = load_jsonl(m_file)
        for m in members:
            all_members.append(flatten_member(m, ds_name))

        # 2. Questionnaires
        q_file = ds_dir / "questionnaires.jsonl"
        q_records = load_jsonl(q_file)
        if not q_records:
            # Fallback to CSV if jsonl missing
            q_csv = ds_dir / "questionnaires.csv"
            if q_csv.exists():
                q_df = pd.read_csv(q_csv)
                q_df["dataset"] = ds_name
                all_questionnaires.extend(q_df.to_dict(orient="records"))
        else:
            for q in q_records:
                q["dataset"] = ds_name
                all_questionnaires.append(q)

        # 3. Introductions
        intro_file = ds_dir / "introductions.csv"
        if intro_file.exists():
            intro_df = pd.read_csv(intro_file)
            intro_df["dataset"] = ds_name
            all_introductions.extend(intro_df.to_dict(orient="records"))

        # 4. Feedback
        fb_file = ds_dir / "feedback.csv"
        if fb_file.exists():
            fb_df = pd.read_csv(fb_file)
            fb_df["dataset"] = ds_name
            all_feedback.extend(fb_df.to_dict(orient="records"))

        # 5. Conversations
        conv_file = ds_dir / "conversations.csv"
        if conv_file.exists():
            conv_df = pd.read_csv(conv_file)
            conv_df["dataset"] = ds_name
            all_conversations.extend(conv_df.to_dict(orient="records"))

        # 6. Ask log
        ask_file = ds_dir / "ask_log.csv"
        if ask_file.exists():
            ask_df = pd.read_csv(ask_file)
            ask_df["dataset"] = ds_name
            all_ask_logs.extend(ask_df.to_dict(orient="records"))

        # Summary for this dataset
        dataset_summaries.append({
            "dataset": ds_name,
            "members_count": len(members),
            "introductions_count": len(intro_df) if intro_file.exists() else 0,
            "feedback_count": len(fb_df) if fb_file.exists() else 0,
            "conversations_count": len(conv_df) if conv_file.exists() else 0,
            "ask_log_count": len(ask_df) if ask_file.exists() else 0
        })

    members_df = pd.DataFrame(all_members)
    questionnaires_df = pd.DataFrame(all_questionnaires)
    introductions_df = pd.DataFrame(all_introductions)
    feedback_df = pd.DataFrame(all_feedback)
    conversations_df = pd.DataFrame(all_conversations)
    ask_logs_df = pd.DataFrame(all_ask_logs)
    summary_df = pd.DataFrame(dataset_summaries)

    return {
        "members": members_df,
        "questionnaires": questionnaires_df,
        "introductions": introductions_df,
        "feedback": feedback_df,
        "conversations": conversations_df,
        "ask_logs": ask_logs_df,
        "summary": summary_df
    }


if __name__ == "__main__":
    print("Testing data loader...")
    data = load_all_datasets()
    print(f"Loaded {len(data['members'])} members across {len(data['summary'])} datasets.")
    print(f"Introductions: {len(data['introductions'])}, Feedback: {len(data['feedback'])}")
