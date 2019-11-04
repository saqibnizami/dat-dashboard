SELECT 
    count(DISTINCT ids) as count_adjudicated,
    sum(payment) as total_payment,
    avg(payment) as avg_payment,
    sum(allowed) as total_allowed,
    avg(allowed) as avg_allowed

FROM (select
    	zc.claim_id as ids,
    	zc.charges as charge,
    	se.allowed as allowed,
    	se.net_payment as payment,
    	se.coinsurance as coinsurance,
    	se.deductible as deductible,
    	se.production_date,
    	se.issue_date,
    	c.product,
    	c.version,
    	row_number() over (partition by zc.claim_id order by se.production_date desc) rk
from billing_views.zirmed_claims zc
inner join billing_views.dc_zirmed_claims dc on dc.zirmed_claims_id = zc.id
inner join billing_views.claims c on c.order_id = dc.order_id and date(c.billing_date) > date('2010-01-01')
left join collections.simplified_eobs se on se.zc_id = zc.id
where se.issue_date between date {start_date} and date {end_date}
and c.product in ({clinical_products})
and c.version in ({version})
group by 1, 2, 3, 4, 5, 6, 7, 8, 9, 10) d
WHERE rk =1