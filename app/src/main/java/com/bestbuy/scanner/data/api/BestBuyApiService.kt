package com.bestbuy.scanner.data.api

import com.bestbuy.scanner.data.model.Product
import com.bestbuy.scanner.data.model.ProductResponse
import com.bestbuy.scanner.data.model.RecommendationResponse
import retrofit2.Response
import retrofit2.http.GET
import retrofit2.http.Path
import retrofit2.http.Query

/**
 * BestBuy API 服務介面
 */
interface BestBuyApiService {
    
    /**
     * 透過 UPC (條碼) 搜尋產品
     * 正確格式: GET /v1/products(upc=XXX)?apiKey=KEY&format=json
     * @param upc 產品的 UPC 條碼
     * @param apiKey BestBuy API Key
     * @param format 回應格式 (預設為 json)
     * @param show 要顯示的欄位 (可以自訂)
     */
    @GET("v1/products(upc={upc})")
    suspend fun searchProductByUPC(
        @Path("upc") upc: String,
        @Query("apiKey") apiKey: String,
        @Query("format") format: String = "json",
        @Query("show") show: String = "sku,name,regularPrice,salePrice,onSale,image,largeFrontImage,mediumImage,thumbnailImage,longDescription,shortDescription,manufacturer,modelNumber,upc,url,addToCartUrl,customerReviewAverage,customerReviewCount,freeShipping,inStoreAvailability,onlineAvailability"
    ): Response<ProductResponse>
    
    /**
     * 透過 SKU 搜尋產品
     * @param sku 產品的 SKU
     * @param apiKey BestBuy API Key
     */
    @GET("v1/products/{sku}.json")
    suspend fun getProductBySKU(
        @Path("sku") sku: String,
        @Query("apiKey") apiKey: String,
        @Query("show") show: String = "sku,name,regularPrice,salePrice,onSale,image,largeFrontImage,mediumImage,thumbnailImage,longDescription,shortDescription,manufacturer,modelNumber,upc,url,addToCartUrl,customerReviewAverage,customerReviewCount,freeShipping,inStoreAvailability,onlineAvailability"
    ): Response<Product>
    
    /**
     * 搜尋產品 (通用搜尋)
     * @param query 搜尋關鍵字
     * @param apiKey BestBuy API Key
     * @param pageSize Number of results per page (max 100)
     * @param sort Sort order
     */
    @GET("v1/products")
    suspend fun searchProducts(
        @Query("search") query: String,
        @Query("apiKey") apiKey: String,
        @Query("format") format: String = "json",
        @Query("show") show: String = "sku,name,regularPrice,salePrice,onSale,image,mediumImage,thumbnailImage,shortDescription,manufacturer,upc,url",
        @Query("pageSize") pageSize: Int = 10,
        @Query("sort") sort: String? = null
    ): Response<ProductResponse>
    
    /**
     * 取得推薦商品
     * @param sku 產品的 SKU
     * @param apiKey BestBuy API Key
     */
    @GET("v1/products/{sku}/alsoViewed")
    suspend fun getRecommendations(
        @Path("sku") sku: String,
        @Query("apiKey") apiKey: String
    ): Response<RecommendationResponse>
    
    /**
     * Get most viewed products by category
     * @param categoryId Category ID
     * @param apiKey BestBuy API Key
     * @param pageSize Number of results to return
     */
    @GET("v1/products/mostViewed(categoryId={categoryId})")
    suspend fun getMostViewed(
        @Path("categoryId") categoryId: String,
        @Query("apiKey") apiKey: String,
        @Query("pageSize") pageSize: Int = 10
    ): Response<ProductResponse>
    
    /**
     * Get Similar Products recommendations
     * @param sku Product SKU
     * @param apiKey BestBuy API Key
     */
    @GET("beta/products/{sku}/similar")
    suspend fun getSimilarProducts(
        @Path("sku") sku: String,
        @Query("apiKey") apiKey: String
    ): Response<RecommendationResponse>
}
