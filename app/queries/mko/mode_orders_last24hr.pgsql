SELECT DATE_TRUNC('hour', o2.created_at) AS created_at_hour,
       o2.clinical_type_name,
       mk_upg_stat,
       o2.upgrade_stat,
       o2.multikit_stat,
       o2.order_channel,
       o2.order_flow,
       utm_fillna,
       COUNT(DISTINCT(o2.id)) AS count_order_id,
       COUNT(DISTINCT(o2.order_id_modified)) AS count_order_kit1only
FROM
  (SELECT *,
          CASE
              WHEN lower(o.order_meta_values) like '%upgraded from%' THEN 'Upgrade'
              WHEN lower(o.order_meta_values) like '%explorer upgrade%' THEN 'Upgrade'
              WHEN prescription_id is not null THEN 'Multi Kit'
              ELSE 'Single Kit'
          END AS mk_upg_stat,
          CASE
              WHEN lower(o.order_meta_values) like '%upgraded from %v1%' THEN 'V1 to V2 Upgrade'
              WHEN lower(o.order_meta_values) like '%upgraded from %v2%' THEN 'V2 to V3 Upgrade'
              WHEN lower(o.order_meta_values) like '%upgraded from %v3%' THEN 'V3 to V4 Upgrade'
              WHEN lower(o.order_meta_values) like '%upgraded from %v4%' THEN 'V4 to V5 Upgrade'
              WHEN lower(o.order_meta_values) like '%explorer upgrade%' THEN 'Exp to Clinical Upgrade'
              WHEN lower(o.order_meta_values) like '%upgraded from%' THEN 'Other Upgrade'
              WHEN lower(o.order_meta_values) like '%explorer upgrade%' THEN 'Other Upgrade'
              ELSE 'Nonupgrade'
          END AS upg_details,
          CASE
              WHEN lower(o.order_meta_values) like '%upgraded from%' THEN 'Upgrade'
              WHEN lower(o.order_meta_values) like '%explorer upgrade%' THEN 'Upgrade'
              ELSE 'Nonupgrade'
          END AS upgrade_stat,
          CASE
              WHEN o.prescription_id is null THEN o.id
              ELSE o.prescription_id
          END AS order_id_modified,
          CASE
              WHEN o.order_flow is null THEN 'Patient Initiated'
              WHEN o.order_flow = 'patient_doctor_ubiome' THEN 'Patient Initiated'
              WHEN o.order_flow = 'patient_doctor_none' THEN 'Patient Initiated'
              WHEN o.order_flow = 'patient_doctor_selected' THEN 'Patient Initiated'
              WHEN o.order_flow = 'prescripted_orders' THEN 'Patient Initiated'
              WHEN o.order_flow = 'free_of_approval' THEN 'No Insurance'
              WHEN o.order_flow = 'trf_transcribed' THEN 'Doctor Initiated'
              WHEN o.order_flow = 'doctor_transcribed' THEN 'Doctor Initiated'
              WHEN o.order_flow = 'emr_trascribed' THEN 'Doctor Initiated'
              WHEN o.order_flow = 'reflex_orders' THEN 'Doctor Initiated'
              ELSE 'Channel Undefined'
          END AS order_channel,
          CASE
              WHEN o.state = 'REJECTED' THEN 'Order Rejected'
              WHEN o.state = 'REJECTED_BY_UBIOME' THEN 'Order Rejected'
              WHEN o.state = 'CANCELLED' THEN 'Order Cancelled'
              WHEN o.state = 'CANCELLED_BY_PATIENT' THEN 'Order Cancelled'
              WHEN o.state = 'DRAFT' THEN 'Legacy Draft Orders'
              WHEN lower(o.order_meta_values) like '%sample received%' THEN 'Sample Received'
              WHEN o.state = 'RECEIVED' THEN 'Sample Received'
              WHEN o.state = 'RELEASED' THEN 'Sample Received'
              WHEN o.state = 'RECOLLECTED' THEN 'Sample Received'
              WHEN o.state = 'APPROVED' THEN 'Sample Not Returned'
              WHEN o.state = 'CREATED' THEN 'Sample Not Returned'
              WHEN o.state = 'PATIENT_PENDING_VALID_INSURANCE' THEN 'Sample Not Returned'
              WHEN o.state = 'PENDING_ELIGIBILITY_CHECK' THEN 'Sample Not Returned'
              WHEN o.state = 'PENDING_PATIENT_INFO' THEN 'Sample Not Returned'
              WHEN o.state = 'PENDING_MANUAL_ELIGIBILITY_CHECK' THEN 'Sample Not Returned'
              WHEN o.state = 'WAITING_FOR_PAYMENT' THEN 'Sample Not Returned'
              ELSE 'Case Undefined'
          END AS sample_receival_stat,
          CASE
              WHEN o.state = 'PATIENT_PENDING_VALID_INSURANCE' THEN 'Orders Pending Action Items'
              WHEN o.state = 'PENDING_ELIGIBILITY_CHECK' THEN 'Orders Pending Action Items'
              WHEN o.state = 'PENDING_PATIENT_INFO' THEN 'Orders Pending Action Items'
              WHEN o.state = 'PENDING_MANUAL_ELIGIBILITY_CHECK' THEN 'Orders Pending Action Items'
              WHEN o.state = 'WAITING_FOR_PAYMENT' THEN 'Orders Pending Action Items'
              ELSE 'No Pending Items'
          END AS pending_items,
          CASE
              WHEN o.state = 'REJECTED' THEN 'Misc.'
              WHEN o.state = 'REJECTED_BY_UBIOME' THEN 'Misc.'
              WHEN o.state = 'CANCELLED' THEN 'Misc.'
              WHEN o.state = 'CANCELLED_BY_PATIENT' THEN 'Misc.'
              WHEN o.state = 'DRAFT' THEN 'Misc.'
              WHEN o.billed is true THEN '6. Orders that are billed'
              WHEN lower(o.order_meta_values) like '%sample received%' THEN '5. Orders that received Samples'
              WHEN o.state = 'RECEIVED' THEN '5. Orders that received Samples'
              WHEN o.state = 'RELEASED' THEN '5. Orders that received Samples'
              WHEN o.state = 'RECOLLECTED' THEN '5. Orders that received Samples'
              WHEN o.delivery_id is not null THEN '4. Orders that shipped Kits'
              WHEN o.state = 'PATIENT_PENDING_VALID_INSURANCE' THEN '3. Orders Pending Action Items'
              WHEN o.state = 'PENDING_ELIGIBILITY_CHECK' THEN '3. Orders Pending Action Items'
              WHEN o.state = 'PENDING_PATIENT_INFO' THEN '3. Orders Pending Action Items'
              WHEN o.state = 'PENDING_MANUAL_ELIGIBILITY_CHECK' THEN '3. Orders Pending Action Items'
              WHEN o.state = 'WAITING_FOR_PAYMENT' THEN '3. Orders Pending Action Items'
              WHEN o.prescription_id is not null
                   AND o.state = 'APPROVED' THEN '2. Orders in Multikit in Queue'
              ELSE '1. Orders'
          END AS order_funnel,
          CASE
              WHEN utm_source is null
                   AND created_at < '2018-09-20' THEN 'Before UTM Integration'
              WHEN utm_source is null AND utm_medium is not null THEN utm_medium
              WHEN utm_source is null AND lower(o.order_meta_values) like '%upgraded from%' THEN 'Upgrades with no UTM'
              WHEN utm_source is null AND lower(o.order_meta_values) like '%explorer upgrade%' THEN 'Upgrades with no UTM'
              WHEN utm_source is null AND lower(o.order_meta_values) like '%vip%' THEN 'Other Backend Generated Orders (VIP, NTRF)'
              WHEN utm_source is null AND lower(o.order_meta_values) like '%ntrf%' THEN 'Other Backend Generated Orders (VIP, NTRF)'
              WHEN utm_source is null AND lower(o.order_meta_values) like '%recollected_from%' THEN 'Other Backend Generated Orders (VIP, NTRF, etc)'
              WHEN utm_source is null AND lower(o.order_meta_values) like '%kit_barcode_replaced%' THEN 'Other Backend Generated Orders (VIP, NTRF, etc)'
              WHEN utm_source is null AND o.order_flow = 'trf_transcribed' THEN 'HCP initiated orders with no UTM'
              WHEN utm_source is null AND o.order_flow = 'doctor_transcribed' THEN 'HCP initiated orders with no UTM'
              WHEN utm_source is null AND o.order_flow = 'emr_trascribed' THEN 'HCP initiated orders with no UTM'
              WHEN utm_source is null AND o.order_flow = 'reflex_orders' THEN 'HCP initiated orders with no UTM'
              WHEN utm_source is null THEN 'No UTM Source'
              WHEN utm_source = 'google' THEN 'google'
              WHEN utm_source = 'facebook' THEN 'facebook'
              ELSE utm_medium
          END AS utm_fillna
   FROM
       (SELECT *
      FROM
          (SELECT *,
                  extract(year
                          FROM created_at) AS created_year,
                  CASE
                      WHEN prescription_id is null THEN 'Single Kit'
                      ELSE 'Multi Kit'
                  END AS multikit_stat
         FROM orders.orders) o_temp
      LEFT JOIN
        (SELECT m.order_id,
                m.order_meta_values
         FROM
           (SELECT order_id,
                   string_agg(value, ', ') AS order_meta_values
            FROM orders.order_metadata
            GROUP BY order_id) AS m) AS ometa
        ON o_temp.id = ometa.order_id
      LEFT JOIN
        (SELECT order_id,
                utm_source,
                utm_medium,
                utm_campaign,
                utm_term,
                utm_content
         FROM orders.tracking_info) AS utm
        ON o_temp.id::varchar = utm.order_id::varchar) AS o
   LEFT JOIN
     (SELECT id AS order_type_id,
             clinical_type_name
      FROM orders.order_type) AS otype
     ON o.order_type_id = otype.order_type_id) AS o2
WHERE o2.state not in ('DRAFT',
                       'PENDING_PATIENT_INFO',
                       'REJECTED_BY_UBIOME')
  AND NOW() > o2.created_at::timestamptz
  AND NOW() - o2.created_at::timestamptz <= interval '24 hours'
GROUP BY DATE_TRUNC('hour', o2.created_at),
         o2.clinical_type_name,
         mk_upg_stat,
         o2.upgrade_stat,
         o2.multikit_stat,
         o2.order_channel,
         o2.order_flow,
         utm_fillna
ORDER BY DATE_TRUNC('hour', o2.created_at) DESC, o2.clinical_type_name,
                                                 mk_upg_stat,
                                                 o2.upgrade_stat,
                                                 o2.multikit_stat,
                                                 o2.order_channel,
                                                 o2.order_flow,
                                                 utm_fillna