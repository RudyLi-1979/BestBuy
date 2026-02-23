# BestBuy Scanner - Quick Start Guide

This project consists of two parts: the **Android App** and the **UCP Server**.

## Part 1: Android App Setup

### Step 1: Set API Key

1. Find the `.env` file in the project root directory (if it doesn't exist, copy `.env.example` and rename it to `.env`)
2. Open the `.env` file
3. Replace `YOUR_API_KEY_HERE` with your BestBuy API Key

```bash
# .env
BESTBUY_API_KEY=YOUR_ACTUAL_API_KEY
```

**Important**: The `.env` file has been added to `.gitignore` and will not be committed to version control, ensuring your API Key is safe.

## Step 2: Sync Gradle

Click "Sync Now" in Android Studio or run:
```bash
./gradlew build
```

## Step 3: Run the Application

1. Connect an Android device (it is recommended to use a physical device to test camera functionality)
2. Click the Run button (green triangle)
3. Grant camera and microphone permissions

---

## Part 2: UCP Server Setup (Optional)

> **Note**: You can skip this section if you only want to test barcode scanning functionality. Chat Mode requires the UCP Server to work.

### Method 1: Using Docker (Recommended)

**Prerequisites**: Docker Desktop is installed and running

```bash
cd ucp_server

# Configure environment variables
copy .env.example .env
# Edit .env to fill in API Keys

# Start the service (using quick script)
.\start_docker.ps1

# Or start manually
docker-compose up -d

# Check running status
docker-compose ps

# View logs
docker-compose logs -f
```

The server will start at `http://localhost:58000`.

**Stop the service**:
```bash
# Using quick script
.\stop_docker.ps1

# Or stop manually
docker-compose down
```

### Method 2: Local Development Mode

### Method 2: Local Development Mode

**Prerequisites**: Python 3.11+

```bash
cd ucp_server

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\/venv\Scripts\activate

# Activate virtual environment (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

```bash
# Copy environment variable template
copy .env.example .env

# Edit .env to fill in API Keys
```

Edit `ucp_server/.env`:
```bash
BESTBUY_API_KEY=your_BestBuy_API_KEY
GEMINI_API_KEY=your_Gemini_API_KEY
GEMINI_API_URL=https://your-gemini-api-url.com
```

### Step 3: Start the Server

```bash
# Using PowerShell script
.\start_server.ps1

# Or directly use uvicorn
uvicorn app.main:app --reload --port 58000
```

The server will start at `http://localhost:58000`.

### Step 4: Test the Server

Visit the following URLs to confirm the server is working properly:
- Homepage: http://localhost:58000
- API Documentation: http://localhost:58000/docs
- UCP Profile: http://localhost:58000/.well-known/ucp

---

## Testing Recommendations

### Test Chat Mode

1. Open the application (automatically enter Chat Mode)
2. Input text or use voice:
   - "I want to buy iPhone 15 Pro"
   - "Show me MacBook Pro 14 inch"
   - "Where can I buy Mac mini?"
3. View AI responses and product cards
4. Click on product cards to view detailed information

### Test Barcode Scanning

1. Click the "📷 Scan" button in Chat Mode
2. Grant camera permission
3. Scan the following test UPC codes:

**Test UPC Codes**

- **Apple AirPods**: `190199246850`
- **Samsung Galaxy**: `887276311111`  
- **Sony PlayStation**: `711719534464`

### Manual Input Test

If you don't have a physical product to scan:
1. Click the "Manual Input UPC" button
2. Enter any of the above UPC codes
3. View product details and recommended items

## Troubleshooting

### Gradle Sync Failed
- Confirm network connection is normal
- Check Android Studio version (version 2021.3 or later is recommended)
- Run `./gradlew clean build`

### Camera Cannot Start
- Use a physical device instead of an emulator
- Confirm camera permissions have been granted
- Check the permissions settings in AndroidManifest.xml

### API Request Failed
- Confirm that the API Key is set correctly
- Check the device's network connection
- View error messages in Logcat

## Development Environment Requirements

- Android Studio Arctic Fox (2020.3.1) or later
- JDK 8 or later
- Android SDK API Level 24 or higher
- Gradle 7.0 or later

## Next Steps

After the application starts, you can:
1. Scan any product barcode
2. View product details
3. Browse recommended products
4. Click on products to go to the BestBuy website

Enjoy using the application!
