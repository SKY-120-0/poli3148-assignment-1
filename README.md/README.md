# Kyrgyzstan-Tajikistan Border Conflict (2018-2025)

## Project Overview
This report adopts a data-driven analytical approach using ACLED event data (2018–2025) to examine how conflict dynamics evolved over time. By applying a Pre-2023 vs Post-2023 analytical framework, the report argues that the border has shifted from chronic escalation toward a form of “managed stability,” characterised by reduced violence but continued structural tensions.
It combines cleaned event data, exploratory analysis, interactive visualizations, and a simple forecast to examine how conflict intensity has changed over time and what the post‑2023 pattern may imply for near‑term stability.
While existing ACLED analyses already cover conflict trends in the earlier period of 2018–2020, this research places its main focus on the major escalation episodes in 2021 and 2022, as well as the differences between pre‑2023 and post‑2023 dynamics. The goal is to build on prior baseline research and provide a more detailed examination of how conflict evolved through these critical turning points and transitioned into a relatively more stable phase after 2023. The previous ACLED analysis report link: https://acleddata.com/report/everlasting-or-ever-changing-violence-along-kyrgyzstan-tajikistan-border

## Research Motivation
As of March 2025, Kyrgyzstan and Tajikistan signed a historic agreement to officially demarcate their entire 970‑kilometer shared border, marking a major step toward resolving a decades‑long conflict. This agreement aims to address long‑standing disputes over territory, resources, and infrastructure, which were key drivers behind the deadly escalation episodes in 2021 and 2022. This development provides a timely and important context for this research, as it raises the question of whether the agreement reflects a genuine turning point in conflict dynamics or simply a temporary stabilization following years of high-intensity violence.
This project is motivated by the question of whether the post‑2023 reduction in violence reflects a lasting resolution or a temporary de‑escalation, and the need to better understand how conflict dynamics have evolved across different phases—particularly the sharp escalation in 2021–2022 and the apparent stabilization after 2023. By analyzing ACLED event data, the research aims to assess whether recent trends indicate a durable shift toward peace or a fragile “cold peace” that may still be vulnerable to future tensions.

## Data Sources
- ACLED (Armed Conflict Location and Event Data) event data.

## Methodology Overview
- Data cleaning and filtering to Kyrgyzstan and Tajikistan border-related events (see Code/01_data_cleaning.ipynb).
- Key variables retained for the analysis include: event_date, event_type, sub_event_type, actor1, actor2, fatalities, admin1, admin2, latitude, longitude
- Standardized dates and basic quality checks (e.g., missing coordinates, missing fatalities).
- Descriptive analysis of monthly events and fatalities (2018-2025).
- Interactive charts and maps using Plotly/GeoPandas to compare spatial patterns (notably 2021 vs 2022).
- Simple forecasting using a 6-month rolling mean of post-2023 monthly event counts to project 2026-2030 (see Code/02_data_analysis (updated).ipynb).

## Key Findings (Summary)
- Conflict intensity peaks in 2021 and 2022 and declines after 2023, with lower average monthly events and fatalities in the post-2023 period.
- The post-2023 pattern supports a managed stability trajectory rather than durable peace: low-intensity incidents persist but high-fatality events become rare.
- Expected post-2023 event types tilt toward strategic developments, protests, and low-intensity riots rather than sustained battle events.
- The shift from localized incidents (2017-2018) to state-led escalation (2022) and then institutionalized border management (2024-2025) suggests de-escalation alongside entrenched militarized infrastructure.

## Limitations
- Data coverage and reporting bias: ACLED data may undercount events or misclassify event types due to uneven media coverage, especially in remote or politically sensitive border areas. Smaller incidents may be underreported, while larger events receive disproportionate attention.
- Data scope limitation: The dataset used in this project only extends to April 2025, meaning it does not capture the most recent developments. As a result, conclusions about post‑2023 stability may not fully reflect ongoing or future changes.
- Simplified forecasting approach: The forecast is descriptive and based on a 6‑month rolling mean of recent event counts. It does not include external variables (e.g., political agreements, military deployments, or economic conditions), and therefore should be interpreted cautiously.
- Lack of causal analysis: The findings are primarily correlational. While patterns of escalation and de‑escalation are identified, the project does not establish causal mechanisms behind these changes.
- Limited variable scope: The analysis focuses mainly on event frequency, fatalities, and basic actor interactions. Other important dimensions—such as local governance, resource disputes, or informal agreements—are not directly captured in the dataset.
- Dependence on secondary data: All analysis relies on existing ACLED data, meaning any inherent biases or gaps in the original dataset are carried into this project.

## Author
- Name: YAO KI SAN
- HKU Course: POLI 3148, Assignment 1
- Date: 2026-05-01

## Project Structure (Quick Guide)
- Code/01_data_cleaning.ipynb: Data cleaning and preprocessing.
- Code/02_data_analysis (updated).ipynb: Main analysis, visuals, and forecast.
- Code/Interactive_Report.ipynb: Narrative/interactive report draft.
- Data_Raw/: Original ACLED CSV download.
- Data_Processed/: Cleaned dataset used for analysis.
- Output/: Exported figures and outputs (if any).
- ACLED_dashboard.html, central_asia_conflict_map.html: Interactive visual outputs.
