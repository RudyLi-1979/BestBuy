package com.bestbuy.scanner.data.repository

import com.bestbuy.scanner.BuildConfig
import com.bestbuy.scanner.data.api.RetrofitClient
import com.bestbuy.scanner.data.model.Product
import com.bestbuy.scanner.data.model.ProductResponse
import com.bestbuy.scanner.data.model.RecommendationResponse
import com.bestbuy.scanner.data.model.RecommendationProduct
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * 產品資料儲存庫
 */
class ProductRepository {
    
    private val apiService = RetrofitClient.apiService
    private val apiKey = BuildConfig.BESTBUY_API_KEY
    
    /**
     * 透過 UPC 條碼搜尋產品
     */
    suspend fun searchProductByUPC(upc: String): Result<Product?> {
        return withContext(Dispatchers.IO) {
            try {
                // 清理 UPC 碼（移除空格和特殊字符）
                val cleanUpc = upc.trim().replace(" ", "")
                
                android.util.Log.d("ProductRepository", "===========================================")
                android.util.Log.d("ProductRepository", "🔍 搜索產品")
                android.util.Log.d("ProductRepository", "原始 UPC: [$upc]")
                android.util.Log.d("ProductRepository", "清理後 UPC: [$cleanUpc]")
                android.util.Log.d("ProductRepository", "API 格式: products(upc=$cleanUpc)")
                android.util.Log.d("ProductRepository", "API Key: ${apiKey.take(8)}...${apiKey.takeLast(4)}")
                android.util.Log.d("ProductRepository", "===========================================")
                
                val response = apiService.searchProductByUPC(cleanUpc, apiKey)
                
                android.util.Log.d("ProductRepository", "📡 API 回應:")
                android.util.Log.d("ProductRepository", "HTTP Code: ${response.code()}")
                android.util.Log.d("ProductRepository", "Is Successful: ${response.isSuccessful}")
                
                if (response.isSuccessful) {
                    val products = response.body()?.products
                    android.util.Log.d("ProductRepository", "找到 ${products?.size ?: 0} 個產品")
                    
                    // 🔍 精確匹配：過濾出 UPC 完全一致的產品
                    val matchedProduct = products?.firstOrNull { product ->
                        val productUpc = product.upc?.trim()?.replace(" ", "")
                        val matched = productUpc == cleanUpc
                        android.util.Log.d("ProductRepository", "檢查產品 SKU: ${product.sku}, UPC: [$productUpc] vs [$cleanUpc] -> ${if (matched) "✅ 匹配" else "❌ 不匹配"}")
                        matched
                    }
                    
                    if (matchedProduct != null) {
                        android.util.Log.d("ProductRepository", "✅ 找到匹配的產品:")
                        android.util.Log.d("ProductRepository", "  SKU: ${matchedProduct.sku}")
                        android.util.Log.d("ProductRepository", "  Name: ${matchedProduct.name}")
                        android.util.Log.d("ProductRepository", "  UPC: ${matchedProduct.upc}")
                        android.util.Log.d("ProductRepository", "  Price: \$${matchedProduct.regularPrice}")
                        Result.success(matchedProduct)
                    } else {
                        android.util.Log.w("ProductRepository", "❌ 找不到產品，UPC: $cleanUpc")
                        Result.failure(Exception("找不到產品，UPC: $cleanUpc"))
                    }
                } else {
                    val errorBody = response.errorBody()?.string()
                    android.util.Log.e("ProductRepository", "❌ API 錯誤: ${response.code()}")
                    Result.failure(Exception("API Error: ${response.code()} - ${response.message()}\n$errorBody"))
                }
            } catch (e: Exception) {
                android.util.Log.e("ProductRepository", "❌ 搜尋失敗: ${e.message}", e)
                Result.failure(Exception("搜尋失敗: ${e.message}", e))
            }
        }
    }
    
    /**
     * 透過 SKU 取得產品資訊
     */
    suspend fun getProductBySKU(sku: String): Result<Product?> {
        return withContext(Dispatchers.IO) {
            try {
                android.util.Log.d("ProductRepository", "🌐 Calling API: getProductBySKU($sku)")
                val response = apiService.getProductBySKU(sku, apiKey)
                if (response.isSuccessful) {
                    val product = response.body()  // Direct product object, not array
                    android.util.Log.d("ProductRepository", "✅ API Success: product=${product?.name}")
                    Result.success(product)
                } else {
                    android.util.Log.e("ProductRepository", "❌ API Error: ${response.code()} - ${response.message()}")
                    Result.failure(Exception("API Error: ${response.code()} - ${response.message()}"))
                }
            } catch (e: Exception) {
                android.util.Log.e("ProductRepository", "❌ Exception: ${e.message}", e)
                Result.failure(e)
            }
        }
    }
    
    /**
     * 搜尋產品
     */
    suspend fun searchProducts(query: String): Result<List<Product>> {
        return withContext(Dispatchers.IO) {
            try {
                val response = apiService.searchProducts(query, apiKey)
                if (response.isSuccessful) {
                    val products = response.body()?.products ?: emptyList()
                    Result.success(products)
                } else {
                    Result.failure(Exception("API Error: ${response.code()} - ${response.message()}"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    /**
     * 取得 Also Viewed 推薦產品（其他用戶也看了這些）
     * 這是 BestBuy API 唯一支持的推薦端點
     */
    suspend fun getAlsoViewed(sku: String): Result<List<RecommendationProduct>> {
        return withContext(Dispatchers.IO) {
            try {
                val response = apiService.getRecommendations(sku, apiKey)
                if (response.isSuccessful) {
                    val products = response.body()?.results ?: emptyList()
                    Result.success(products)
                } else {
                    Result.failure(Exception("API Error: ${response.code()} - ${response.message()}"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    /**
     * Get Similar Products recommendations
     */
    suspend fun getSimilarProducts(sku: String): Result<List<RecommendationProduct>> {
        return withContext(Dispatchers.IO) {
            try {
                val response = apiService.getSimilarProducts(sku, apiKey)
                if (response.isSuccessful) {
                    val products = response.body()?.results ?: emptyList()
                    Result.success(products)
                } else {
                    Result.failure(Exception("API Error: ${response.code()} - ${response.message()}"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    /**
     * Get combined recommendations (Also Viewed + Similar Products)
     * Returns a merged list of unique recommendations
     */
    suspend fun getRecommendations(sku: String): Result<List<RecommendationProduct>> {
        return withContext(Dispatchers.IO) {
            try {
                val alsoViewedResult = getAlsoViewed(sku)
                val similarResult = getSimilarProducts(sku)
                
                val alsoViewed = alsoViewedResult.getOrNull() ?: emptyList()
                val similar = similarResult.getOrNull() ?: emptyList()
                
                // Merge and deduplicate by SKU
                val combined = (alsoViewed + similar)
                    .distinctBy { it.sku }
                    .take(10) // Limit to 10 recommendations
                
                Result.success(combined)
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
}
