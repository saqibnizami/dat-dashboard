SELECT COUNT (DISTINCT id) as count_claims_submitted
FROM (
SELECT
 	id,
 	billing_date AT TIME ZONE 'America/Los_Angeles' AS billing_date,
 	product,
 	resubmitted
FROM billing_views.claims
WHERE (resubmitted IS null OR resubmitted = false)
AND billing_date between date {start_date} and date {end_date}
AND product in ({clinical_products})
) AS count_claims_submitted