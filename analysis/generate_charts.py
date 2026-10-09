"""Research Vector SVG Chart Generation Module for The Sequential Matching Problem.
Generates publication-quality, scalable SVG visualizations with academic styling:
clean typography, high contrast, explicit axis units, legends, and dataset citations.
"""

from pathlib import Path
from typing import Dict, Any, List
import pandas as pd


def create_svg_bar_chart(
    title: str,
    subtitle: str,
    x_labels: List[str],
    y_values: List[float],
    x_title: str,
    y_title: str,
    output_path: Path,
    unit: str = "%",
    color: str = "#1e3a8a",
    secondary_color: str = "#3b82f6"
) -> None:
    """Generate a clean academic vertical bar chart in pure vector SVG."""
    width, height = 750, 420
    margin_top, margin_bottom, margin_left, margin_right = 70, 70, 80, 40
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom

    max_val = max(y_values) if y_values and max(y_values) > 0 else 100
    y_max = max_val * 1.15

    n_bars = len(x_labels)
    bar_width = min(60, plot_width / (n_bars * 1.5))
    gap = (plot_width - (n_bars * bar_width)) / (n_bars + 1)

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif; background: #ffffff;">',
        f'  <rect width="{width}" height="{height}" fill="#ffffff" rx="8"/>',
        # Title
        f'  <text x="{margin_left}" y="32" font-size="16" font-weight="700" fill="#0f172a">{title}</text>',
        f'  <text x="{margin_left}" y="50" font-size="12" fill="#64748b">{subtitle}</text>',
    ]

    # Grid lines and Y-axis labels
    n_ticks = 5
    for i in range(n_ticks + 1):
        tick_val = (y_max / n_ticks) * i
        y_pos = margin_top + plot_height - (tick_val / y_max * plot_height)
        svg.append(f'  <line x1="{margin_left}" y1="{y_pos}" x2="{width - margin_right}" y2="{y_pos}" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="3,3"/>')
        val_str = f"{tick_val:.1f}{unit}" if isinstance(tick_val, float) and tick_val < 10 else f"{int(tick_val)}{unit}"
        svg.append(f'  <text x="{margin_left - 10}" y="{y_pos + 4}" font-size="11" fill="#64748b" text-anchor="end">{val_str}</text>')

    # Axes
    svg.append(f'  <line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_height}" stroke="#94a3b8" stroke-width="1.5"/>')
    svg.append(f'  <line x1="{margin_left}" y1="{margin_top + plot_height}" x2="{width - margin_right}" y2="{margin_top + plot_height}" stroke="#94a3b8" stroke-width="1.5"/>')

    # Bars
    for i, (label, val) in enumerate(zip(x_labels, y_values)):
        x_pos = margin_left + gap + i * (bar_width + gap)
        bar_h = (val / y_max) * plot_height if y_max > 0 else 0
        y_pos = margin_top + plot_height - bar_h

        bar_color = color if i % 2 == 0 else secondary_color
        svg.append(f'  <rect x="{x_pos}" y="{y_pos}" width="{bar_width}" height="{bar_h}" fill="{bar_color}" rx="3">')
        svg.append(f'    <title>{label}: {val}{unit}</title>')
        svg.append('  </rect>')

        # Value label on top of bar
        val_display = f"{val:.1f}{unit}" if isinstance(val, float) else f"{val}{unit}"
        svg.append(f'  <text x="{x_pos + bar_width/2}" y="{y_pos - 6}" font-size="11" font-weight="600" fill="#1e293b" text-anchor="middle">{val_display}</text>')

        # X label
        svg.append(f'  <text x="{x_pos + bar_width/2}" y="{margin_top + plot_height + 18}" font-size="11" fill="#334155" text-anchor="middle">{label}</text>')

    # Axis Titles
    svg.append(f'  <text x="{margin_left + plot_width/2}" y="{height - 15}" font-size="12" font-weight="600" fill="#475569" text-anchor="middle">{x_title}</text>')
    svg.append(f'  <text transform="rotate(-90 22 {margin_top + plot_height/2})" x="22" y="{margin_top + plot_height/2}" font-size="12" font-weight="600" fill="#475569" text-anchor="middle">{y_title}</text>')

    svg.append('</svg>')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(svg), encoding="utf-8")


def create_svg_horizontal_bar_chart(
    title: str,
    subtitle: str,
    categories: List[str],
    values: List[float],
    types: List[str],
    output_path: Path
) -> None:
    """Generate a clean horizontal bar chart for missingness across fields."""
    width, height = 780, 520
    margin_top, margin_bottom, margin_left, margin_right = 70, 50, 190, 80
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom

    n_bars = len(categories)
    bar_height = min(22, plot_height / (n_bars * 1.3))
    gap = (plot_height - (n_bars * bar_height)) / (n_bars + 1)

    max_val = 100.0  # Percentage scale

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif; background: #ffffff;">',
        f'  <rect width="{width}" height="{height}" fill="#ffffff" rx="8"/>',
        f'  <text x="{margin_left}" y="32" font-size="16" font-weight="700" fill="#0f172a">{title}</text>',
        f'  <text x="{margin_left}" y="50" font-size="12" fill="#64748b">{subtitle}</text>',
    ]

    # Legend
    svg.append(f'  <rect x="{width - margin_right - 230}" y="24" width="12" height="12" fill="#dc2626" rx="2"/>')
    svg.append(f'  <text x="{width - margin_right - 212}" y="34" font-size="11" fill="#334155">Hard Constraint</text>')
    svg.append(f'  <rect x="{width - margin_right - 110}" y="24" width="12" height="12" fill="#3b82f6" rx="2"/>')
    svg.append(f'  <text x="{width - margin_right - 92}" y="34" font-size="11" fill="#334155">Soft Preference</text>')

    # Vertical gridlines
    for pct in [0, 20, 40, 60, 80, 100]:
        x_pos = margin_left + (pct / max_val * plot_width)
        svg.append(f'  <line x1="{x_pos}" y1="{margin_top}" x2="{x_pos}" y2="{margin_top + plot_height}" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="3,3"/>')
        svg.append(f'  <text x="{x_pos}" y="{margin_top + plot_height + 18}" font-size="11" fill="#64748b" text-anchor="middle">{pct}%</text>')

    # Left Y axis line
    svg.append(f'  <line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_height}" stroke="#94a3b8" stroke-width="1.5"/>')

    # Bars
    for i, (cat, val, ftype) in enumerate(zip(categories, values, types)):
        y_pos = margin_top + gap + i * (bar_height + gap)
        bar_w = (val / max_val) * plot_width
        b_color = "#dc2626" if "HARD" in ftype.upper() else "#3b82f6"

        # Label on left
        svg.append(f'  <text x="{margin_left - 10}" y="{y_pos + bar_height/2 + 4}" font-size="11" fill="#1e293b" text-anchor="end">{cat}</text>')

        # Bar
        svg.append(f'  <rect x="{margin_left}" y="{y_pos}" width="{bar_w}" height="{bar_height}" fill="{b_color}" rx="3">')
        svg.append(f'    <title>{cat}: {val:.1f}% missing ({ftype})</title>')
        svg.append('  </rect>')

        # Value on right
        svg.append(f'  <text x="{margin_left + bar_w + 8}" y="{y_pos + bar_height/2 + 4}" font-size="11" font-weight="600" fill="#334155">{val:.1f}%</text>')

    svg.append(f'  <text x="{margin_left + plot_width/2}" y="{height - 12}" font-size="12" font-weight="600" fill="#475569" text-anchor="middle">Missingness Percentage (%)</text>')
    svg.append('</svg>')

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(svg), encoding="utf-8")


def create_svg_flowchart(output_path: Path) -> None:
    """Generate a clean matching lifecycle process flowchart in SVG."""
    width, height = 800, 320
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif; background: #ffffff;">',
        f'  <rect width="{width}" height="{height}" fill="#ffffff" rx="8"/>',
        f'  <text x="30" y="32" font-size="16" font-weight="700" fill="#0f172a">Sequential Matching Lifecycle & Concurrency Protocol</text>',
        f'  <text x="30" y="50" font-size="12" fill="#64748b">Two-phase daily execution loop with 12-unit asking budget and 7-day waiting lockout</text>',
    ]

    steps = [
        ("1. Observe", "Inspect active\nmembers & feed", "#1e3a8a"),
        ("2. Clarify", "Spend <=12 units\nask budget", "#2563eb"),
        ("3. Feasibility", "Reciprocal 22-rule\nchecks", "#0d9488"),
        ("4. Allocate", "Global matching\n& UCB scoring", "#059669"),
        ("5. Waiting", "7-day lock\n(no rematches)", "#d97706"),
        ("6. Resolve", "Feedback -> date\n-> MSMI outcome", "#7c3aed")
    ]

    box_w, box_h = 105, 75
    y_box = 105
    start_x = 30
    gap = 25

    for i, (title, desc, col) in enumerate(steps):
        x = start_x + i * (box_w + gap)
        # Box
        svg.append(f'  <rect x="{x}" y="{y_box}" width="{box_w}" height="{box_h}" fill="#f8fafc" stroke="{col}" stroke-width="2" rx="6"/>')
        svg.append(f'  <text x="{x + box_w/2}" y="{y_box + 24}" font-size="12" font-weight="700" fill="{col}" text-anchor="middle">{title}</text>')

        lines = desc.split("\n")
        for line_idx, line in enumerate(lines):
            svg.append(f'  <text x="{x + box_w/2}" y="{y_box + 44 + line_idx*14}" font-size="10" fill="#64748b" text-anchor="middle">{line}</text>')

        # Arrow to next
        if i < len(steps) - 1:
            arr_x = x + box_w
            mid_x = arr_x + gap / 2
            svg.append(f'  <line x1="{arr_x + 3}" y1="{y_box + box_h/2}" x2="{arr_x + gap - 5}" y2="{y_box + box_h/2}" stroke="#94a3b8" stroke-width="2"/>')
            svg.append(f'  <polygon points="{arr_x + gap - 5},{y_box + box_h/2 - 4} {arr_x + gap},{y_box + box_h/2} {arr_x + gap - 5},{y_box + box_h/2 + 4}" fill="#94a3b8"/>')

    # Bottom explanatory cards
    svg.append(f'  <rect x="30" y="215" width="355" height="75" fill="#eff6ff" stroke="#bfdbfe" rx="6"/>')
    svg.append(f'  <text x="45" y="238" font-size="12" font-weight="700" fill="#1e3a8a">Exploration Mechanism (The Asking Budget)</text>')
    svg.append(f'  <text x="45" y="258" font-size="11" fill="#3b82f6">Target 3-unit hard bundle queries to members with high potential degree.</text>')
    svg.append(f'  <text x="45" y="274" font-size="11" fill="#3b82f6">Unlocks candidate edges from the 40,715 uncertain episode pool.</text>')

    svg.append(f'  <rect x="415" y="215" width="355" height="75" fill="#f0fdf4" stroke="#bbf7d0" rx="6"/>')
    svg.append(f'  <text x="430" y="238" font-size="12" font-weight="700" fill="#166534">Exploitation Mechanism (Allocation & Feedback)</text>')
    svg.append(f'  <text x="430" y="258" font-size="11" fill="#15803d">Score pairs using soft trait alignment (goal +0.70, pace +0.40).</text>')
    svg.append(f'  <text x="430" y="274" font-size="11" fill="#15803d">Apply degree-scarcity bonuses to protect single-candidate members.</text>')

    svg.append('</svg>')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(svg), encoding="utf-8")


def generate_all_showcase_charts(
    descriptive_dir: Path,
    pair_dir: Path,
    cand_dir: Path,
    episode_dir: Path,
    policy_dir: Path,
    charts_output_dir: Path
) -> None:
    """Generate all 10+ publication-grade SVG charts for the research showcase."""
    charts_output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Age Distribution Chart
    age_groups_file = descriptive_dir / "05_age_groups.csv"
    if age_groups_file.exists():
        df_age = pd.read_csv(age_groups_file)
        create_svg_bar_chart(
            title="Participant Age Distribution (N = 2,000 Adults)",
            subtitle="Synthetic pool demographic breakdown across six standardized 5-year brackets",
            x_labels=df_age["age_group"].tolist(),
            y_values=df_age["percentage"].tolist(),
            x_title="Age Brackets (Years)",
            y_title="Proportion of Total Population (%)",
            output_path=charts_output_dir / "chart_01_age_distribution.svg",
            unit="%",
            color="#1e3a8a",
            secondary_color="#2563eb"
        )

    # 2. Zone Distribution Chart
    zone_file = descriptive_dir / "07_location_distribution.csv"
    if zone_file.exists():
        df_zone = pd.read_csv(zone_file)
        create_svg_bar_chart(
            title="Geographic Zone Distribution Across 10 Benchmark Pools",
            subtitle="Demonstrates heavy population concentration in Zone A vs extreme scarcity in Zone D",
            x_labels=[z.upper() for z in df_zone["zone"].tolist()],
            y_values=df_zone["percentage"].tolist(),
            x_title="Geographic Cluster",
            y_title="Population Share (%)",
            output_path=charts_output_dir / "chart_02_geographic_distribution.svg",
            unit="%",
            color="#0d9488",
            secondary_color="#14b8a6"
        )

    # 3. Missingness Chart (Horizontal)
    miss_file = descriptive_dir / "02_missingness_report.csv"
    if miss_file.exists():
        df_miss = pd.read_csv(miss_file).sort_values("missing_percentage", ascending=False)
        create_svg_horizontal_bar_chart(
            title="Field Missingness Audit: Hard Constraints vs. Soft Preferences",
            subtitle="Missing values represent uncertainty (UNKNOWN), never rejection; hard missingness locks edges",
            categories=df_miss["field_name"].tolist()[:14],
            values=df_miss["missing_percentage"].tolist()[:14],
            types=df_miss["field_type"].tolist()[:14],
            output_path=charts_output_dir / "chart_03_missingness_audit.svg"
        )

    # 4. Incompatibility Reasons Chart
    reasons_file = pair_dir / "02_incompatibility_reasons_distribution.csv"
    if reasons_file.exists():
        df_reasons = pd.read_csv(reasons_file)
        create_svg_bar_chart(
            title="Primary Causes of Hard Reciprocal Incompatibility",
            subtitle="Breakdown of rule failures across 199,000 pair-level combinations",
            x_labels=[r.replace("_", " ").title() for r in df_reasons["failure_reason"].tolist()[:6]],
            y_values=df_reasons["percentage_of_incompatible_pairs"].tolist()[:6],
            x_title="Constraint Rule Violated",
            y_title="Share of Incompatible Pairs (%)",
            output_path=charts_output_dir / "chart_04_incompatibility_causes.svg",
            unit="%",
            color="#dc2626",
            secondary_color="#ea580c"
        )

    # 5. Candidate Bracket Distribution Chart
    brackets_file = cand_dir / "02_candidate_bracket_distribution.csv"
    if brackets_file.exists():
        df_brack = pd.read_csv(brackets_file)
        create_svg_bar_chart(
            title="Candidate Degree Distribution: Feasible Options per Member",
            subtitle="Distribution of confirmed available candidates per participant under Day 30 observation",
            x_labels=df_brack["candidate_bracket"].tolist(),
            y_values=df_brack["percentage"].tolist(),
            x_title="Candidate Count Range",
            y_title="Proportion of Members (%)",
            output_path=charts_output_dir / "chart_05_candidate_degrees.svg",
            unit="%",
            color="#4338ca",
            secondary_color="#6366f1"
        )

    # 6. Introduction Outcomes Funnel Chart
    outcomes_file = episode_dir / "01_introduction_outcome_funnel.csv"
    if outcomes_file.exists():
        df_out = pd.read_csv(outcomes_file)
        create_svg_bar_chart(
            title="Historical Introduction Outcome Funnel (613 Introductions)",
            subtitle="Distribution of final responses: mutual acceptance vs rejection vs 7-day timeout",
            x_labels=[o.replace("_", " ").title() for o in df_out["outcome_category"].tolist()],
            y_values=df_out["percentage"].tolist(),
            x_title="Introduction Resolution Status",
            y_title="Percentage of Total Introductions (%)",
            output_path=charts_output_dir / "chart_06_outcome_funnel.svg",
            unit="%",
            color="#059669",
            secondary_color="#10b981"
        )

    # 7. Response Time Delay Chart
    delays_file = episode_dir / "03_response_time_distribution.csv"
    if delays_file.exists():
        df_del = pd.read_csv(delays_file)
        create_svg_bar_chart(
            title="Empirical Response Time Distribution (Mean = 3.28 Days)",
            subtitle="Observed turnaround time from introduction assignment to participant response",
            x_labels=df_del["response_day"].tolist(),
            y_values=df_del["percentage"].tolist(),
            x_title="Turnaround Days to Response",
            y_title="Proportion of Responding Members (%)",
            output_path=charts_output_dir / "chart_07_response_times.svg",
            unit="%",
            color="#d97706",
            secondary_color="#f59e0b"
        )

    # 8. Policy Comparison Chart
    policy_comp_file = policy_dir / "01_policy_overall_comparison.csv"
    if policy_comp_file.exists():
        df_pol = pd.read_csv(policy_comp_file)
        create_svg_bar_chart(
            title="Policy Benchmark: Mutual Acceptances per 100 Members",
            subtitle="Evaluated across 120 episodes (6 scenario families, 5 seeds per scenario)",
            x_labels=df_pol["Policy"].tolist(),
            y_values=df_pol["Mutual Acceptances / 100"].tolist(),
            x_title="Decision Policy",
            y_title="Mutual Acceptances per 100 Arrived",
            output_path=charts_output_dir / "chart_08_policy_acceptance_comparison.svg",
            unit="",
            color="#1e3a8a",
            secondary_color="#3b82f6"
        )

    # 9. Flowchart
    create_svg_flowchart(charts_output_dir / "chart_09_matching_lifecycle_process.svg")

    print(f"Generated all SVG research charts in {charts_output_dir}")


if __name__ == "__main__":
    generate_all_showcase_charts(
        Path("analysis_output/descriptive_results"),
        Path("analysis_output/pair_results"),
        Path("analysis_output/candidate_results"),
        Path("analysis_output/episode_results"),
        Path("analysis_output/policy_results"),
        Path("analysis_output/charts")
    )
