SELECT
date_trunc('week', cart_created_date) AS cart_created_date,
program_category,
COUNT(DISTINCT drop_use_this_for_join) AS kit1_count_of_orders_generated
FROM
(SELECT
	cart.cart_id, 
    cart.product, 
    cart.cart_created_date, 
    cart.program, 
    cart.eligibility, 
    cart.source,
	otype.clinical_type_name, 
    o.*, 
    ometa.order_metadata, 
    ds.ship_date, 
    ds.delivered_date, 
    date_diff('day', ds.delivered_date, samples.sample_received_date) as kit_received_time_in_days, 
    -- billing_entities.*,
	CASE
        WHEN program = 'pap' THEN '1. pap'
        WHEN program = 'cash_pay_program' THEN '2. cash_pay_program'
        WHEN program = 'patient_responsibility' THEN '3. patient_responsibility'
    ELSE '4. legacy_or_misc_programs'
    END AS program_category,
    CASE
        WHEN o.prescription_id is null and o.order_id is null THEN null
        WHEN o.prescription_id is not null THEN row_number() OVER (PARTITION BY o.prescription_id ORDER BY ds.delivered_date, o.order_created_at)
        WHEN o.prescription_id is null THEN 1
        ELSE 1
    END AS kit_number,
    CASE
        WHEN o.order_id is null then null
        WHEN cardinality(filter(ometa.order_metadata, x -> x like '%Upgraded from%')) > 0 THEN 'Upgrade'
        WHEN cardinality(filter(ometa.order_metadata, x -> x like '%%Explorer upgrade%%')) > 0 THEN 'Upgrade'
        WHEN o.prescription_id is not null THEN 'Multi Kit'
        ELSE 'Single Kit'
    END AS mk_upg_stat,
    CASE
        WHEN o.order_id is null THEN null
        WHEN o.sample_id is not null THEN 'Sample Received'
        ELSE 'Sample Not Received'
    END AS sample_receival_stat


FROM

(SELECT
	owner_id,
	COALESCE(prescription_id, id) AS drop_use_this_for_join,
	prescription_id,
	id AS order_id,
	created_at AS order_created_at,
	order_flow,
	state AS order_state,
	insurance_id AS insurance_id,
	sample_id,
	delivery_id,
	order_type_id,
	billed AS billed_stat
FROM orders.orders_view) AS o

LEFT JOIN
(SELECT
    id AS order_type_id,
    clinical_type_name
FROM orders.order_type_view
) AS otype 
ON o.order_type_id = otype.order_type_id

LEFT JOIN
(SELECT
	order_id,
	array_agg(value) as order_metadata
FROM orders.order_metadata_view
GROUP BY order_id) AS ometa 
on ometa.order_id = o.order_id

LEFT JOIN
(SELECT
	order_id AS delivery_id,
	carrier_code,
	service_code,
	tracking_number,
	created_at AS kit_shipment_created_at,
	ship_date,
	delivered_date,
	tracking_status AS shipment_tracking_status
FROM delivery.shipment_view
WHERE type = 'NORMAL'
) AS ds
ON o.delivery_id = ds.delivery_id

-- LEFT JOIN
-- (SELECT
-- 	iv.id as drop_insurance_id,
-- 	iv.insurance_type,
-- 	iv.plan_number,
-- 	iv.plan_description,
-- 	iv.group_number,
-- 	iv.group_description,
-- 	sv.subscriber_id,
-- 	sv.company_id,
-- 	sv.company_name,
-- 	sv.first_name,
-- 	sv.last_name,
-- 	sv.birthdate,
-- 	sv.subscriber_relation,
-- 	sv.gender,
-- 	sv.subscriber_address_id
-- FROM billing.billing_entities.insurances_view AS iv
-- LEFT JOIN billing.billing_entities.subscriber_view sv on sv.insurance_id = iv.id) AS billing_entities
-- ON o.insurance_id = billing_entities.drop_insurance_id

-- RIGHT JOIN
-- (SELECT
-- 	id AS cart_id,
-- 	insurance_id,
-- 	COALESCE(prescription_id, order_id) AS drop_use_this_for_join,
-- 	created_at as cart_created_date,
-- 	program,
-- 	product,
-- 	eligibility,
-- 	source
-- FROM products.roadrunner.cart_view) AS cart
-- ON o.drop_use_this_for_join = cart.drop_use_this_for_join

-- LEFT JOIN (
--             SELECT
--                     id AS sample_id,
--                     experiment as experiment_id,
--                     vial_barcode,
--                     kit_barcode,
--                     arrived AS sample_arrived_at_lab_date,
--                     received AS sample_accessioned_date,
--                     created AS sample_record_created,
--                     COALESCE(received, arrived) AS sample_received_date,
--                     accessioning_issues,
--                     accessioning_comments,
--                     upgraded_to_clinical
--             FROM mysql.ubiome.samples
--             ORDER BY sample_received_date DESC
-- ) AS samples
-- ON o.sample_id = samples.sample_id

) AS base
WHERE cart_created_date >= date_trunc('week', now()-interval '31' day)
AND source is not null
-- [[AND cart_created_date >= {{cart_created_start}}]]
-- [[AND cart_created_date < {{cart_created_end}}]]
-- [[AND REPLACE(UPPER(product), '_', '') = REPLACE(UPPER({{product}}), '_', '')]]
GROUP BY date_trunc('week', cart_created_date), program_category