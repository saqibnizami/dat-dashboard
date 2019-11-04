SELECT
    id AS bill_id,
    order_id,
    billing_date AT TIME ZONE 'America/Los_Angeles' AS billing_date,
    product,
    resubmitted
FROM billing_views.claims
WHERE billing_date > '2017-12-31'
