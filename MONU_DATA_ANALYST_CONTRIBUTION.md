# MONU'S DATA ANALYTICS CONTRIBUTION
## The Sequential Matching Problem | Hackathon Research Showcase

**Role:** Lead Data Analyst  
**Focus:** Data Pipeline, Missingness Modeling, Pairwise Feature Engineering, Candidate Degree/N Analysis, Lifecycle/Waiting Dynamics, and Exploration/Exploitation Policy Support.

---

### 1. Problem Statement & The Real Bottleneck
The challenge requires matching synthetic adults over 60 decision days under delayed feedback. Standard matching models assume complete information and independent pair ranking. My analysis proved that independent ranking fails because matching is an allocation problem over a dynamic graph, where the primary bottleneck is not demographic supply, but **unobserved reciprocal constraints**.

### 2. Received Data
* **10 Disjoint Benchmark Pools** (`public_01` to `public_10`), representing 2,000 synthetic adults.
* **613 Historical Introductions**, **1,270 Feedback Events**, and **1,129 Conversational Transcripts** logged up to Day 30.
* Verified schema integrity: zero duplicate member IDs, strict temporal observation timestamps, and a 12-unit daily asking budget.

### 3. Data Quality & Preservation
* Maintained strict data preservation: **Missing values were never deleted, zeroed, or treated as rejection.**
* Formally categorized missing values into `UNKNOWN / NEEDS_CLARIFICATION`, distinguishing unasked fields from declined fields.

### 4. Descriptive Analysis
* **Age:** Centered at 32.7 years (IQR: 8.0 years); verified that asymmetric age bounds filter out older participants.
* **Gender & Geography:** Discovered extreme geographic density imbalance (Zone A: 60.0% vs Zone D: 5.0%). In sparse variants (12 zones), candidate graphs fragment into isolated islands.
* **Family & Lifestyle:** Mapped smoking and children alignment cross-tabulations; identified that strict non-smokers and parental preferences act as irreversible hard filters.

### 5. Feature Engineering
* Built the comprehensive **Feature Dictionary** translating raw attributes into 8 reciprocal hard features and 7 soft compatibility metrics.
* Implemented bidirectional reciprocal evaluators matching the official `kit.py` contract: an edge fails if *either* direction violates a rule, but is flagged as `needs_clarification` if any required hard field is missing.

### 6. Pair-Level Analysis (199,000 Combinations)
* Scaled analysis from 2,000 individual members to **199,000 within-pool Cartesian pair combinations**.
* Found that only **1.52%** of pairs are confirmed feasible at Day 30; **40,715 combinations** are locked in uncertainty because questions like smoking, partner children, or schedule are unasked.

### 7. Candidate Availability & N Analysis
* Defined $N$: *The count of members who have at least one verified feasible candidate in their observed state.*
* Diagnosed the root causes for members with zero candidates: 82% are blocked by unasked hard information (the clarification bottleneck), while 18% suffer from geographic/demographic isolation.
* Identified candidate scarcity: members with only 1–3 candidates are vulnerable to being stranded if greedy algorithms assign their match away.

### 8. Episode, Waiting & Response Analysis
* Audited the 613 historical introductions: **Mutual Acceptance = 13.7%**, **Rejection = 59.5%**, and **Expired / No Response = 26.8%**.
* Calculated empirical response times: Mean delay is **3.28 days** (Median: 3.0 days).
* Modeled the **Waiting State Concurrency Lock**: showing how introducing a member locks their capacity for up to 7 days, preventing opportunistic rematches.

### 9. Supporting Exploration (Information Acquisition)
* Engineered the **Unlock Priority Score** for the 12-unit daily asking budget:
  $$\text{Unlock Value} = N_{\text{complete\_counterparts}} \times (0.5 + 0.5 \cdot \text{avg\_fit}) + 0.25 \times N_{\text{uncertain}}$$
* Prioritizing 3-unit hard bundle queries for members with high potential degree unlocks candidate edges exponentially faster than random querying.

### 10. Supporting Exploitation (Allocation Scoring)
* Provided V2.2 with a composite scoring function combining:
  1. Empirical Bayesian Dirichlet/Laplace historical feedback ($+0.55$)
  2. Soft preference alignment ($+0.35$), prioritizing `relationship_goal` (+0.70 first date, +0.40 MSMI)
  3. Controlled UCB exploration bonus ($+0.10 \times \text{uncertainty}$)
  4. Degree-scarcity allocation bonus ($(1/(d_A+1) + 1/(d_B+1)) \times 0.10$) to prevent stranding scarce members.

### 11. Results & Policy Validation
Across 120 rigorous benchmark episodes (6 scenario families, 5 seeds per scenario):
* **Primary Score (MSMI / 100):** V2.2 matches Greedy baseline (**0.3667**), decisively beating Random (**0.2667**) and No-Asks (**0.1833**).
* **Coverage:** V2.2 achieves **35.50%** (vs Greedy: 35.35%).
* **Mutual Acceptances per 100:** V2.2 reaches **5.42** (vs Greedy: 5.18, a +4.6% relative improvement).
* **Inference Speed:** V2.2 runs in **18.66s** (32.3% faster than Greedy: 27.58s).

### 12. Summary of Personal Contribution
* Transformed unstructured synthetic JSONL logs into a clean, reproducible pair-level analytical pipeline.
* Uncovered the crucial Information Bottleneck that guided the development of Policy V2.2.
* Designed the mathematical metrics that improved mutual acceptance, protected scarce candidates, and ensured compliance with all offline execution limits.
