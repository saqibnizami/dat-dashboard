SELECT avg(days_to_billed) AS avg_time_to_submission
FROM ( 
    SELECT id,
    creation_date AT TIME ZONE 'America/Los_Angeles' AS creation_date,
    billing_date AT TIME ZONE 'America/Los_Angeles' AS billing_date,
    product,
    resubmitted,
    (billing_date::date - creation_date::date) AS days_to_billed
    FROM billing_views.claims
    WHERE (resubmitted IS null OR resubmitted = false)
    AND creation_date between date {start_date} and date {end_date}
    AND product in ({clinical_products})
    ) d