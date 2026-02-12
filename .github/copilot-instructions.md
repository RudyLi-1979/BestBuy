# BestBuy Scanner - AI Coding Agent Instructions

## Project Overview

Android barcode scanner app using **MVVM architecture** with CameraX, ML Kit, and BestBuy API integration. Written in **Kotlin** with manual dependency injection (no Hilt/Koin).

## Critical Patterns

### API Key Management
- **NEVER hardcode API keys** - always use `BuildConfig.BESTBUY_API_KEY`
- API key is loaded from `.env` file at build time via `app/build.gradle.kts`
- Example: `private val apiKey = BuildConfig.BESTBUY_API_KEY`
- See [SECURITY.md](../SECURITY.md) for complete guidelines

### UPC Barcode Processing
Always clean UPC input before API calls:
```kotlin
val cleanUpc = upc.trim().replace(" ", "")
```
Valid formats: UPC-A (12), EAN-13 (13), UPC-E (8) - all numeric. See [ProductRepository.kt](../app/src/main/java/com/bestbuy/scanner/data/repository/ProductRepository.kt#L27-L29) for reference implementation.

### API Request Patterns
- BestBuy API uses unique path format: `products(upc={upc})` not `products?upc={upc}`
- Always include `@Query("format") format: String = "json"`
- Use `@Query("show")` parameter to specify exact fields (reduces response size)
- See [BestBuyApiService.kt](../app/src/main/java/com/bestbuy/scanner/data/api/BestBuyApiService.kt) for all endpoint signatures

### Logging Standards
Use structured logging with visual separators for debugging:
```kotlin
android.util.Log.d("ComponentName", "===========================================")
android.util.Log.d("ComponentName", "🔍 Operation description")
android.util.Log.d("ComponentName", "Key data: $value")
android.util.Log.d("ComponentName", "===========================================")
```
See [ProductRepository.kt](../app/src/main/java/com/bestbuy/scanner/data/repository/ProductRepository.kt#L28-L36) for examples.

### Coroutines & LiveData
- All repository methods use `suspend fun` with `withContext(Dispatchers.IO)`
- ViewModel launches coroutines with `viewModelScope.launch`
- Return `Result<T>` from repository methods for cleaner error handling
- Use `MutableLiveData` privately, expose as `LiveData` publicly in ViewModels

## Architecture Layers

```
View (Activity/Fragment)
  ↓ observes LiveData
ViewModel (ProductViewModel)
  ↓ calls repository
Repository (ProductRepository) 
  ↓ uses Retrofit service
API Service (BestBuyApiService)
```

**Manual DI**: Components instantiated directly (e.g., `private val repository = ProductRepository()`)

## Key Files

- [BestBuyApiService.kt](../app/src/main/java/com/bestbuy/scanner/data/api/BestBuyApiService.kt) - All API endpoint definitions
- [ProductRepository.kt](../app/src/main/java/com/bestbuy/scanner/data/repository/ProductRepository.kt) - Data access layer with UPC cleaning logic
- [ProductViewModel.kt](../app/src/main/java/com/bestbuy/scanner/ui/viewmodel/ProductViewModel.kt) - Business logic and state management
- [RetrofitClient.kt](../app/src/main/java/com/bestbuy/scanner/data/api/RetrofitClient.kt) - Network configuration (30s timeouts, logging interceptor)
- [BarcodeScannerAnalyzer.kt](../app/src/main/java/com/bestbuy/scanner/utils/BarcodeScannerAnalyzer.kt) - CameraX image analysis for ML Kit

## Common Issues & Debugging

### API Error 400 (Bad Request)
1. Verify `.env` file exists with valid `BESTBUY_API_KEY`
2. Check UPC format (must be all numeric, 8-14 digits)
3. Review logged API URL format in Logcat
4. See [TROUBLESHOOTING_API_400.md](../TROUBLESHOOTING_API_400.md) for complete diagnosis

### Build Issues
```powershell
# Clean and rebuild
./gradlew clean build

# Sync after .env changes
# Then: Gradle sync in Android Studio
```

### Camera Testing
- **Use physical device** - emulators don't support CameraX well
- Test UPCs: `190199246850` (AirPods), `887276311111` (Samsung), `711719534464` (PlayStation)
- See [API_TESTING.md](../API_TESTING.md) for more test data

## Development Workflow

1. **Setup**: Copy `.env.example` → `.env`, add API key
2. **Build**: `./gradlew build` or Android Studio sync
3. **Run**: Deploy to physical device (camera required)
4. **Test**: Scan barcodes or use test UPCs from [QUICKSTART.md](../QUICKSTART.md)

## Code Style

- **Package structure**: `com.bestbuy.scanner.{data|ui|utils}`
- **Naming**: Activities end with `Activity`, ViewModels with `ViewModel`, Adapters with `Adapter`
- **Comments**: Use KDoc for public methods, Chinese comments where needed for clarity
- **View Binding**: Enabled globally, use `binding.viewId` pattern

## Dependencies

Key libraries (see [app/build.gradle.kts](../app/build.gradle.kts)):
- CameraX 1.3.1 - Camera operations
- ML Kit 17.2.0 - Barcode scanning
- Retrofit 2.9.0 + OkHttp 4.12.0 - Networking
- Coroutines 1.7.3 - Async operations
- Lifecycle 2.7.0 - ViewModel/LiveData
- Glide 4.16.0 - Image loading

## Documentation References

- [ARCHITECTURE.md](../ARCHITECTURE.md) - Detailed architecture diagrams and data flows
- [QUICKSTART.md](../QUICKSTART.md) - Setup steps and test UPCs
- [SECURITY.md](../SECURITY.md) - API key management best practices
- [API_TESTING.md](../API_TESTING.md) - curl commands for API testing
