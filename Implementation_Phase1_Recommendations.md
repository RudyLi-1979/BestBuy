# 個人化推薦功能實作計畫 - 階段一

## 目標
實現基於用戶瀏覽歷史和類別偏好的個人化推薦功能

## 實作範圍（短期方案 1-2 週）

### 1. 數據收集層

#### [NEW] `UserInteraction.kt`
```kotlin
@Entity(tableName = "user_interactions")
data class UserInteraction(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val sku: String,
    val productName: String,
    val category: String?,
    val manufacturer: String?,
    val price: Double,
    val interactionType: InteractionType,
    val timestamp: Long = System.currentTimeMillis()
)

enum class InteractionType {
    VIEW,           // 查看商品詳情
    SCAN,           // 掃描條碼
    ADD_TO_CART     // 加入購物車
}
```

#### [NEW] `UserInteractionDao.kt`
```kotlin
@Dao
interface UserInteractionDao {
    @Insert
    suspend fun insertInteraction(interaction: UserInteraction)
    
    @Query("SELECT * FROM user_interactions ORDER BY timestamp DESC")
    fun getAllInteractions(): Flow<List<UserInteraction>>
    
    @Query("SELECT * FROM user_interactions WHERE interactionType = :type ORDER BY timestamp DESC LIMIT :limit")
    suspend fun getInteractionsByType(type: InteractionType, limit: Int): List<UserInteraction>
    
    @Query("SELECT category, COUNT(*) as count FROM user_interactions WHERE category IS NOT NULL GROUP BY category ORDER BY count DESC LIMIT :limit")
    suspend fun getMostViewedCategories(limit: Int): List<CategoryCount>
    
    @Query("SELECT DISTINCT sku FROM user_interactions")
    suspend fun getAllViewedSkus(): List<String>
    
    @Query("DELETE FROM user_interactions WHERE timestamp < :cutoffTime")
    suspend fun deleteOldInteractions(cutoffTime: Long)
}

data class CategoryCount(
    val category: String,
    val count: Int
)
```

#### [NEW] `UserBehaviorRepository.kt`
```kotlin
class UserBehaviorRepository(private val dao: UserInteractionDao) {
    
    suspend fun trackInteraction(
        product: Product,
        type: InteractionType
    ) {
        val interaction = UserInteraction(
            sku = product.sku?.toString() ?: return,
            productName = product.name ?: "Unknown",
            category = product.categoryPath?.firstOrNull()?.name,
            manufacturer = product.manufacturer,
            price = product.salePrice ?: product.regularPrice ?: 0.0,
            interactionType = type
        )
        dao.insertInteraction(interaction)
    }
    
    suspend fun getFavoriteCategories(limit: Int = 3): List<String> {
        return dao.getMostViewedCategories(limit).map { it.category }
    }
    
    suspend fun getViewedSkus(): List<String> {
        return dao.getAllViewedSkus()
    }
    
    suspend fun cleanOldData(daysToKeep: Int = 30) {
        val cutoffTime = System.currentTimeMillis() - (daysToKeep * 24 * 60 * 60 * 1000L)
        dao.deleteOldInteractions(cutoffTime)
    }
}
```

#### [MODIFY] `AppDatabase.kt`
新增 UserInteraction entity 和 DAO

---

### 2. 推薦引擎層

#### [NEW] `RecommendationEngine.kt`
```kotlin
class RecommendationEngine(
    private val userBehaviorRepository: UserBehaviorRepository,
    private val bestBuyApi: BestBuyApiService,
    private val apiKey: String
) {
    suspend fun getPersonalizedRecommendations(limit: Int = 10): List<Product> {
        // 1. 獲取用戶最喜歡的類別
        val favoriteCategories = userBehaviorRepository.getFavoriteCategories(3)
        
        if (favoriteCategories.isEmpty()) {
            // 新用戶：返回全站熱門商品
            return getDefaultRecommendations(limit)
        }
        
        // 2. 從每個類別獲取熱門商品
        val recommendations = mutableListOf<Product>()
        favoriteCategories.forEach { categoryId ->
            try {
                val response = bestBuyApi.getMostViewed(categoryId, apiKey)
                if (response.isSuccessful) {
                    response.body()?.results?.let { products ->
                        recommendations.addAll(products)
                    }
                }
            } catch (e: Exception) {
                Log.e("RecommendationEngine", "Error fetching recommendations for category $categoryId", e)
            }
        }
        
        // 3. 過濾已查看的商品
        val viewedSkus = userBehaviorRepository.getViewedSkus()
        val filtered = recommendations.filterNot { product ->
            product.sku?.toString() in viewedSkus
        }
        
        // 4. 去重並限制數量
        return filtered
            .distinctBy { it.sku }
            .take(limit)
    }
    
    private suspend fun getDefaultRecommendations(limit: Int): List<Product> {
        // 返回全站熱門商品（無類別限制）
        return try {
            val response = bestBuyApi.searchProducts(
                query = "*",
                apiKey = apiKey,
                pageSize = limit,
                sort = "customerReviewAverage.desc"
            )
            response.body()?.products ?: emptyList()
        } catch (e: Exception) {
            Log.e("RecommendationEngine", "Error fetching default recommendations", e)
            emptyList()
        }
    }
}
```

#### [NEW] `RecommendationRepository.kt`
```kotlin
class RecommendationRepository(
    private val recommendationEngine: RecommendationEngine
) {
    suspend fun getRecommendations(limit: Int = 10): List<Product> {
        return recommendationEngine.getPersonalizedRecommendations(limit)
    }
}
```

---

### 3. ViewModel 層

#### [NEW] `RecommendationViewModel.kt`
```kotlin
class RecommendationViewModel(application: Application) : AndroidViewModel(application) {
    private val database = AppDatabase.getDatabase(application)
    private val userBehaviorRepository = UserBehaviorRepository(database.userInteractionDao())
    private val apiKey = BuildConfig.BESTBUY_API_KEY
    
    private val recommendationEngine = RecommendationEngine(
        userBehaviorRepository,
        RetrofitClient.bestBuyApiService,
        apiKey
    )
    
    private val repository = RecommendationRepository(recommendationEngine)
    
    private val _recommendations = MutableLiveData<List<Product>>()
    val recommendations: LiveData<List<Product>> = _recommendations
    
    private val _isLoading = MutableLiveData<Boolean>()
    val isLoading: LiveData<Boolean> = _isLoading
    
    fun loadRecommendations() {
        viewModelScope.launch {
            _isLoading.value = true
            try {
                val results = repository.getRecommendations(10)
                _recommendations.value = results
            } catch (e: Exception) {
                Log.e("RecommendationViewModel", "Error loading recommendations", e)
                _recommendations.value = emptyList()
            } finally {
                _isLoading.value = false
            }
        }
    }
    
    fun trackView(product: Product) {
        viewModelScope.launch {
            userBehaviorRepository.trackInteraction(product, InteractionType.VIEW)
        }
    }
    
    fun trackScan(product: Product) {
        viewModelScope.launch {
            userBehaviorRepository.trackInteraction(product, InteractionType.SCAN)
        }
    }
    
    fun trackAddToCart(product: Product) {
        viewModelScope.launch {
            userBehaviorRepository.trackInteraction(product, InteractionType.ADD_TO_CART)
        }
    }
}
```

---

### 4. UI 層整合

#### [MODIFY] `ProductDetailActivity.kt`
新增行為追蹤和個人化推薦區塊

```kotlin
class ProductDetailActivity : AppCompatActivity() {
    private lateinit var recommendationViewModel: RecommendationViewModel
    
    override fun onCreate(savedInstanceState: Bundle?) {
        // ... existing code ...
        
        recommendationViewModel = ViewModelProvider(this)[RecommendationViewModel::class.java]
        
        // 追蹤查看行為
        product?.let { recommendationViewModel.trackView(it) }
        
        setupRecommendations()
    }
    
    private fun setupRecommendations() {
        // 載入個人化推薦
        recommendationViewModel.loadRecommendations()
        
        recommendationViewModel.recommendations.observe(this) { products ->
            if (products.isNotEmpty()) {
                binding.tvForYouTitle.visibility = View.VISIBLE
                binding.rvForYou.visibility = View.VISIBLE
                
                val forYouAdapter = RecommendationAdapter { product ->
                    // 點擊推薦商品
                    val intent = Intent(this, ProductDetailActivity::class.java)
                    intent.putExtra("PRODUCT_SKU", product.sku.toString())
                    startActivity(intent)
                }
                binding.rvForYou.adapter = forYouAdapter
                binding.rvForYou.layoutManager = LinearLayoutManager(
                    this,
                    LinearLayoutManager.HORIZONTAL,
                    false
                )
                forYouAdapter.submitList(products)
            }
        }
    }
    
    private fun setupAddToCart() {
        binding.btnAddToCart.setOnClickListener {
            product?.let { prod ->
                cartViewModel.addToCart(prod)
                recommendationViewModel.trackAddToCart(prod) // 追蹤加入購物車
                // ... existing snackbar code ...
            }
        }
    }
}
```

#### [MODIFY] `MainActivity.kt`
新增掃描追蹤

```kotlin
private fun onBarcodeDetected(barcode: String) {
    // ... existing code ...
    
    viewModel.searchProductByUPC(barcode)
    viewModel.product.observe(this) { product ->
        if (product != null) {
            // 追蹤掃描行為
            recommendationViewModel.trackScan(product)
            // ... navigate to detail ...
        }
    }
}
```

#### [NEW] `activity_product_detail.xml` 更新
新增 "For You" 推薦區塊

```xml
<!-- 在現有的推薦商品區塊之前新增 -->
<TextView
    android:id="@+id/tvForYouTitle"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:text="For You"
    android:textSize="18sp"
    android:textStyle="bold"
    android:paddingStart="16dp"
    android:paddingEnd="16dp"
    android:paddingTop="16dp"
    android:visibility="gone"
    app:layout_constraintTop_toBottomOf="@id/btnAddToCart" />

<androidx.recyclerview.widget.RecyclerView
    android:id="@+id/rvForYou"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:orientation="horizontal"
    android:paddingStart="16dp"
    android:paddingEnd="16dp"
    android:visibility="gone"
    app:layout_constraintTop_toBottomOf="@id/tvForYouTitle" />
```

---

### 5. BestBuy API 更新

#### [MODIFY] `BestBuyApiService.kt`
新增 mostViewed by category 端點

```kotlin
@GET("v1/products/mostViewed(categoryId={categoryId})")
suspend fun getMostViewed(
    @Path("categoryId") categoryId: String,
    @Query("apiKey") apiKey: String,
    @Query("pageSize") pageSize: Int = 10
): Response<ProductResponse>
```

---

## 驗證計畫

### 手動測試步驟

1. **測試數據收集**
   - 掃描多個不同類別的商品（例如：3 個相機、2 個電視）
   - 查看商品詳情頁
   - 加入購物車
   - 確認 Room Database 中有記錄

2. **測試推薦生成**
   - 查看 ProductDetailActivity 的 "For You" 區塊
   - 確認推薦商品與瀏覽歷史相關
   - 確認不會推薦已查看過的商品

3. **測試新用戶體驗**
   - 清除 App 數據
   - 確認顯示全站熱門商品

### 數據庫驗證
```sql
-- 查看用戶互動記錄
SELECT * FROM user_interactions ORDER BY timestamp DESC LIMIT 20;

-- 查看類別統計
SELECT category, COUNT(*) as count 
FROM user_interactions 
WHERE category IS NOT NULL 
GROUP BY category 
ORDER BY count DESC;
```

---

## 檔案清單

| 檔案 | 類型 | 說明 |
|------|------|------|
| `UserInteraction.kt` | 新增 | Entity 資料模型 |
| `InteractionType.kt` | 新增 | Enum 定義 |
| `UserInteractionDao.kt` | 新增 | DAO 介面 |
| `UserBehaviorRepository.kt` | 新增 | 用戶行為 Repository |
| `RecommendationEngine.kt` | 新增 | 推薦引擎核心邏輯 |
| `RecommendationRepository.kt` | 新增 | 推薦 Repository |
| `RecommendationViewModel.kt` | 新增 | 推薦 ViewModel |
| `AppDatabase.kt` | 修改 | 新增 UserInteraction entity |
| `BestBuyApiService.kt` | 修改 | 新增 mostViewed API |
| `ProductDetailActivity.kt` | 修改 | 整合推薦和追蹤 |
| `MainActivity.kt` | 修改 | 追蹤掃描行為 |
| `activity_product_detail.xml` | 修改 | 新增 For You 區塊 |

---

## 預期成果

1. ✅ 自動追蹤用戶行為（查看、掃描、加入購物車）
2. ✅ 基於類別偏好生成個人化推薦
3. ✅ 過濾已查看商品，避免重複推薦
4. ✅ 新用戶顯示全站熱門商品
5. ✅ 推薦結果顯示在商品詳情頁
