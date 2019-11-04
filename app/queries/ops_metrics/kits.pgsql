SELECT
    ship.id AS shipment_id,
    o.order_id AS order_item_id,
    o.item_type_id,
    ship.type,
    ship.ship_date
FROM  delivery.shipment_view AS ship
INNER JOIN delivery.order_item_view AS o on ship.order_id = o.order_id
WHERE o.item_type_id IN ('32708e12-4254-4d46-933a-f44d2ed32f5f', 'd20ee363-ea4c-4411-ab71-cc68e8723670', 'b255e35e-82bf-4436-8195-6c33b0eb9615') AND ship.type = 'NORMAL' AND ship_date > '2017-12-31'
