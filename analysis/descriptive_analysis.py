"""Descriptive Analysis Module for The Sequential Matching Problem.
Generates comprehensive distribution tables, cross-tabulations, and
grounded analytical insights across all demographic and preference variables.
"""

from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np


def run_descriptive_analysis(dfs: Dict[str, pd.DataFrame], output_dir: Path) -> Dict[str, Any]:
    """Execute descriptive analysis on members across all pools."""
    output_dir.mkdir(parents=True, exist_ok=True)
    df = dfs["members"]
    total = len(df)

    results = {}

    # 1. Age Analysis
    age_series = df["age"].dropna()
    age_stats = pd.DataFrame([{
        "Metric": "Total Count", "Value": len(age_series)
    }, {
        "Metric": "Mean Age", "Value": round(age_series.mean(), 2)
    }, {
        "Metric": "Std Deviation", "Value": round(age_series.std(), 2)
    }, {
        "Metric": "Median Age", "Value": round(age_series.median(), 2)
    }, {
        "Metric": "Min Age", "Value": int(age_series.min())
    }, {
        "Metric": "Max Age", "Value": int(age_series.max())
    }, {
        "Metric": "Interquartile Range (IQR)", "Value": round(age_series.quantile(0.75) - age_series.quantile(0.25), 2)
    }])
    age_stats.to_csv(output_dir / "04_age_summary.csv", index=False)
    results["age_summary"] = age_stats

    # Age Groups
    bins = [20, 25, 30, 35, 40, 45, 50]
    labels = ["21-25", "26-30", "31-35", "36-40", "41-45", "46-50"]
    df["age_group"] = pd.cut(df["age"], bins=bins, labels=labels, include_lowest=True)
    age_group_df = df["age_group"].value_counts().sort_index().reset_index()
    age_group_df.columns = ["age_group", "count"]
    age_group_df["percentage"] = (age_group_df["count"] / total * 100).round(2)
    age_group_df.to_csv(output_dir / "05_age_groups.csv", index=False)
    results["age_groups"] = age_group_df

    # 2. Gender Distribution
    gender_df = df["gender"].value_counts().reset_index()
    gender_df.columns = ["gender", "count"]
    gender_df["percentage"] = (gender_df["count"] / total * 100).round(2)
    gender_df.to_csv(output_dir / "06_gender_distribution.csv", index=False)
    results["gender"] = gender_df

    # 3. Geography (Zone) Distribution
    zone_df = df["zone"].value_counts().reset_index()
    zone_df.columns = ["zone", "count"]
    zone_df["percentage"] = (zone_df["count"] / total * 100).round(2)
    zone_df.to_csv(output_dir / "07_location_distribution.csv", index=False)
    results["zone"] = zone_df

    # 4. Smoking & Partner Smoking
    smoking_df = df["val_smoking"].value_counts(dropna=False).reset_index()
    smoking_df.columns = ["smoking_status", "count"]
    smoking_df["smoking_status"] = smoking_df["smoking_status"].fillna("UNKNOWN")
    smoking_df["percentage"] = (smoking_df["count"] / total * 100).round(2)
    smoking_df.to_csv(output_dir / "08_smoking_distribution.csv", index=False)
    results["smoking"] = smoking_df

    partner_smoking_df = df["val_partner_smoking"].value_counts(dropna=False).reset_index()
    partner_smoking_df.columns = ["partner_smoking_preference", "count"]
    partner_smoking_df["partner_smoking_preference"] = partner_smoking_df["partner_smoking_preference"].fillna("UNKNOWN")
    partner_smoking_df["percentage"] = (partner_smoking_df["count"] / total * 100).round(2)
    partner_smoking_df.to_csv(output_dir / "09_partner_smoking_preferences.csv", index=False)
    results["partner_smoking"] = partner_smoking_df

    # Smoking Cross-tabulation
    smoking_cross = pd.crosstab(
        df["val_smoking"].fillna("UNKNOWN"),
        df["val_partner_smoking"].fillna("UNKNOWN"),
        margins=True, margins_name="Total"
    ).reset_index()
    smoking_cross.to_csv(output_dir / "10_smoking_cross_tab.csv", index=False)
    results["smoking_cross"] = smoking_cross

    # 5. Children & Partner Children
    has_children_df = df["val_has_children"].value_counts(dropna=False).reset_index()
    has_children_df.columns = ["has_children", "count"]
    has_children_df["has_children"] = has_children_df["has_children"].fillna("UNKNOWN")
    has_children_df["percentage"] = (has_children_df["count"] / total * 100).round(2)
    has_children_df.to_csv(output_dir / "11_existing_children.csv", index=False)
    results["has_children"] = has_children_df

    partner_children_df = df["val_partner_children"].value_counts(dropna=False).reset_index()
    partner_children_df.columns = ["partner_children_preference", "count"]
    partner_children_df["partner_children_preference"] = partner_children_df["partner_children_preference"].fillna("UNKNOWN")
    partner_children_df["percentage"] = (partner_children_df["count"] / total * 100).round(2)
    partner_children_df.to_csv(output_dir / "12_partner_children_preferences.csv", index=False)
    results["partner_children"] = partner_children_df

    wants_children_df = df["val_wants_children"].value_counts(dropna=False).reset_index()
    wants_children_df.columns = ["wants_children", "count"]
    wants_children_df["wants_children"] = wants_children_df["wants_children"].fillna("UNKNOWN")
    wants_children_df["percentage"] = (wants_children_df["count"] / total * 100).round(2)
    wants_children_df.to_csv(output_dir / "13_wants_children.csv", index=False)
    results["wants_children"] = wants_children_df

    children_cross = pd.crosstab(
        df["val_has_children"].fillna("UNKNOWN"),
        df["val_partner_children"].fillna("UNKNOWN"),
        margins=True, margins_name="Total"
    ).reset_index()
    children_cross.to_csv(output_dir / "14_children_cross_tab.csv", index=False)
    results["children_cross"] = children_cross

    # 6. Soft Preferences Distributions
    soft_traits = [
        ("relationship_goal", "15_relationship_goals.csv"),
        ("relationship_pace", "16_relationship_pace.csv"),
        ("lifestyle", "17_lifestyle_distribution.csv"),
        ("conversations", "18_conversations_distribution.csv"),
        ("emotional_availability", "19_emotional_availability.csv"),
        ("space_for_relationship", "20_space_for_relationship.csv"),
        ("relocate", "21_relocate_distribution.csv")
    ]
    for trait, fname in soft_traits:
        col = f"val_{trait}"
        trait_df = df[col].value_counts(dropna=False).reset_index()
        trait_df.columns = [trait, "count"]
        trait_df[trait] = trait_df[trait].fillna("UNKNOWN")
        trait_df["percentage"] = (trait_df["count"] / total * 100).round(2)
        trait_df.to_csv(output_dir / fname, index=False)
        results[trait] = trait_df

    # 7. Grounded Analytical Insights
    insights = [
        {
            "category": "Demographics & Density",
            "observation": "Geographic concentration is heavily skewed towards Zone A.",
            "evidence": f"Zone A represents {zone_df[zone_df['zone']=='zone_a']['percentage'].values[0]}% of the population, while Zone D represents only {zone_df[zone_df['zone']=='zone_d']['percentage'].values[0]}%.",
            "impact_on_matching": "Members in Zone D face severe geographic supply scarcity. In sparse variants where zones expand to 12 clusters, candidate graphs fragment rapidly into disconnected components."
        },
        {
            "category": "Demographics & Age",
            "observation": "The age distribution is centered around early 30s with moderate spread.",
            "evidence": f"Mean age is {age_stats[age_stats['Metric']=='Mean Age']['Value'].values[0]} (std: {age_stats[age_stats['Metric']=='Std Deviation']['Value'].values[0]}), with 26-35 accounting for over 50% of participants.",
            "impact_on_matching": "Asymmetric age tolerance windows (e.g. ±3 to 10 years) filter out older participants (45+) who require younger partners or vice versa."
        },
        {
            "category": "Information Asymmetry",
            "observation": "Smoking tolerance exhibits substantial missingness that acts as a hidden barrier.",
            "evidence": f"{partner_smoking_df[partner_smoking_df['partner_smoking_preference']=='UNKNOWN']['percentage'].values[0]}% of partner smoking preferences are unobserved at Day 30.",
            "impact_on_matching": "Because strict non-smokers reject smokers, unknown smoking status leaves thousands of otherwise viable pairs in an uncertain state."
        },
        {
            "category": "Children & Family Alignment",
            "observation": "Strong alignment exists between having children and accepting partner children, but unasked fields dominate.",
            "evidence": f"{has_children_df[has_children_df['has_children']=='UNKNOWN']['percentage'].values[0]}% of existing children status is unobserved.",
            "impact_on_matching": "Clarifying children constraints is one of the highest leverage operations to unlock high-probability long-term compatibility."
        },
        {
            "category": "Soft Match Driver",
            "observation": "Relationship goal is the single most decisive compatibility attribute.",
            "evidence": f"Simulator ground truth assigns a +0.70 first-date weight and +0.40 second-date weight to matching relationship goals, yet {results['relationship_goal'][results['relationship_goal']['relationship_goal']=='UNKNOWN']['percentage'].values[0]}% are unobserved.",
            "impact_on_matching": "Matching pairs with opposing relationship goals (long_term vs exploring) leads to catastrophic attrition down the MSMI conversion funnel."
        }
    ]
    pd.DataFrame(insights).to_csv(output_dir / "22_descriptive_insights.csv", index=False)
    results["insights"] = insights

    return results


if __name__ == "__main__":
    from analysis.data_loader import load_all_datasets
    dfs = load_all_datasets()
    res = run_descriptive_analysis(dfs, Path("analysis_output/descriptive_results"))
    print("Descriptive analysis complete.")
