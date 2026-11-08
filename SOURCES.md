# Sources

Every public figure in `data/public/affiliates_public.csv` comes from a primary company document (regulatory filing or official release). `source_id` in the CSV maps to the rows below. Figures were checked on 2026-11-08.

| source_id | Document | Publisher / date | Link |
|---|---|---|---|
| GAMB-20F-2025 | Gambling.com Group Ltd, Form 20-F for fiscal year 2025 (Note 19 "Revenue", XBRL pages R25, R111-R114; Item 4.B "Financial highlights" and "Marketing") | SEC EDGAR, filed 2026-03-19, accession 0001839799-26-000048 | https://www.sec.gov/Archives/edgar/data/1839799/000183979926000048/gamb-20251231.htm |
| GAMB-FY2024-PR | Gambling.com Group, Q4 and full-year 2024 results (Exhibit 99.1 to Form 6-K), used to cross-check FY2023-FY2024 | SEC EDGAR, 2025-03-20 | https://www.sec.gov/Archives/edgar/data/1839799/000183979925000020/gamb-q42024xpressrelease.htm |
| BETCO-Q1-2025 | Better Collective reports Q1 2025 (regulatory release 19/2025) | MFN, 2025-05-21 | https://mfn.se/a/better-collective/better-collective-reports-q1-2025 |
| BETCO-Q2-2025 | Better Collective reports Q2 2025 (regulatory release 36/2025) | MFN, 2025-08-20 | https://mfn.se/a/better-collective/better-collective-reports-q2-2025 |
| BETCO-Q3-2025 | Better Collective reports Q3 2025 (regulatory release 52/2025) | MFN, 2025-11-12 | https://mfn.se/a/better-collective/better-collective-reports-q3-2025 |
| BETCO-AR-2025 | Better Collective Annual Report 2025 release (regulatory release 12/2026) | MFN, 2026-02-25 | https://www.mfn.se/a/better-collective/better-collective-annual-report-2025 |
| BETCO-AR-2025-PDF | Better Collective Annual Report 2025, full PDF: p.17 (Q4 NDCs, 73% revenue share), p.21 (key figures table, NDCs 2021-2025), p.22 (2025 revenue mix), p.138 (Note 3, revenue by type and geographical segment, tEUR) | bettercollective.com, 2026-02-25 (local copy in `data/raw/`, not committed) | https://bettercollective.com/wp-content/uploads/2026/02/Annual-Report-2025_Better-Collective.pdf |
| BETCO-WEBCAST-2025 | Better Collective Annual Report 2025 webcast presentation (slides 6 and 16) | bettercollective.com, 2026-02-26 | https://bettercollective.com/wp-content/uploads/2026/02/260226_Annual-Report-2025_Webcast.pdf |
| CTM-YE-2025 | Catena Media, Year-End Report January-December 2025 (press release) | GlobeNewswire, 2026-02-10 (reprinted by finanznachrichten.de) | https://www.finanznachrichten.de/nachrichten-2026-02/67664742-catena-media-p-l-c-a-solid-quarter-of-revenue-growth-and-improved-profitability-399.htm |

## Company context (not used as data)

| Fact | Source |
|---|---|
| Growth Leads was renamed PLAYERSBEST; contacts and agreements unchanged | https://www.playersbest.com/rebrand/ |
| Lead generation for iGaming: organic search & SEO (comparison and news sites), paid media (search, social, in-app), publisher solutions, streaming & creators; address in Ta' Xbiex, Malta | https://www.playersbest.com/ |
| Better Collective lists "prediction markets" among its 2026 tailwinds (slides 5 and 16) | BETCO-WEBCAST-2025 |

## A/B test dataset (page 4)

| source_id | Dataset | Notes |
|---|---|---|
| AB-KAGGLE | "A/B testing" by Luyuan Zhang, file `ab_data.csv` (294,478 rows; columns user_id, timestamp, group, landing_page, converted; 2017-01-02 to 2017-01-24) | Public dataset widely used in a Udacity course; its origin is not documented, so the report labels it "PUBLIC DATASET" rather than real company data. Not redistributed here (no licence stated): download it from https://www.kaggle.com/datasets/zhangluyuan/ab-testing and place it in `data/raw/`. Cleaning: 3,893 rows where group and landing page disagree are removed, then 1 duplicated user, leaving 290,584 users. |

## Notes on definitions

- **NDC** (new depositing customer): "a unique referral of a player from our system to one of our customers that satisfied an agreed performance obligation (typically making a deposit above a minimum threshold)" (Gambling.com Group 20-F).
- **CPA / revenue share / hybrid**: CPA is a single cash payment per referred player; revenue share is a percentage of the net gaming revenue (NGR) of referred players; hybrid combines both (Gambling.com Group 20-F, Note 19).
- Gambling.com Group reports "more than 454,000 and 479,000 new customers" referred in 2025 and 2024. Revenue per referred customer in this study divides performance-marketing revenue by these counts, so it is an upper-bound estimate.
- Gambling.com Group's CPA / revenue share / hybrid split is a percentage of **performance-marketing** revenue, not of total revenue.
- Better Collective's Note 3 (p.138) splits revenue by type and region: in 2025, revenue share was 55% of Europe & RoW revenue but 24% of North America revenue. Its slides quote "17 mEUR pure revenue share" for North America, while Note 3 shows 22.3 mEUR in the "Revenue Share" line; the study uses the Note 3 figure and keeps both definitions apart.
- Better Collective's quarterly revenue-share percentages (80%, 86%, 81%, 73%) are a share of **NDCs**, not of revenue. The two companies' mixes are therefore not directly comparable, and the report says so.

## Simulated data

All files in `data/simulated/` are generated by `src/simulate.py` with a fixed seed. They are calibrated on the public benchmarks above where possible and are labelled SIMULATED on every report page.

Independent case study, not affiliated with PLAYERSBEST (formerly Growth Leads).
