	SELECT *
    FROM
    (SELECT
		kit_sent.*,
		kit_return.kit_return_tracking_status,
		kit_return.kit_return_carrier_code,
		kit_return.kit_return_service_code,
		kit_return.kit_return_tracking_number,
		kit_return.kit_return_carrier_id,
		kit_return.kit_return_created_date,
		kit_return.kit_return_ship_date,
		kit_return.kit_return_delivered_date
	FROM (
		SELECT
			order_id AS drop_delivery_id,
			tracking_status AS kit_sent_tracking_status,
			carrier_code AS kit_sent_carrier_code,
			service_code AS kit_sent_service_code,
			tracking_number AS kit_sent_tracking_number,
			carrier_id AS kit_sent_carrier_id,
			created_at AS kit_sent_created_date,
			ship_date AS kit_sent_ship_date,
			delivered_date AS kit_sent_delivered_date
		FROM
			delivery.shipment_view
		WHERE
			TYPE = 'NORMAL') AS kit_sent -- NORMAL IS FROM UBIOME TO PATIENT
	FULL OUTER JOIN (
		SELECT
			*
		FROM (
			SELECT
				order_id AS drop_delivery_id,
				tracking_status AS kit_return_tracking_status,
				carrier_code AS kit_return_carrier_code,
				service_code AS kit_return_service_code,
				tracking_number AS kit_return_tracking_number,
				carrier_id AS kit_return_carrier_id,
				created_at AS kit_return_created_date,
				ship_date AS kit_return_ship_date,
				delivered_date AS kit_return_delivered_date,
				ROW_NUMBER()
				OVER (PARTITION BY
						order_id
					ORDER BY
						delivered_date DESC,
						ship_date DESC,
						created_at DESC) AS rn
				FROM
					delivery.shipment_view
				WHERE
					TYPE = 'RETURN') AS ret -- RETURN IS FROM PATIENT TO UBIOME NOTE THAT I USE RANK TO ONLY HAVE ONE RETURN RECORD (UBIOME PROVIDES TWO OPTIONS FOR RETURN IN SOME CASES)
			WHERE
				rn = 1) AS kit_return ON kit_sent.drop_delivery_id = kit_return.drop_delivery_id) AS kit --ON o.delivery_id = kit.drop_delivery_id