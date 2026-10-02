PRODUCT = {
    "type": "object",
    "required": ["id", "name", "price", "stock"],
    "properties": {"id": {"type": "integer"}, "name": {"type": "string", "minLength": 1},
                   "price": {"type": "number", "minimum": 0}, "stock": {"type": "integer", "minimum": 0}},
    "additionalProperties": False,
}
PRODUCT_LIST = {"type": "array", "minItems": 1, "items": PRODUCT}
LOGIN = {"type": "object", "required": ["token", "user_id", "username"],
         "properties": {"token": {"type": "string"}, "user_id": {"type": "integer"},
                        "username": {"type": "string"}}}
ORDER_CREATED = {"type": "object", "required": ["order_id", "total", "status"],
                 "properties": {"order_id": {"type": "integer"}, "total": {"type": "number"},
                                "status": {"enum": ["PLACED"]}}}
ORDER = {"type": "object", "required": ["order_id", "total", "status", "items"],
         "properties": {"items": {"type": "array", "minItems": 1, "items": {
             "type": "object", "required": ["product_id", "quantity", "unit_price"]}}}}
