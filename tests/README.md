# Тесты orders

Из корня сервиса (нужен установленный проект и `PYTHONPATH`):

```bash
cd GastroRoute_orders
set PYTHONPATH=src
python -m unittest discover -s tests -p "test*.py" -v
```

Файлы:

- `test_orders_redis_integration.py` — Redis / кэш
- `test_order_list_schema.py` — схема `OrderListResponse` (список заказов, KPI)
