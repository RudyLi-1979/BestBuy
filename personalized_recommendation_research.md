# 個人化推薦系統研究報告

## 研究目標
針對 BestBuy Scanner App，研究如何實現基於用戶購買紀錄和瀏覽歷史的個人化推薦功能。

---

## 一、主要發現

### 1.1 BestBuy API 限制
**結論**: BestBuy Recommendations API **不支援個人化推薦**

所有 BestBuy API 推薦端點都基於**全站用戶的聚合數據**，而非個別用戶的行為：
- `trendingViewed` - 過去 3 小時全站趨勢
- `mostViewed` - 過去 48 小時最多瀏覽
- `alsoViewed` - 過去 30 天其他人也看了
- `alsoBought` - 過去 30 天一起購買
- `viewedUltimatelyBought` - 過去 30 天看了最終買了

**影響**: 必須在 App 端自行實現個人化推薦邏輯

---

## 二、推薦系統實現方法

### 2.1 推薦演算法比較

| 演算法類型 | 原理 | 優點 | 缺點 | 適用場景 |
|-----------|------|------|------|----------|
| **Content-Based Filtering**<br>(基於內容) | 根據商品屬性推薦相似商品 | • 不依賴其他用戶<br>• 新商品易推薦<br>• 推薦理由明確 | • 缺乏多樣性<br>• 需要豐富的商品屬性<br>• 新用戶冷啟動 | 商品屬性豐富的場景 |
| **Collaborative Filtering**<br>(協同過濾) | 根據相似用戶的行為推薦 | • 推薦多樣化<br>• 不需要商品屬性<br>• 能發現意外驚喜 | • 新用戶/商品冷啟動<br>• 數據稀疏問題<br>• 熱門偏見 | 用戶數量多的平台 |
| **Association Rules**<br>(關聯規則) | 找出經常一起購買的商品 | • 簡單直觀<br>• 適合購物車推薦 | • 需要大量交易數據<br>• 僅限於共現模式 | "經常一起購買" 功能 |
| **Hybrid System**<br>(混合系統) | 結合多種方法 | • 互補優勢<br>• 推薦質量高 | • 實現複雜<br>• 計算成本高 | 成熟的電商平台 |

### 2.2 大型電商平台的實現方式

#### Amazon 的方法
- **Amazon Personalize**: 全託管的 ML 推薦服務
- **實時個人化**: 持續學習用戶最新行為
- **生成式 AI**: 使用 LLM 分析商品屬性和用戶購物資訊
- **多種推薦源**: 結合用戶行為、商品相似度、協同過濾

#### Alibaba 的方法
- **AIRec 引擎**: 基於大數據和 AI 技術
- **實時推薦**: 秒級捕捉用戶行為，毫秒級返回推薦
- **推薦多樣性**: 強調發現優化，避免過濾氣泡
- **個人化捆綁**: 使用 BGN (Bundle Generation Network)

---

## 三、Android 實現方案

### 3.1 架構選擇

#### 方案 A: 本地推薦引擎 (推薦)
**適合場景**: 小型 App、隱私優先、離線功能

```
┌─────────────────────────────────────┐
│         Android App (Kotlin)        │
├─────────────────────────────────────┤
│  UI Layer                           │
│  └─ ProductDetailActivity           │
│  └─ RecommendationFragment          │
├─────────────────────────────────────┤
│  ViewModel Layer                    │
│  └─ RecommendationViewModel         │
├─────────────────────────────────────┤
│  Repository Layer                   │
│  └─ UserBehaviorRepository          │
│  └─ RecommendationRepository        │
├─────────────────────────────────────┤
│  Local Recommendation Engine        │
│  ├─ Content-Based Filter            │
│  ├─ Simple Collaborative Filter     │
│  └─ Association Rules (Apriori)     │
├─────────────────────────────────────┤
│  Data Layer (Room Database)         │
│  ├─ UserInteraction Entity          │
│  ├─ ProductCache Entity             │
│  └─ RecommendationCache Entity      │
└─────────────────────────────────────┘
```

**優點**:
- ✅ 隱私保護 (數據不離開設備)
- ✅ 離線可用
- ✅ 響應速度快
- ✅ 無需後端服務器

**缺點**:
- ❌ 僅基於單一用戶數據
- ❌ 無法利用全局用戶行為
- ❌ 推薦質量受限

#### 方案 B: 後端推薦服務
**適合場景**: 大型 App、需要高質量推薦

```
┌─────────────────┐      API      ┌──────────────────┐
│  Android App    │◄─────────────►│  Backend Server  │
│  (Kotlin)       │               │  (Python/Node)   │
└─────────────────┘               ├──────────────────┤
                                  │  ML Models       │
                                  │  ├─ CF Model     │
                                  │  ├─ CBF Model    │
                                  │  └─ Hybrid       │
                                  ├──────────────────┤
                                  │  Database        │
                                  │  └─ User Data    │
                                  └──────────────────┘
```

**優點**:
- ✅ 利用全局用戶數據
- ✅ 複雜 ML 模型
- ✅ 推薦質量高
- ✅ 易於更新算法

**缺點**:
- ❌ 需要後端開發
- ❌ 隱私考量
- ❌ 需要網路連線
- ❌ 維護成本高

### 3.2 推薦的實現方案 (本地引擎)

#### 階段 1: 數據收集 (已完成)
使用 Room Database 記錄用戶行為：

```kotlin
@Entity(tableName = "user_interactions")
data class UserInteraction(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val sku: String,
    val productName: String,
    val category: String?,
    val price: Double,
    val interactionType: InteractionType, // VIEW, SCAN, ADD_TO_CART, PURCHASE
    val timestamp: Long = System.currentTimeMillis()
)

enum class InteractionType {
    VIEW,           // 查看商品詳情
    SCAN,           // 掃描條碼
    ADD_TO_CART,    // 加入購物車
    PURCHASE        // 結帳 (模擬)
}
```

#### 階段 2: 簡單推薦演算法

##### 2.1 基於類別的推薦 (最簡單)
```kotlin
class CategoryBasedRecommender(
    private val userInteractionDao: UserInteractionDao,
    private val bestBuyApi: BestBuyApiService
) {
    suspend fun getRecommendations(limit: Int = 10): List<Product> {
        // 1. 分析用戶最常瀏覽的類別
        val favoriteCategories = userInteractionDao
            .getMostViewedCategories(limit = 3)
        
        // 2. 從 BestBuy API 獲取該類別的熱門商品
        val recommendations = mutableListOf<Product>()
        favoriteCategories.forEach { category ->
            val products = bestBuyApi.getMostViewed(categoryId = category.id)
            recommendations.addAll(products.results)
        }
        
        // 3. 過濾已查看過的商品
        val viewedSkus = userInteractionDao.getAllViewedSkus()
        return recommendations.filterNot { it.sku in viewedSkus }
            .take(limit)
    }
}
```

##### 2.2 基於內容的推薦
```kotlin
class ContentBasedRecommender(
    private val userInteractionDao: UserInteractionDao,
    private val productRepository: ProductRepository
) {
    suspend fun getRecommendations(currentProduct: Product, limit: Int = 10): List<Product> {
        // 1. 獲取用戶喜歡的商品特徵
        val likedProducts = userInteractionDao.getLikedProducts() // 購物車 + 高評分
        
        // 2. 計算當前商品與用戶偏好的相似度
        val similarProducts = productRepository.findSimilarProducts(
            category = currentProduct.category,
            priceRange = currentProduct.regularPrice?.let { it * 0.7..it * 1.3 },
            manufacturer = currentProduct.manufacturer
        )
        
        // 3. 根據用戶歷史行為排序
        return similarProducts
            .sortedByDescending { calculateSimilarity(it, likedProducts) }
            .take(limit)
    }
    
    private fun calculateSimilarity(product: Product, likedProducts: List<Product>): Double {
        var score = 0.0
        likedProducts.forEach { liked ->
            if (product.category == liked.category) score += 0.4
            if (product.manufacturer == liked.manufacturer) score += 0.3
            if (isPriceRangeSimilar(product.regularPrice, liked.regularPrice)) score += 0.3
        }
        return score / likedProducts.size
    }
}
```

##### 2.3 關聯規則推薦 (經常一起購買)
```kotlin
class AssociationRuleRecommender(
    private val cartDao: CartDao,
    private val userInteractionDao: UserInteractionDao
) {
    suspend fun getFrequentlyBoughtTogether(currentSku: String, limit: Int = 5): List<String> {
        // 1. 獲取所有包含當前商品的購物車會話
        val sessionsWithProduct = userInteractionDao.getSessionsContaining(currentSku)
        
        // 2. 統計其他商品的共現頻率
        val coOccurrence = mutableMapOf<String, Int>()
        sessionsWithProduct.forEach { session ->
            session.products.forEach { sku ->
                if (sku != currentSku) {
                    coOccurrence[sku] = coOccurrence.getOrDefault(sku, 0) + 1
                }
            }
        }
        
        // 3. 返回最常一起購買的商品
        return coOccurrence.entries
            .sortedByDescending { it.value }
            .take(limit)
            .map { it.key }
    }
}
```

#### 階段 3: 混合推薦策略
```kotlin
class HybridRecommender(
    private val categoryBased: CategoryBasedRecommender,
    private val contentBased: ContentBasedRecommender,
    private val associationRule: AssociationRuleRecommender
) {
    suspend fun getPersonalizedRecommendations(
        context: RecommendationContext,
        limit: Int = 10
    ): List<Product> {
        val recommendations = mutableListOf<ScoredProduct>()
        
        // 1. 類別推薦 (權重 30%)
        categoryBased.getRecommendations(limit * 2).forEach {
            recommendations.add(ScoredProduct(it, score = 0.3))
        }
        
        // 2. 內容推薦 (權重 40%)
        context.currentProduct?.let { product ->
            contentBased.getRecommendations(product, limit * 2).forEach {
                recommendations.add(ScoredProduct(it, score = 0.4))
            }
        }
        
        // 3. 關聯規則 (權重 30%)
        context.cartItems.forEach { cartItem ->
            associationRule.getFrequentlyBoughtTogether(cartItem.sku, limit).forEach { sku ->
                // 從 API 獲取商品詳情
                val product = productRepository.getProductBySKU(sku)
                product?.let { recommendations.add(ScoredProduct(it, score = 0.3)) }
            }
        }
        
        // 4. 合併去重並排序
        return recommendations
            .groupBy { it.product.sku }
            .mapValues { entry -> entry.value.sumOf { it.score } }
            .entries
            .sortedByDescending { it.value }
            .take(limit)
            .mapNotNull { productRepository.getProductBySKU(it.key) }
    }
}

data class ScoredProduct(val product: Product, val score: Double)
data class RecommendationContext(
    val currentProduct: Product? = null,
    val cartItems: List<CartItem> = emptyList()
)
```

---

## 四、GitHub 參考資源

### 4.1 Android 推薦系統實現

| 專案 | 語言 | 技術 | 說明 |
|------|------|------|------|
| [Advanced-E-Commerce-Recommendation-System](https://github.com/rbhanush/Advanced-E-Commerce-Recommendation-System) | Java | Collaborative Filtering + NLP | Android app with clustering |
| [Recommendation-System-kNN](https://github.com/pprattis/Recommendation-System-for-Android-Java-App-that-finds-an-ideal-destination-with-the-kNN-Algorithm) | Java | k-NN Algorithm | 使用 k-NN 預測用戶評分 |
| [Ecommerce-Recommender](https://github.com/karan3691/Ecommerce-Recommender) | Python | ML-based (Flask API) | 可整合到 Android |
| [E_Commerce_Recommendation_System](https://github.com/kshitij7704/E_Commerce_Recommendation_System) | Python | Hybrid (Angular + Flask) | RESTful API 架構 |

### 4.2 推薦演算法庫

| 工具/庫 | 語言 | 用途 |
|---------|------|------|
| [Gorse](https://gorse.io) | Go | 開源推薦系統，提供 REST API |
| LightFM | Python | 協同過濾 (可部署為 API) |
| Surprise | Python | 推薦系統庫 |
| TensorFlow Lite | Kotlin/Java | 設備端 ML 推理 |

### 4.3 TensorFlow Lite 整合

Google 提供了 [Recommendations Codelab](https://codelabs.developers.google.com/codelabs/tflite-recommendations-firebase-android)，展示如何：
1. 使用 Firebase Analytics 收集用戶行為
2. 訓練推薦模型
3. 使用 TensorFlow Lite 在 Android 設備上運行推理

---

## 五、實施建議

### 5.1 短期方案 (1-2 週)
**目標**: 快速實現基本個人化推薦

1. **數據收集層**
   - ✅ 已有 Room Database (CartItem)
   - ➕ 新增 `UserInteraction` Entity
   - ➕ 在 `ProductDetailActivity` 記錄 VIEW 事件
   - ➕ 在 `CartActivity` 記錄 ADD_TO_CART 事件

2. **簡單推薦演算法**
   - 實現**基於類別的推薦**
   - 結合 BestBuy API 的 `mostViewed(categoryId)`
   - 過濾用戶已查看的商品

3. **UI 整合**
   - 在 `ProductDetailActivity` 新增 "For You" 推薦區塊
   - 在 `MainActivity` 新增 "Recommended for You" 首頁區塊

### 5.2 中期方案 (1-2 個月)
**目標**: 提升推薦質量

1. **內容推薦**
   - 實現基於內容的相似度計算
   - 分析商品屬性 (category, manufacturer, price range)

2. **關聯規則**
   - 實現 "Frequently Bought Together"
   - 使用 Apriori 演算法

3. **混合策略**
   - 組合多種推薦方法
   - 動態調整權重

### 5.3 長期方案 (3+ 個月)
**目標**: 進階 ML 推薦

1. **TensorFlow Lite 整合**
   - 訓練協同過濾模型
   - 部署到設備端

2. **後端服務** (可選)
   - 建立推薦 API 服務
   - 利用全局用戶數據

3. **A/B 測試**
   - 測試不同推薦策略
   - 優化推薦質量

---

## 六、參考資料

### 技術文章
- [Building a Recommendation System with TensorFlow Lite](https://developers.google.com/ml-kit/recommendations)
- [Amazon Personalize Documentation](https://aws.amazon.com/personalize/)
- [Alibaba AIRec Engine](https://www.alibabacloud.com/product/airec)

### 學術資源
- [Collaborative Filtering Explained](https://realpython.com/build-recommendation-engine-collaborative-filtering/)
- [Content-Based vs Collaborative Filtering](https://www.ibm.com/topics/recommendation-system)

### 實作教學
- [Android Recommendation System Tutorial](https://medium.com/@karan3691/building-an-e-commerce-recommendation-system)
- [Room Database Best Practices](https://developer.android.com/training/data-storage/room)

---

## 七、總結

### 核心發現
1. ❌ BestBuy API 不支援個人化推薦
2. ✅ 必須在 App 端實現推薦邏輯
3. ✅ 本地推薦引擎是可行且實用的方案

### 推薦的實施路徑
```
階段 1: 數據收集 (1 週)
    ↓
階段 2: 基於類別推薦 (1 週)
    ↓
階段 3: 內容推薦 + 關聯規則 (2-3 週)
    ↓
階段 4: 混合策略 (1-2 週)
    ↓
階段 5: ML 模型 (可選，1-2 個月)
```

### 預期效果
- **短期**: 基本個人化推薦，提升用戶體驗
- **中期**: 高質量推薦，增加商品發現率
- **長期**: 進階 ML 推薦，接近大型電商水平
