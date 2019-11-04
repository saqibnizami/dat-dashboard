select 
        CAST(billing_date AS date) as billing_date,
        count(o.id) as counts
    FROM 
        (SELECT 
            *
            FROM billing_views.claims c
            WHERE resubmitted IS null OR resubmitted = false
        ) o
WHERE billing_date between date {start_date} and date {end_date}
GROUP BY 1
ORDER BY 1 ASC