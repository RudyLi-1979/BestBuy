# API Endpoint Testing Guide

This document provides testing methods and examples for the UCP Server API endpoints.

## Prerequisites

Ensure the UCP Server is running:
```powershell
cd c:\Users\rudy\AndroidStudioProjects\BestBuy\ucp_server
uvicorn app.main:app --reload --port 58000
# Or: .\start_docker.ps1
```

## API Documentation

Access Swagger UI to view complete API documentation:
- **Swagger UI**: http://localhost:58000/docs
- **ReDoc**: http://localhost:58000/redoc

---

## 1. Products API Testing

### 1.1 Search products by keyword

```powershell
# Search for iPhone
curl "http://localhost:58000/products/search?q=iPhone&page_size=5"

# Search and sort
curl "http://localhost:58000/products/search?q=laptop&page_size=10&sort=salePrice.asc"
```

### 1.2 Query by SKU

```powershell
# Query specific product (requires actual SKU)
curl "http://localhost:58000/products/6428324"
```

### 1.3 Query by UPC

```powershell
# Query by UPC barcode
curl "http://localhost:58000/products/upc/195949038488"
```

### 1.4 Recommended Products

```powershell
# Get recommended products
curl "http://localhost:58000/products/6428324/recommendations"
```

---

## 2. Cart API Testing

### 2.1 Add product to cart

```powershell
curl -X POST "http://localhost:58000/cart/add" `
  -H "Content-Type: application/json" `
  -d '{
    "sku": "6428324",
    "name": "iPhone 15 Pro 128GB",
    "price": 999.99,
    "image_url": "https://example.com/image.jpg",
    "quantity": 1
  }'
```

### 2.2 View cart

```powershell
curl "http://localhost:58000/cart"
```

### 2.3 Update product quantity

```powershell
# Update quantity to 2
curl -X PUT "http://localhost:58000/cart/items/6428324" `
  -H "Content-Type: application/json" `
  -d '{"quantity": 2}'

# Set quantity to 0 to remove product
curl -X PUT "http://localhost:58000/cart/items/6428324" `
  -H "Content-Type: application/json" `
  -d '{"quantity": 0}'
```

### 2.4 Remove product

```powershell
curl -X DELETE "http://localhost:58000/cart/items/6428324"
```

### 2.5 Clear cart

```powershell
curl -X DELETE "http://localhost:58000/cart"
```

---

## 3. Checkout API Testing

### 3.1 Create checkout session

```powershell
# Add product to shopping cart first, then create checkout session
curl -X POST "http://localhost:58000/checkout/session"
```

Example response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "guest_abc123",
  "total_amount": 999.99,
  "created_at": "2026-02-12T10:00:00Z"
}
```

### 3.2 Update Shipping Information

```powershell
# Use the session_id obtained from the previous step
curl -X POST "http://localhost:58000/checkout/session/{session_id}/update" `
  -H "Content-Type: application/json" `
  -d '{
    "shipping_name": "John Doe",
    "shipping_address": "123 Main St, Apt 4B",
    "shipping_city": "New York",
    "shipping_postal_code": "10001",
    "shipping_country": "US"
  }'
```

### 3.3 Complete Checkout

```powershell
# Complete checkout and create order
curl -X POST "http://localhost:58000/checkout/session/{session_id}/complete"
```

Example response:
```json
{
  "id": 1,
  "order_number": "ORD-20260212-001",
  "total_amount": 999.99,
  "status": "confirmed",
  "items": [...]
}
```

---

## 4. Orders API Testing

### 4.1 Query All Orders

```powershell
curl "http://localhost:58000/orders"
```

### 4.2 Query Specific Order

```powershell
# Query by order number
curl "http://localhost:58000/orders/ORD-20260212-001"
```

### 4.3 Update Order Status (Admin Feature)

```powershell
curl -X PUT "http://localhost:58000/orders/ORD-20260212-001/status?status=shipped"
```

Available statuses:
- `pending` - Pending
- `confirmed` - Confirmed
- `processing` - Processing
- `shipped` - Shipped
- `delivered` - Delivered
- `cancelled` - Cancelled

---

## 5. UCP Profile Testing

```powershell
curl "http://localhost:58000/.well-known/ucp"
```

---

## Complete Shopping Workflow Test

Below is a complete shopping workflow example:

```powershell
# 1. Search for products
curl "http://localhost:58000/products/search?q=iPhone"

# 2. Add product to cart
curl -X POST "http://localhost:58000/cart/add" `
  -H "Content-Type: application/json" `
  -d '{
    "sku": "6428324",
    "name": "iPhone 15 Pro",
    "price": 999.99,
    "quantity": 1
  }'

# 3. View cart
curl "http://localhost:58000/cart"

# 4. Create checkout session
curl -X POST "http://localhost:58000/checkout/session"

# 5. Update shipping information (use session_id from previous step)
curl -X POST "http://localhost:58000/checkout/session/{session_id}/update" `
  -H "Content-Type: application/json" `
  -d '{
    "shipping_name": "John Doe",
    "shipping_address": "123 Main St",
    "shipping_city": "New York",
    "shipping_postal_code": "10001"
  }'

# 6. Complete checkout
curl -X POST "http://localhost:58000/checkout/session/{session_id}/complete"

# 7. Query orders
curl "http://localhost:58000/orders"
```

---

## Important Notes

1. **Guest User ID**: The system currently uses simplified Guest Checkout, automatically generating a guest user ID for each request
2. **Best Buy API Key**: Ensure `BESTBUY_API_KEY` in `.env` file is correctly configured
3. **Real SKU/UPC**: Testing requires valid SKU or UPC from Best Buy API
4. **Session ID**: The `session_id` in checkout flow must be obtained from the create session response

---

## Testing with Swagger UI

The easiest way to test is to use Swagger UI:

1. Visit http://localhost:58000/docs
2. Expand any API endpoint
3. Click "Try it out"
4. Enter parameters
5. Click "Execute"
6. View the response result

This allows testing all API endpoints directly in the browser!
