SELECT *
FROM
(
    SELECT
        zc.claim_id,
        zc.charges as charge,
        se.allowed as allowed,
        se.net_payment as payment,
        se.coinsurance as coinsurance,
        se.deductible as deductible,
        se.production_date,
        se.issue_date,
        c.product,
        c.version,
        c.order_id,
        row_number() over (partition by zc.claim_id order by se.production_date desc) rk
    from billing_views.zirmed_claims zc
    inner join billing_views.dc_zirmed_claims dc on dc.zirmed_claims_id = zc.id
    inner join billing_views.claims c on c.order_id = dc.order_id and date(c.billing_date) > date('2010-01-01')
    left join collections.simplified_eobs se on se.zc_id = zc.id
    where se.issue_date > '2017-12-31'
    group by 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11) AS data
WHERE rk = 1
