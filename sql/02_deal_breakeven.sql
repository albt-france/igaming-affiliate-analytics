-- Page 3: CPA or revenue share - which deal is worth more per operator, and when does revenue share overtake CPA?
-- (SIMULATED data)
-- Cumulative NGR per NDC by month since first deposit, censoring-safe: a cohort only counts for
-- month n if every player in it could have reached month n before the data cut-off (Aug 2026).
-- Players who churned stay in the denominator with zero NGR, so the curve is "value per NDC acquired".
WITH cohorts AS (
    SELECT ndc_id, operator, vertical, DATE_TRUNC('month', ftd_date) AS ftd_month
    FROM 'data/simulated/sim_ndc_players.csv'
),
months AS (SELECT UNNEST(RANGE(1, 25)) AS month_n),
eligible AS (            -- cohort x month pairs that are fully observed
    SELECT c.ndc_id, c.operator, c.vertical, m.month_n
    FROM cohorts c CROSS JOIN months m
    WHERE c.ftd_month + TO_MONTHS(CAST(m.month_n - 1 AS INTEGER)) <= DATE '2026-08-01'
),
monthly AS (
    SELECT e.operator, e.vertical, e.month_n,
           COUNT(*)                     AS ndcs_observed,
           SUM(COALESCE(g.ngr_usd, 0))  AS ngr_usd
    FROM eligible e
    LEFT JOIN 'data/simulated/sim_ndc_monthly_ngr.csv' g
           ON g.ndc_id = e.ndc_id AND g.month_n = e.month_n
    GROUP BY ALL
),
curve AS (
    SELECT operator, vertical, month_n, ndcs_observed,
           ngr_usd / ndcs_observed AS ngr_per_ndc,
           SUM(ngr_usd / ndcs_observed) OVER (PARTITION BY operator ORDER BY month_n) AS cum_ngr_per_ndc
    FROM monthly
)
SELECT c.operator, c.vertical, d.current_deal, c.month_n, c.ndcs_observed,
       ROUND(c.ngr_per_ndc, 2)                              AS ngr_per_ndc_usd,
       ROUND(c.cum_ngr_per_ndc, 2)                          AS cum_ngr_per_ndc_usd,
       d.cpa_offer_usd,
       d.revshare_offer_pct,
       ROUND(d.revshare_offer_pct * c.cum_ngr_per_ndc, 2)   AS cum_revshare_per_ndc_usd,
       d.revshare_offer_pct * c.cum_ngr_per_ndc >= d.cpa_offer_usd AS revshare_ahead
FROM curve c
JOIN 'data/simulated/sim_operator_deals.csv' d USING (operator)
ORDER BY c.operator, c.month_n;
