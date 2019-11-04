SELECT
	DATE_TRUNC({}, created_at)::date AS created,
	state,
	count(DISTINCT id)
FROM
	orders.orders_view
GROUP BY
	state, created
ORDER BY
	created DESC