"""Master Analytical Pipeline Runner for The Sequential Matching Problem.
Executes the full end-to-end data science pipeline:
1. Data loading & unification across 10 pools
2. Data quality & missingness audits
3. Descriptive statistics & demographic distributions
4. Feature engineering & dictionary compilation
5. Pair-level Cartesian evaluation (199,000 combinations)
6. Candidate degree, N metric & zero-candidate root causes
7. Episode lifecycle, waiting lockouts & turnaround times
8. Policy benchmarking (V2.2 vs Greedy, Random, No-Asks)
9. SVG vector chart generation
10. Markdown deliverables & 15-sheet Excel workbook
11. Interactive academic web showcase (showcase/index.html)
"""

import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from analysis.data_loader import load_all_datasets
from analysis.data_quality import audit_data_quality
from analysis.descriptive_analysis import run_descriptive_analysis
from analysis.feature_engineering import get_feature_dictionary
from analysis.pair_analysis import run_pair_level_analysis
from analysis.candidate_analysis import run_candidate_analysis
from analysis.episode_analysis import run_episode_lifecycle_analysis
from analysis.policy_analysis import run_policy_benchmark_analysis
from analysis.generate_charts import generate_all_showcase_charts
from analysis.generate_report import generate_all_reports_and_workbooks
from analysis.generate_showcase import generate_html_showcase


def run_complete_pipeline():
    start_time = time.perf_counter()
    print("=" * 70)
    print("STARTING REPRODUCIBLE DATA ANALYTICS PIPELINE")
    print("Project: The Sequential Matching Problem (Hackathon Release 1.0.0)")
    print("Author: Monu (Lead Data Analyst)")
    print("=" * 70)

    # Directories
    output_base = PROJECT_ROOT / "analysis_output"
    desc_dir = output_base / "descriptive_results"
    pair_dir = output_base / "pair_results"
    cand_dir = output_base / "candidate_results"
    ep_dir = output_base / "episode_results"
    pol_dir = output_base / "policy_results"
    charts_dir = output_base / "charts"
    reports_dir = output_base / "reports"
    showcase_dir = PROJECT_ROOT / "showcase"

    for d in [desc_dir, pair_dir, cand_dir, ep_dir, pol_dir, charts_dir, reports_dir, showcase_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Step 1: Load Data
    print("\n[Step 1/11] Loading and unifying all 10 benchmark datasets...")
    dfs = load_all_datasets(PROJECT_ROOT / "data")
    print(f" -> Unified {len(dfs['members'])} members, {len(dfs['introductions'])} introductions, {len(dfs['feedback'])} feedback events.")

    # Step 2: Data Quality & Missingness
    print("\n[Step 2/11] Auditing data quality, duplicate IDs, and field missingness...")
    audit_data_quality(dfs, desc_dir)
    print(" -> Data quality and missingness reports generated.")

    # Step 3: Descriptive Analysis
    print("\n[Step 3/11] Computing demographic distributions and grounded insights...")
    run_descriptive_analysis(dfs, desc_dir)
    print(" -> Descriptive distributions and cross-tabulations complete.")

    # Step 4: Feature Engineering
    print("\n[Step 4/11] Compiling official Feature Dictionary & compatibility logic...")
    feat_df = get_feature_dictionary()
    feat_df.to_csv(reports_dir / "FEATURE_DICTIONARY.csv", index=False)
    print(f" -> Feature dictionary compiled with {len(feat_df)} features.")

    # Step 5: Pair-Level Cartesian Analysis
    print("\n[Step 5/11] Evaluating within-pool pair combinations (199,000 edges)...")
    pair_res = run_pair_level_analysis(dfs, pair_dir)
    print(" -> Pair-level feasibility and incompatibility breakdown complete.")

    # Step 6: Candidate & N Analysis
    print("\n[Step 6/11] Calculating candidate degrees, N metric, and zero-candidate causes...")
    cand_res = run_candidate_analysis(dfs, cand_dir)
    print(" -> Candidate availability and scarcity analysis complete.")

    # Step 7: Episode Lifecycle & Waiting
    print("\n[Step 7/11] Analyzing introduction lifecycle, waiting lockout, and response times...")
    ep_res = run_episode_lifecycle_analysis(dfs, ep_dir)
    print(" -> Lifecycle, waiting, and turnaround distributions complete.")

    # Step 8: Policy Benchmarking
    print("\n[Step 8/11] Benchmarking V2.2 vs Greedy, Random, and No-Asks baselines...")
    pol_res = run_policy_benchmark_analysis(PROJECT_ROOT, pol_dir)
    print(" -> Multi-seed, all-variant benchmark analysis complete.")

    # Step 9: Vector SVG Charts
    print("\n[Step 9/11] Rendering academic vector SVG visualizations...")
    generate_all_showcase_charts(desc_dir, pair_dir, cand_dir, ep_dir, pol_dir, charts_dir)
    print(" -> Vector SVG charts successfully generated.")

    # Step 10: Reports and Excel Workbook
    print("\n[Step 10/11] Generating markdown deliverables and 15-sheet Excel workbook...")
    generate_all_reports_and_workbooks(
        dfs, desc_dir, pair_dir, cand_dir, ep_dir, pol_dir, reports_dir, PROJECT_ROOT
    )
    print(" -> Master Excel workbook and research documents generated.")

    # Step 11: Web Showcase
    print("\n[Step 11/11] Generating interactive academic web showcase...")
    generate_html_showcase(
        desc_dir, pair_dir, cand_dir, ep_dir, pol_dir, charts_dir, showcase_dir / "index.html"
    )
    print(" -> Showcase available at showcase/index.html")

    elapsed = time.perf_counter() - start_time
    print("\n" + "=" * 70)
    print(f"PIPELINE COMPLETED SUCCESSFULLY IN {elapsed:.2f} SECONDS")
    print(f"Deliverables located in:")
    print(f" - Reports:  {reports_dir}")
    print(f" - Charts:   {charts_dir}")
    print(f" - Showcase: {showcase_dir / 'index.html'}")
    print(f" - Excel:    {reports_dir / 'Sequential_Matching_Data_Analysis_Showcase.xml'}")
    print("=" * 70)


if __name__ == "__main__":
    run_complete_pipeline()
