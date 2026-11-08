-- Page 4: clean the public landing-page A/B test (ab_data.csv) before testing it
-- 1. drop rows where the assigned group and the page shown disagree (treatment must see new_page)
-- 2. keep one row per user (first exposure)
WITH raw AS (
    SELECT * RENAME ("group" AS group_name)        -- "group" is a reserved SQL word
    FROM 'data/raw/ab_data.csv'
),
consistent AS (
    SELECT *
    FROM raw
    WHERE (group_name = 'treatment') = (landing_page = 'new_page')
),
first_exposure AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY timestamp) AS rn
    FROM consistent
)
SELECT user_id, CAST(timestamp AS TIMESTAMP) AS ts, group_name, landing_page, converted
FROM first_exposure
WHERE rn = 1
ORDER BY ts;
