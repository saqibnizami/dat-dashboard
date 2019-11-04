-- Checkout Completion Volume
-- -- created March 2019, Saqib Nizami, Data Analytics Team 
-- Lay Definition: Site visitors that complete a test request or test purchase
-- Technical Definition: Carts with an order_id (SingleKit) or a prescription_id (MultiKit)
SELECT 
        *
FROM
    (
    SELECT
        c.created_date,
        -- sum(c.completed) as completed_carts,
        coalesce(c.prescription_id, c.order_id) as order_id_coalesced,
        c.product,
        c.mk_sk
    FROM
        (
        SELECT
            -- frequency values can be 'day', 'week', 'month'
            cast(date_trunc({{frequency}}, cart.created_at) as date) AS created_date,
            *
        FROM
            (
            -- this block selects 
            SELECT
                *,
                CASE WHEN prescription_id IS NOT NULL THEN 'MultiKit' ELSE 'SingleKit' END AS mk_sk
            FROM
                postgresql_products.roadrunner.cart_view AS c
            WHERE
                (EXTRACT(year from created_at) = EXTRACT(year from CURRENT_DATE))
            AND 
                (c.order_id IS NOT NULL OR c.prescription_id IS NOT NULL)

            ) as cart
        WHERE 
            (mk_sk LIKE 'SingleKit' OR mk_sk LIKE 'MultiKit')

        ) AS c
    ) as carts
LEFT JOIN
    (
    SELECT 
            orders.id,
            orders.prescription_id,
            COALESCE(orders.prescription_id, orders.id) AS order_id_coalesced,
            orders.created_at,
            orders.state,
            orders.order_flow,
            tracking.utm_source,
            tracking.utm_medium,
            ometa.order_meta_values,
            -- Map Paid Acquisition Sources
            CASE
                WHEN (tracking.utm_source LIKE 'facebook' 
                        AND tracking.utm_medium LIKE 'paid_social') 
                    THEN 'Online Performance Marketing'
                WHEN (tracking.utm_source LIKE 'facebook' 
                        AND tracking.utm_medium LIKE 'paid') 
                    THEN 'Online Performance Marketing'
                WHEN (tracking.utm_source LIKE 'facebook' 
                        AND tracking.utm_medium LIKE 'cpc') 
                    THEN 'Online Performance Marketing'
                WHEN (tracking.utm_source LIKE 'google' 
                        AND tracking.utm_medium LIKE 'cpc')
                    THEN 'Online Performance Marketing'
                WHEN (tracking.utm_source LIKE 'bing' 
                        AND tracking.utm_medium LIKE 'cpc')
                    THEN 'Online Performance Marketing'
                WHEN (tracking.utm_source LIKE 'SmartGut' 
                        AND tracking.utm_medium LIKE 'email') 
                    THEN 'Online Performance Marketing'
                WHEN (tracking.utm_source LIKE 'SmartJane' 
                        AND tracking.utm_medium LIKE 'email') 
                    THEN 'Online Performance Marketing'
                WHEN (tracking.utm_source LIKE 'Explorer' 
                        AND tracking.utm_medium LIKE 'email') 
                    THEN 'Online Performance Marketing'
                WHEN (tracking.utm_source LIKE 'Blog' 
                        AND tracking.utm_medium LIKE 'email') 
                    THEN 'Online Performance Marketing'
            END AS mapped_category,
            -- Indicator column for upgrades
            CASE
                WHEN contains(ometa.order_meta_values, 'Explorer Upgrade') 
                    THEN 'Upgrade'
                WHEN contains(ometa.order_meta_values, 'Upgraded from SGv1') 
                    THEN 'Upgrade'
                WHEN contains(ometa.order_meta_values, 'Upgraded from SJv1') 
                    THEN 'Upgrade'
                WHEN contains(ometa.order_meta_values, 'Upgraded from SGv2') 
                    THEN 'Upgrade'
                WHEN contains(ometa.order_meta_values, 'Upgraded from SJv2') 
                    THEN 'Upgrade'
                WHEN contains(ometa.order_meta_values, 'Upgraded from SGv3') 
                    THEN 'Upgrade'
                WHEN contains(ometa.order_meta_values, 'Upgraded from SJv3') 
                    THEN 'Upgrade'
                END AS upg_status
    FROM
            postgresql.orders.orders_view AS orders
    LEFT JOIN 
            postgresql.orders.tracking_info AS tracking
            ON orders.id = tracking.order_id
    LEFT JOIN
            (
            SELECT
                    m.order_id, 
                    m.order_meta_values 
            FROM 
                (
                SELECT
                        order_id, 
                        array_agg(value) AS order_meta_values 
                FROM
                        postgresql.orders.order_metadata_view 
                GROUP BY 
                        order_id
                ) AS m
            ) AS ometa
        ON orders.id = ometa.order_id
    ) as o
    ON carts.order_id_coalesced = o.order_id_coalesced
-- WHERE order_meta_values is not null
LIMIT 20