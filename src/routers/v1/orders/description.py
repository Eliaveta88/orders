"""Description strings for orders endpoints."""

LIST_ORDERS_DESC = (
    "Retrieve list of orders with pagination and filtering. "
    "Shows order ID, client, amount, status, and date. "
    "Action: LIST_ORDERS"
)

GET_ORDER_DESC = (
    "Get detailed order information including items, totals, and delivery info. "
    "Shows all line items and integration points. "
    "Action: GET_ORDER"
)

CREATE_ORDER_DESC = (
    "Create new order from client request. "
    "Validates client, items, and quantities. "
    "Initiates stock reservation and delivery planning. "
    "Action: CREATE_ORDER"
)

UPDATE_ORDER_STATUS_DESC = (
    "Update order status in lifecycle pipeline. "
    "Supports: draft, confirmed, in_delivery, closed, cancelled. "
    "Action: UPDATE_ORDER_STATUS"
)
