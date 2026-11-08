-- Page 5: daily KPI series for forecasting and anomaly detection (SIMULATED data)
-- Tracked NDCs come from our own click/postback tracking; reported NDCs come from the operators'
-- reports (one row per NDC). A gap between the two is a tracking problem, not a business change.
-- Missouri launched on 1 Dec 2025 and has no history before that, so it is kept as its own group:
-- the forecast is trained on existing states and Missouri is added once it has enough history.
WITH traffic AS (
    SELECT date, vertical, IF(state = 'MO', 'Missouri', 'Existing states') AS state_group,
           SUM(sessions) AS sessions, SUM(clickouts) AS clickouts
    FROM 'data/simulated/sim_traffic_daily.csv'
    GROUP BY ALL
),
funnel AS (
    SELECT date, vertical, IF(state = 'MO', 'Missouri', 'Existing states') AS state_group,
           SUM(registrations) AS registrations, SUM(ndcs_tracked) AS ndcs_tracked
    FROM 'data/simulated/sim_operator_daily.csv'
    GROUP BY ALL
),
reported AS (
    SELECT ftd_date AS date, vertical, IF(state = 'MO', 'Missouri', 'Existing states') AS state_group,
           COUNT(*) AS ndcs_reported
    FROM 'data/simulated/sim_ndc_players.csv'
    GROUP BY ALL
)
SELECT t.date, t.vertical, t.state_group, t.sessions, t.clickouts,
       COALESCE(f.registrations, 0)  AS registrations,
       COALESCE(f.ndcs_tracked, 0)   AS ndcs_tracked,
       COALESCE(r.ndcs_reported, 0)  AS ndcs_reported
FROM traffic t
LEFT JOIN funnel f USING (date, vertical, state_group)
LEFT JOIN reported r USING (date, vertical, state_group)
ORDER BY t.date, t.vertical, t.state_group;
