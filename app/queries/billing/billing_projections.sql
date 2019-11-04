SELECT *, COUNT(prediction) as counts

FROM (SELECT
    CASE
        WHEN ((created_at + interval '45' day) >= CAST({start_date} as date)) AND (latest_date < cast({end_date} as date)) THEN 'lower_bound'
        WHEN (earliest_date < cast({end_date} as date)) AND (latest_date > cast({end_date} as date)) THEN 'upper_bound'
        ELSE null
    END AS prediction
FROM 
    (SELECT 
        id,
        created_at,
        created_at + interval '17' day as earliest_date,
        created_at + interval '52' day as latest_date
     FROM  orders.orders_view 
        WHERE state = 'APPROVED' 
    ) as o

) as b GROUP BY 1