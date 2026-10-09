# Data Dictionary: The Sequential Matching Problem

**Release Version:** 1.0.0 | **Author:** Monu (Data Analyst)

This document provides the exhaustive specification of all tables, fields, types, and semantics in the 10 benchmark datasets (`public_01` to `public_10`).

---

## 1. Primary Datasets Overview

| File Name | Format | Record Count | Description | Primary Key |
| :--- | :--- | :--- | :--- | :--- |
| `members.jsonl` / `.csv` | JSONL / CSV | 2,000 | Core member profiles, demographics, observed values, and status | `member_id` |
| `questionnaires.jsonl` / `.csv` | JSONL / CSV | 2,000 | Initial self-reported preferences and constraint questionnaires | `member_id` |
| `introductions.jsonl` / `.csv` | JSONL / CSV | 613 | Historical introduction proposals logged up to Day 30 | `introduction_id` |
| `feedback.jsonl` / `.csv` | JSONL / CSV | 1,270 | Member responses ('yes'/'no'/'no_response') and date events | Compound |
| `conversations.jsonl` / `.csv` | JSONL / CSV | 1,129 | Synthetic conversational transcripts revealing latent soft traits | `member_id` |
| `state.json` | JSON | 10 files | Complete checkpoint state at Day 30 (ask budget remaining: 12) | N/A |
| `ask_log.csv` | CSV | 619 rows | Audit trail of historical clarification queries spent | N/A |

---

## 2. Member Profile Attributes (`members.jsonl`)

### Static Demographic Fields
* **`member_id`** (`str`): Unique opaque synthetic identifier (e.g., `syn_ee6abfe43191...`). Unique across all pools.
* **`pool_id`** (`str`): Identifier of the disjoint population pool (e.g., `public_01`).
* **`age`** (`int`): Stated age in years (Range: 21–46; Mean: 32.7). Under 18 is strictly prohibited.
* **`gender`** (`str`): Stated gender (`woman`, `man`, `non_binary`).
* **`zone`** (`str`): Fictional geographic cluster (`zone_a`, `zone_b`, `zone_c`, `zone_d`). In `sparse` variant, expands to 12 clusters (`zone_0` to `zone_11`).
* **`arrived_day`** (`int`): Day the member joined the pool (70% arrive on Day 0; rest trickle in between Days 1–20).
* **`available`** (`bool`): True if member is unpaused, within residence window (`arrived_day <= day < exit_day`), and not currently locked in an active introduction.

---

## 3. Hard Constraints (Reciprocal Blockers)

Every hard field possesses a corresponding `field_status` (`observed`, `not_asked`, `declined`) and `field_observed_day`.
**Rule:** If a field status is `not_asked`, its value is `None` (UNKNOWN). **Missing fields NEVER imply incompatibility or rejection.**

| Field Name | Type | Allowed Vocabulary | Unknown Semantic | Feasibility Check |
| :--- | :--- | :--- | :--- | :--- |
| `who_to_meet` | `list[str]` | Subset of `['woman', 'man', 'non_binary']` | `None` $\rightarrow$ UNKNOWN | Partner's gender MUST be in this list (both ways). |
| `age_min` | `int` | Integer (18 to 65) | `None` $\rightarrow$ UNKNOWN | Partner's age MUST be $\ge$ `age_min`. |
| `age_max` | `int` | Integer (18 to 65) | `None` $\rightarrow$ UNKNOWN | Partner's age MUST be $\le$ `age_max`. |
| `acceptable_zones` | `list[str]` | Subset of zones | `None` $\rightarrow$ UNKNOWN | Partner's zone MUST be in acceptable list (both ways). |
| `smoking` | `str` | `['no', 'occasionally', 'yes']` | `None` $\rightarrow$ UNKNOWN | Self-reported smoking frequency. |
| `partner_smoking` | `str` | `['no_smoking', 'any']` | `None` $\rightarrow$ UNKNOWN | If `no_smoking`, partner smoking cannot be `yes` or `occasionally`. |
| `has_children` | `bool` | `[True, False]` | `None` $\rightarrow$ UNKNOWN | Self-reported presence of dependent children. |
| `partner_children` | `str` | `['no_children', 'any']` | `None` $\rightarrow$ UNKNOWN | If `no_children`, partner cannot have children. |
| `wants_children` | `str` | `['yes', 'no', 'unsure']` | `None` $\rightarrow$ UNKNOWN | Mutually conflicting only if the pair set is exactly `{'yes', 'no'}`. |
| `relationship_structure` | `str` | `['monogamous', 'non_monogamous']` | `None` $\rightarrow$ UNKNOWN | Both partners must have identical structure. |
| `schedule` | `list[str]` | Subset of `['weekday_evening', 'weekend_day', 'weekend_evening']` | `None` $\rightarrow$ UNKNOWN | Intersection of schedule sets must be non-empty. |

---

## 4. Soft Preference Attributes (Compatibility Drivers)

Soft fields do not block pairs. They modulate mutual acceptance probability and MSMI intention.

| Field Name | Type | Allowed Values | Latent Weight (First Date) | Latent Weight (MSMI) |
| :--- | :--- | :--- | :--- | :--- |
| `relationship_goal` | `str` | `['long_term', 'exploring']` | **+0.70** | **+0.40** |
| `relationship_pace` | `str` | `['slow', 'steady', 'quick']` | **+0.40** | 0.00 |
| `lifestyle` | `str` | `['quiet', 'mixed', 'social']` | **+0.25** | 0.00 |
| `conversations` | `str` | `['ideas', 'stories', 'practical', 'playful']` | **+0.20** | 0.00 |
| `emotional_availability` | `str` | `['ready', 'taking_time']` | Neutral | Neutral |
| `space_for_relationship` | `str` | `['limited', 'moderate', 'ample']` | Neutral | Neutral |
| `relocate` | `str` | `['yes', 'no', 'unsure']` | Neutral | Neutral |
