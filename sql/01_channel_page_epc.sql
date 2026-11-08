-- Page 2: which channels and content pages bring NDCs, at what EPC and ROI? (SIMULATED data)
-- Censoring-safe window: NDC cohorts from Sep 2024 to Aug 2025, each valued on its first 12 months,
-- which are fully observed because the data runs to Aug 2026.
-- Affiliate revenue per NDC follows the operator's current deal:
--   CPA            one-off fee
--   Revenue share  % of the player's 12-month NGR (net of losing months, floored at zero)
--   Hybrid         smaller one-off fee + smaller % of NGR
WITH ngr12 AS (
    SELECT ndc_id, GREATEST(SUM(ngr_usd), 0) AS ngr_12m
    FROM 'data/simulated/sim_ndc_monthly_ngr.csv'
    WHERE month_n <= 12
    GROUP BY ndc_id
),
ndc_value AS (
    SELECT p.ndc_id, p.channel, p.page_type, p.vertical, p.operator,
           CASE d.current_deal
                WHEN 'CPA'           THEN d.cpa_offer_usd
                WHEN 'Revenue share' THEN d.revshare_offer_pct * COALESCE(n.ngr_12m, 0)
                WHEN 'Hybrid'        THEN d.hybrid_cpa_usd + d.hybrid_revshare_pct * COALESCE(n.ngr_12m, 0)
           END AS revenue_12m
    FROM 'data/simulated/sim_ndc_players.csv' p
    JOIN 'data/simulated/sim_operator_deals.csv' d USING (operator)
    LEFT JOIN ngr12 n USING (ndc_id)
    WHERE p.ftd_date BETWEEN DATE '2024-09-01' AND DATE '2025-08-31'
),
traffic AS (
    SELECT channel, page_type, SUM(sessions) AS sessions, SUM(clickouts) AS clickouts
    FROM 'data/simulated/sim_traffic_daily.csv'
    WHERE date BETWEEN DATE '2024-09-01' AND DATE '2025-08-31'
    GROUP BY ALL
),
ndcs AS (
    SELECT channel, page_type, COUNT(*) AS ndcs, SUM(revenue_12m) AS revenue_12m
    FROM ndc_value
    GROUP BY ALL
),
cost AS (
    SELECT channel, SUM(spend_usd) AS spend_usd
    FROM 'data/simulated/sim_marketing_cost_daily.csv'
    WHERE date BETWEEN DATE '2024-09-01' AND DATE '2025-08-31'
    GROUP BY ALL
)
SELECT t.channel, t.page_type, t.sessions, t.clickouts,
       COALESCE(n.ndcs, 0)                                  AS ndcs,
       ROUND(t.clickouts / t.sessions, 4)                   AS clickout_rate,
       ROUND(COALESCE(n.ndcs, 0) / NULLIF(t.clickouts, 0), 4) AS ndc_per_clickout,
       ROUND(n.revenue_12m, 0)                              AS revenue_12m_usd,
       ROUND(n.revenue_12m / NULLIF(t.clickouts, 0), 2)     AS epc_usd,      -- earnings per click-out
       ROUND(n.revenue_12m / NULLIF(n.ndcs, 0), 0)          AS revenue_per_ndc_usd,
       -- paid spend is tracked per channel, so it is allocated to pages pro rata of sessions
       ROUND(c.spend_usd * t.sessions / SUM(t.sessions) OVER (PARTITION BY t.channel), 0) AS spend_usd
FROM traffic t
LEFT JOIN ndcs n USING (channel, page_type)
LEFT JOIN cost c USING (channel)
ORDER BY revenue_12m_usd DESC;
