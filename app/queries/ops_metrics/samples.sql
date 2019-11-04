SELECT
    s.received AS sample_received,
    s.id AS sample_id,
    k.kit_type AS product
FROM ubiome.samples AS s
INNER JOIN ubiome.kits AS k ON k.barcode = s.kit_barcode
WHERE k.barcode NOT LIKE 'study-%' AND s.received > '2017-12-31'
