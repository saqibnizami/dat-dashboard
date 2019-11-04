SELECT 
    DATE_TRUNC('day', cart_created_date)::date AS cart_created_date, 
    source, 
    ((COUNT(DISTINCT order_id_modified) * 1.0) / COUNT(DISTINCT cart_id)) AS orders_to_cart_ratio
    -- program
FROM
(SELECT
    id AS cart_id,
    insurance_id,
    COALESCE(prescription_id, order_id) AS order_id_modified,
    created_at as cart_created_date,
    program,
    product,
    eligibility,
    source
FROM roadrunner.cart_view) as base
{}
-- WHERE program LIKE '%cash%'
-- [[WHERE cart_created_date >= {{cart_created_start}} AND cart_created_date < {{cart_created_end}}]]
GROUP BY DATE_TRUNC('day', cart_created_date), source --,program
ORDER BY DATE_TRUNC('day', cart_created_date) DESC