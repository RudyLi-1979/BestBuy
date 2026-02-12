package com.bestbuy.scanner.data.model

import com.google.gson.annotations.SerializedName
import java.io.Serializable

/**
 * 產品資料模型
 */
data class Product(
    @SerializedName("sku")
    val sku: Int?,
    
    @SerializedName("name")
    val name: String?,
    
    @SerializedName("regularPrice")
    val regularPrice: Double?,
    
    @SerializedName("salePrice")
    val salePrice: Double?,
    
    @SerializedName("onSale")
    val onSale: Boolean?,
    
    @SerializedName("image")
    val image: String?,
    
    @SerializedName("largeFrontImage")
    val largeFrontImage: String?,
    
    @SerializedName("mediumImage")
    val mediumImage: String?,
    
    @SerializedName("thumbnailImage")
    val thumbnailImage: String?,
    
    @SerializedName("longDescription")
    val longDescription: String?,
    
    @SerializedName("shortDescription")
    val shortDescription: String?,
    
    @SerializedName("manufacturer")
    val manufacturer: String?,
    
    @SerializedName("modelNumber")
    val modelNumber: String?,
    
    @SerializedName("upc")
    val upc: String?,
    
    @SerializedName("url")
    val productUrl: String?,
    
    @SerializedName("addToCartUrl")
    val addToCartUrl: String?,
    
    @SerializedName("affiliateAddToCartUrl")
    val affiliateAddToCartUrl: String?,
    
    @SerializedName("freeShipping")
    val freeShipping: Boolean?,
    
    @SerializedName("shippingCost")
    val shippingCost: Double?,
    
    @SerializedName("inStoreAvailability")
    val inStoreAvailability: Boolean?,
    
    @SerializedName("onlineAvailability")
    val onlineAvailability: Boolean?,
    
    @SerializedName("customerReviewAverage")
    val customerReviewAverage: Double?,
    
    @SerializedName("customerReviewCount")
    val customerReviewCount: Int?,
    
    @SerializedName("categoryPath")
    val categoryPath: List<CategoryPathItem>?
) : Serializable

data class CategoryPathItem(
    @SerializedName("id")
    val id: String?,
    
    @SerializedName("name")
    val name: String?
)

/**
 * API 回應模型
 */
data class ProductResponse(
    @SerializedName("products")
    val products: List<Product>?,
    
    @SerializedName("from")
    val from: Int?,
    
    @SerializedName("to")
    val to: Int?,
    
    @SerializedName("total")
    val total: Int?,
    
    @SerializedName("currentPage")
    val currentPage: Int?,
    
    @SerializedName("totalPages")
    val totalPages: Int?
)

/**
 * 推薦商品數據模型 (與 Products API 結構不同)
 */
data class RecommendationProduct(
    @SerializedName("sku")
    val sku: String?,
    
    @SerializedName("customerReviews")
    val customerReviews: CustomerReviews?,
    
    @SerializedName("descriptions")
    val descriptions: Descriptions?,
    
    @SerializedName("images")
    val images: Images?,
    
    @SerializedName("names")
    val names: Names?,
    
    @SerializedName("prices")
    val prices: Prices?,
    
    @SerializedName("links")
    val links: Links?,
    
    @SerializedName("rank")
    val rank: Int?
)

data class CustomerReviews(
    @SerializedName("averageScore")
    val averageScore: Double?,
    
    @SerializedName("count")
    val count: Int?
)

data class Descriptions(
    @SerializedName("short")
    val short: String?
)

data class Images(
    @SerializedName("standard")
    val standard: String?
)

data class Names(
    @SerializedName("title")
    val title: String?
)

data class Prices(
    @SerializedName("regular")
    val regular: Double?,
    
    @SerializedName("current")
    val current: Double?
)

data class Links(
    @SerializedName("product")
    val product: String?,
    
    @SerializedName("web")
    val web: String?,
    
    @SerializedName("addToCart")
    val addToCart: String?
)

/**
 * 推薦商品回應模型
 */
data class RecommendationResponse(
    @SerializedName("metadata")
    val metadata: RecommendationMetadata?,
    
    @SerializedName("results")
    val results: List<RecommendationProduct>?
)

data class RecommendationMetadata(
    @SerializedName("resultSet")
    val resultSet: ResultSet?,
    
    @SerializedName("context")
    val context: Context?
)

data class ResultSet(
    @SerializedName("count")
    val count: Int?
)

data class Context(
    @SerializedName("canonicalUrl")
    val canonicalUrl: String?
)
