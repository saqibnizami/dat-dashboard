SELECT
	DATE_TRUNC('day', cart_created_date) AS cart_created_date, 
	(COUNT(DISTINCT cart_id)) AS cart_number,
	program AS program
FROM (
	SELECT
	id AS cart_id,
	insurance_id,
	COALESCE(prescription_id, order_id) AS order_id_modified,
	created_at AS cart_created_date,
	program,
	product,
	eligibility,
	source
	FROM
	roadrunner.cart_view) AS base
{}
GROUP BY
	DATE_TRUNC('day', cart_created_date), program
ORDER BY
	DATE_TRUNC('day', cart_created_date)
	DESC