# Shopping Cart Implementation Plan

## 目標 (Goal)
將「Add to Cart」功能從跳轉 BestBuy 官網改為使用本地購物車系統,提供完整的購物車管理功能(新增、移除、修改數量、顯示總金額),無需真實金流付款。

## 問題分析 (Problem Analysis)
目前點擊「Add to Cart」會開啟手機瀏覽器並導向 BestBuy 官網,需要登入帳號。由於這是測試開發階段,不需要真實付款功能,因此需要實作本地購物車系統。

## 設計決策 (Design Decisions)

### UI/UX 設計方向
根據研究結果,採用以下設計原則:
- **Mobile-First**: 針對 Android 手機優化,大按鈕、易於單手操作
- **清晰透明**: 即時顯示商品資訊、數量、價格、總金額
- **易於編輯**: 直接在購物車內調整數量或移除商品
- **視覺回饋**: 新增商品時顯示 Toast 或 Snackbar 確認

### 技術架構
- **資料持久化**: 使用 Room Database 儲存購物車資料
- **架構模式**: 延續 MVVM 架構
- **UI 元件**: RecyclerView + CardView 顯示商品列表

## 實作變更 (Proposed Changes)

### 1. Data Layer

#### [NEW] [`CartItem.kt`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/java/com/bestbuy/scanner/data/model/CartItem.kt)
```kotlin
@Entity(tableName = "cart_items")
data class CartItem(
    @PrimaryKey val sku: Int,
    val name: String,
    val price: Double,
    val imageUrl: String?,
    var quantity: Int = 1,
    val addedAt: Long = System.currentTimeMillis()
)
```

#### [NEW] [`CartDao.kt`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/java/com/bestbuy/scanner/data/dao/CartDao.kt)
```kotlin
@Dao
interface CartDao {
    @Query("SELECT * FROM cart_items ORDER BY addedAt DESC")
    fun getAllItems(): Flow<List<CartItem>>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertItem(item: CartItem)
    
    @Update
    suspend fun updateItem(item: CartItem)
    
    @Delete
    suspend fun deleteItem(item: CartItem)
    
    @Query("DELETE FROM cart_items")
    suspend fun clearCart()
    
    @Query("SELECT COUNT(*) FROM cart_items")
    fun getItemCount(): Flow<Int>
}
```

#### [NEW] [`AppDatabase.kt`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/java/com/bestbuy/scanner/data/database/AppDatabase.kt)
```kotlin
@Database(entities = [CartItem::class], version = 1)
abstract class AppDatabase : RoomDatabase() {
    abstract fun cartDao(): CartDao
    
    companion object {
        @Volatile
        private var INSTANCE: AppDatabase? = null
        
        fun getDatabase(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "bestbuy_database"
                ).build()
                INSTANCE = instance
                instance
            }
        }
    }
}
```

#### [NEW] [`CartRepository.kt`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/java/com/bestbuy/scanner/data/repository/CartRepository.kt)
```kotlin
class CartRepository(private val cartDao: CartDao) {
    val allItems: Flow<List<CartItem>> = cartDao.getAllItems()
    val itemCount: Flow<Int> = cartDao.getItemCount()
    
    suspend fun addItem(product: Product) {
        val cartItem = CartItem(
            sku = product.sku ?: return,
            name = product.name ?: "Unknown",
            price = product.salePrice ?: product.regularPrice ?: 0.0,
            imageUrl = product.image
        )
        cartDao.insertItem(cartItem)
    }
    
    suspend fun updateQuantity(item: CartItem, newQuantity: Int) {
        if (newQuantity <= 0) {
            cartDao.deleteItem(item)
        } else {
            cartDao.updateItem(item.copy(quantity = newQuantity))
        }
    }
    
    suspend fun removeItem(item: CartItem) {
        cartDao.deleteItem(item)
    }
    
    suspend fun clearCart() {
        cartDao.clearCart()
    }
}
```

---

### 2. ViewModel Layer

#### [NEW] [`CartViewModel.kt`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/java/com/bestbuy/scanner/ui/viewmodel/CartViewModel.kt)
```kotlin
class CartViewModel(application: Application) : AndroidViewModel(application) {
    private val repository: CartRepository
    val cartItems: LiveData<List<CartItem>>
    val itemCount: LiveData<Int>
    val totalPrice: LiveData<Double>
    
    init {
        val cartDao = AppDatabase.getDatabase(application).cartDao()
        repository = CartRepository(cartDao)
        cartItems = repository.allItems.asLiveData()
        itemCount = repository.itemCount.asLiveData()
        totalPrice = cartItems.map { items ->
            items.sumOf { it.price * it.quantity }
        }
    }
    
    fun addToCart(product: Product) = viewModelScope.launch {
        repository.addItem(product)
    }
    
    fun updateQuantity(item: CartItem, quantity: Int) = viewModelScope.launch {
        repository.updateQuantity(item, quantity)
    }
    
    fun removeItem(item: CartItem) = viewModelScope.launch {
        repository.removeItem(item)
    }
    
    fun clearCart() = viewModelScope.launch {
        repository.clearCart()
    }
}
```

---

### 3. UI Layer

#### [NEW] [`activity_cart.xml`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/res/layout/activity_cart.xml)
購物車主畫面佈局:
- Toolbar with cart icon and item count
- RecyclerView for cart items
- Bottom bar with total price and checkout button
- Empty state view

#### [NEW] [`item_cart.xml`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/res/layout/item_cart.xml)
購物車商品項目佈局:
- Product image (thumbnail)
- Product name
- Price per unit
- Quantity controls (+/- buttons)
- Remove button
- Subtotal

#### [NEW] [`CartActivity.kt`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/java/com/bestbuy/scanner/ui/CartActivity.kt)
```kotlin
class CartActivity : AppCompatActivity() {
    private lateinit var binding: ActivityCartBinding
    private lateinit var viewModel: CartViewModel
    private lateinit var adapter: CartAdapter
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityCartBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        setupToolbar()
        setupRecyclerView()
        setupObservers()
        setupButtons()
    }
    
    private fun setupObservers() {
        viewModel.cartItems.observe(this) { items ->
            adapter.submitList(items)
            binding.emptyView.visibility = if (items.isEmpty()) View.VISIBLE else View.GONE
        }
        
        viewModel.totalPrice.observe(this) { total ->
            binding.tvTotalPrice.text = formatPrice(total)
        }
    }
}
```

#### [NEW] [`CartAdapter.kt`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/java/com/bestbuy/scanner/ui/adapter/CartAdapter.kt)
RecyclerView Adapter for cart items with quantity controls

---

### 4. MainActivity Updates

#### [MODIFY] [`MainActivity.kt`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/java/com/bestbuy/scanner/ui/MainActivity.kt)
新增購物車圖示到 Toolbar:
```kotlin
override fun onCreateOptionsMenu(menu: Menu): Boolean {
    menuInflater.inflate(R.menu.menu_main, menu)
    val cartMenuItem = menu.findItem(R.id.action_cart)
    
    // Update cart badge
    viewModel.itemCount.observe(this) { count ->
        cartMenuItem.actionView?.findViewById<TextView>(R.id.cart_badge)?.text = count.toString()
    }
    return true
}

override fun onOptionsItemSelected(item: MenuItem): Boolean {
    return when (item.itemId) {
        R.id.action_cart -> {
            startActivity(Intent(this, CartActivity::class.java))
            true
        }
        else -> super.onOptionsItemSelected(item)
    }
}
```

---

### 5. ProductDetailActivity Updates

#### [MODIFY] [`ProductDetailActivity.kt`](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/src/main/java/com/bestbuy/scanner/ui/ProductDetailActivity.kt)
修改「Add to Cart」按鈕行為:
```kotlin
// Before:
binding.btnAddToCart.setOnClickListener {
    val url = product.addToCartUrl ?: product.productUrl
    if (url != null) {
        val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
        startActivity(intent)
    }
}

// After:
binding.btnAddToCart.setOnClickListener {
    cartViewModel.addToCart(product)
    Snackbar.make(binding.root, "Added to cart", Snackbar.LENGTH_SHORT)
        .setAction("View Cart") {
            startActivity(Intent(this, CartActivity::class.java))
        }
        .show()
}
```

---

### 6. Dependencies

#### [MODIFY] [`build.gradle.kts` (app level)](file:///c:/Users/rudy/AndroidStudioProjects/BestBuy/app/build.gradle.kts)
新增 Room 依賴:
```kotlin
dependencies {
    // Room
    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    ksp("androidx.room:room-compiler:2.6.1")
    
    // Lifecycle
    implementation("androidx.lifecycle:lifecycle-livedata-ktx:2.7.0")
}
```

---

## 驗證計畫 (Verification Plan)

### 手動驗證步驟

1. **新增商品到購物車**
   - 啟動 App 並掃描任意商品
   - 進入商品詳情頁
   - 點擊「Add to Cart」按鈕
   - 確認出現 Snackbar 提示「Added to cart」
   - 確認 Toolbar 購物車圖示顯示數量 badge

2. **查看購物車**
   - 點擊 Toolbar 購物車圖示
   - 確認進入 CartActivity
   - 確認顯示剛才新增的商品
   - 確認商品資訊正確(圖片、名稱、價格、數量)
   - 確認底部顯示總金額

3. **修改商品數量**
   - 在購物車內點擊「+」按鈕
   - 確認數量增加,總金額更新
   - 點擊「-」按鈕
   - 確認數量減少,總金額更新
   - 當數量減到 0 時,確認商品從列表移除

4. **移除商品**
   - 點擊商品的「Remove」按鈕
   - 確認商品從列表移除
   - 確認總金額更新
   - 確認 Toolbar badge 更新

5. **清空購物車**
   - 新增多個商品到購物車
   - 點擊「Clear Cart」按鈕
   - 確認所有商品被移除
   - 確認顯示空狀態畫面

6. **資料持久化**
   - 新增商品到購物車
   - 關閉 App (完全退出)
   - 重新開啟 App
   - 確認購物車商品仍然存在

### 自動化測試 (Optional)
建議未來新增 Room DAO 單元測試:
```kotlin
@Test
fun insertAndRetrieveCartItem() {
    // Test implementation
}
```

---

## 後續改進建議

1. **結帳功能**: 新增結帳按鈕,顯示訂單摘要(僅 UI,無金流)
2. **商品庫存檢查**: 整合 BestBuy API 的庫存狀態
3. **購物車同步**: 若未來支援用戶登入,可同步到雲端
4. **優惠券系統**: 新增折扣碼輸入功能
5. **推薦商品**: 在購物車頁面顯示相關推薦
