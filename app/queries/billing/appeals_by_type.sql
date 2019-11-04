with eobs as (
    select 
        se.zc_id,
        se.production_date,
        se.name as payer_name,
        se.issue_date as issue_date,
        row_number() over (partition by se.zc_id order by se.production_date desc, se.status_code_id asc) rk
    from collections.simplified_eobs se 
)       
select
    coalesce(fa."type", fa."type", 'medical_necessity') as appeal_type,
    
    count(CASE WHEN ds.source_type = 'first_appeal' THEN 1 ELSE NULL END ) as total_first_appeal_sent
    
from billing_views.document_sent ds
left join eobs se on se.zc_id = ds.zirmed_claim_id and se.rk = 1 and se.production_date > (ds.created_at + interval '5' day)
left join billing_views.zirmed_claims zc on ds.zirmed_claim_id = zc.id
inner join billing_views.dc_zirmed_claims dc on dc.zirmed_claims_id = zc.id
inner join billing_views.claims c on c.order_id = dc.order_id and date(c.billing_date) > date('2010-01-01')
left join billing.first_appeal fa on fa.zirmed_claim_id = zc.id
WHERE issue_date between date {start_date} and date {end_date}
AND c.product in ({clinical_products})
group by 1
order by 2 desc
