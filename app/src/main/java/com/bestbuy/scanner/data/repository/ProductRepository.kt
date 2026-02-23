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
 * Product Data Repository
 */
class ProductRepository {
    
    private val apiService = RetrofitClient.apiService
    private val apiKey = BuildConfig.BESTBUY_API_KEY
    
    /**
     * Search for products by UPC barcode
     */
    suspend fun searchProductByUPC(upc: String): Result<Product?> {
        return withContext(Dispatchers.IO) {
            try {
                // Clean UPC code (remove spaces and special characters)
                val cleanUpc = upc.trim().replace(" ", "")
                
                android.util.Log.d("ProductRepository", "===========================================")
                android.util.Log.d("ProductRepository", "Search for products")
                android.util.Log.d("ProductRepository", "Original UPC: [$upc]")
                android.util.Log.d("ProductRepository", "Cleaned UPC: [$cleanUpc]")
                android.util.Log.d("ProductRepository", "API Format: products(upc=$cleanUpc)")
                android.util.Log.d("ProductRepository", "API Key: ${apiKey.take(8)}...${apiKey.takeLast(4)}")
                android.util.Log.d("ProductRepository", "===========================================")
                
                val response = apiService.searchProductByUPC(cleanUpc, apiKey)
                
                android.util.Log.d("ProductRepository", "API Response:")
                android.util.Log.d("ProductRepository", "HTTP Code: ${response.code()}")
                android.util.Log.d("ProductRepository", "Is Successful: ${response.isSuccessful}")
                
                if (response.isSuccessful) {
                    val products = response.body()?.products
                    android.util.Log.d("ProductRepository", "Found ${products?.size ?: 0} products")
                    
                    // Exact Match: Filter products with UPC matching exactly
                    val matchedProduct = products?.firstOrNull { product ->
                        val productUpc = product.upc?.trim()?.replace(" ", "")
                        val matched = productUpc == cleanUpc
                        android.util.Log.d("ProductRepository", "Check Product SKU: ${product.sku}, UPC: [$productUpc] vs [$cleanUpc] -> ${if (matched) "Match" else "Not Match"}")
                        matched
                    }
                    
                    if (matchedProduct != null) {
                        android.util.Log.d("ProductRepository", "Found matching product:")
                        android.util.Log.d("ProductRepository", "  SKU: ${matchedProduct.sku}")
                        android.util.Log.d("ProductRepository", "  Name: ${matchedProduct.name}")
                        android.util.Log.d("ProductRepository", "  UPC: ${matchedProduct.upc}")
                        android.util.Log.d("ProductRepository", "  Price: $${matchedProduct.regularPrice}")
                        Result.success(matchedProduct)
                    } else {
                        android.util.Log.w("ProductRepository", "Product not found, UPC: $cleanUpc")
                        Result.failure(Exception("Product not found, UPC: $cleanUpc"))
                    }
                } else {
                    val errorBody = response.errorBody()?.string()
                    android.util.Log.e("ProductRepository", "API Error: ${response.code()}")
                    Result.failure(Exception("API Error: ${response.code()} - ${response.message()}\n$errorBody"))
                }
            } catch (e: Exception) {
                android.util.Log.e("ProductRepository", "Search failed: ${e.message}", e)
                Result.failure(Exception("Search failed: ${e.message}", e))
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
