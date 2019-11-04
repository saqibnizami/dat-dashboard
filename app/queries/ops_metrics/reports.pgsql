SELECT
    o.id AS order_id,
    o.order_type_id,
    flow.id AS status_id,
    flow.status,
    flow.created_at AS report_created_at
FROM orders.orders_view AS o
INNER JOIN orders.order_status_view AS flow ON flow.order_id = o.id AND flow.status = 'RELEASED'
WHERE o.state = 'RELEASED'
