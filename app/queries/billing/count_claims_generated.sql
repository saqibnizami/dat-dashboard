SELECT COUNT( DISTINCT id) as count_claims_generated
FROM ( 
    SELECT id,
    creation_date AT TIME ZONE 'America/Los_Angeles' AS creation_date,
    product,
    resubmitted
    FROM billing_views.claims
    WHERE creation_date between date {start_date} and date {end_date}
    AND product in ({clinical_products})
    ) AS count_claims_generated