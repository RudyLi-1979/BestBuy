# API Testing Guide

## BestBuy API Endpoint Tests

### 1. Test Product Search (UPC)

Use the following curl command to test the API:

```bash
curl "https://api.bestbuy.com/v1/products(upc=190199246850)?apiKey=YOUR_API_KEY&format=json"
```

### 2. Test Product Details (SKU)

```bash
curl "https://api.bestbuy.com/v1/products/6443036.json?apiKey=YOUR_API_KEY"
```

### 3. Test Recommended Products

```bash
curl "https://api.bestbuy.com/v1/products/6443036/recommendations.json?apiKey=YOUR_API_KEY"
```

### 4. Test Also Viewed

```bash
curl "https://api.bestbuy.com/v1/products/6443036/alsoViewed.json?apiKey=YOUR_API_KEY"
```

## Test UPC Codes

| Product Name | UPC Code |
|---------|--------|
| Apple AirPods Pro | 190199246850 |
| Samsung Galaxy | 887276311111 |
| Sony PlayStation 5 | 711719534464 |
| Nintendo Switch | 045496590062 |
| Xbox Series X | 889842640670 |

## Application Testing Steps

### Functional Testing

1. **Barcode Scanning Test**
   - Open the application
   - Grant camera permission
   - Scan physical product barcode
   - Verify that product information is displayed correctly

2. **Manual Input Test**
   - Click \"Manual Input UPC\"
   - Input test UPC (e.g.: 190199246850)
   - Verify that product information is loaded

3. **Product Details Test**
   - Check product name and image display
   - Check price information (including sale price indicators)
   - Check product description
   - Check inventory status
   - Check customer reviews

4. **Recommended Products Test**
   - Verify that the recommended products list is displayed
   - Verify that the \"Others Also Viewed\" list is displayed
   - Click on recommended products to view details
   - Verify that navigation functions normally

5. **External Link Test**
   - Click \"View on BestBuy\"
   - Verify that the browser opens correctly
   - Click \"Add to Cart\"
   - Verify that the link is correct

### Error Handling Tests

1. **No Network Connection**
   - Disconnect from the network
   - Try scanning a barcode
   - Verify that an error message is displayed

2. **Invalid UPC**
   - Enter an invalid UPC (e.g.: 000000000000)
   - Verify that a "Product Not Found" message is displayed

3. **API Limits**
   - Quickly scan multiple barcodes in succession
   - Verify API limit handling

### Performance Testing

1. **Memory Usage**
   - Use Android Profiler to monitor memory usage
   - Continuously browse multiple products
   - Check for memory leaks

2. **Network Performance**
   - Monitor API request times
   - Check image loading speed
   - Verify caching mechanism

## UCP Server Testing

### Start the Server
```powershell
cd ucp_server
.\start_docker.ps1          # Docker (recommended) → http://localhost:58000
# OR
.\venv\Scripts\activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 58000
```

### Chat API
```bash
curl -X POST http://localhost:58000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me Mac mini 256GB", "session_id": "test-001"}'
```

### Store Availability (BOPIS)
```bash
curl -X POST http://localhost:58000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Is SKU 6509650 available near zip 94103?", "session_id": "test-002"}'
```

### Also Bought / Advanced Search via Chat
```bash
curl -X POST http://localhost:58000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What accessories are frequently bought with AirPods Pro?", "session_id": "test-003"}'

curl -X POST http://localhost:58000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me Sony TVs under $800", "session_id": "test-004"}'
```

### Health Check
```bash
curl http://localhost:58000/
# Swagger UI: http://localhost:58000/docs
```

## Troubleshooting

### API Returns 401 Error
- Check if the API Key is set correctly
- Confirm that the API Key is valid in the BestBuy Developer Portal

### API Returns 404 Error
- The product may not exist in the BestBuy database
- Try other test UPCs

### Recommended Products Not Showing
- Not all products have recommendation data
- This is normal; try other products

### Scanning Speed is Slow
- Ensure adequate lighting
- Keep the camera stable
- Barcode should be clear and visible

## Logcat Debugging

View detailed logs of API requests:

```bash
adb logcat | grep -E "BestBuy|OkHttp|Retrofit"
```

## Recommended Test Devices

- **Physical Device**: It is recommended to use a physical device to test camera functionality
- **Minimum API**: Android 7.0 (API 24)
- **Recommended API**: Android 10 (API 29) or higher

## Automated Testing (Future Implementation)

Can be considered for addition:
- Unit Tests (JUnit)
- UI Tests (Espresso)
- Integration Tests
- API Mock Testing
