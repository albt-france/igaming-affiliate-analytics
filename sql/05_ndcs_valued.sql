-- One row per NDC with its 12-month affiliate revenue under the operator's current deal (SIMULATED).
-- Same valuation as 01_channel_page_epc.sql; revenue_12m_usd is NULL for cohorts after Aug 2025,
-- whose first 12 months are not fully observed yet. Feeds the Power BI NDCs table.
WITH ngr12 AS (
    SELECT ndc_id, GREATEST(SUM(ngr_usd), 0) AS ngr_12m
    FROM 'data/simulated/sim_ndc_monthly_ngr.csv'
    WHERE month_n <= 12
    GROUP BY ndc_id
)
SELECT p.ndc_id, p.ftd_date, p.channel, p.state, p.page_type, p.vertical, p.operator,
       CASE WHEN p.ftd_date <= DATE '2025-08-31' THEN
           ROUND(CASE d.current_deal
                     WHEN 'CPA'           THEN d.cpa_offer_usd
                     WHEN 'Revenue share' THEN d.revshare_offer_pct * COALESCE(n.ngr_12m, 0)
                     WHEN 'Hybrid'        THEN d.hybrid_cpa_usd + d.hybrid_revshare_pct * COALESCE(n.ngr_12m, 0)
                 END, 2)
       END AS revenue_12m_usd
FROM 'data/simulated/sim_ndc_players.csv' p
JOIN 'data/simulated/sim_operator_deals.csv' d USING (operator)
LEFT JOIN ngr12 n USING (ndc_id)
ORDER BY p.ndc_id;
