package com.bestbuy.scanner.data.api

/**
 * BestBuy API 測試範例
 * 
 * 這個檔案包含一些常見的產品 UPC 碼，可用於測試應用程式
 */
object BestBuyApiExamples {
    
    /**
     * 測試用的 UPC 碼列表
     */
    val TEST_UPCS = mapOf(
        "Apple AirPods Pro" to "190199246850",
        "Samsung Galaxy" to "887276311111",
        "Sony PlayStation 5" to "711719534464",
        "Nintendo Switch" to "045496590062",
        "Xbox Series X" to "889842640670",
        "MacBook Pro" to "194252098936",
        "iPad Air" to "194252096642",
        "Apple Watch" to "194252721711"
    )
    
    /**
     * API 使用範例
     */
    object ApiExamples {
        
        // 1. 透過 UPC 搜尋產品
        const val SEARCH_BY_UPC = "GET https://api.bestbuy.com/v1/products(upc=190199246850)?apiKey=YOUR_KEY&format=json"
        
        // 2. 透過 SKU 取得產品
        const val GET_BY_SKU = "GET https://api.bestbuy.com/v1/products/6443036.json?apiKey=YOUR_KEY"
        
        // 3. 搜尋產品（關鍵字）
        const val SEARCH_PRODUCTS = "GET https://api.bestbuy.com/v1/products(search=iphone)?apiKey=YOUR_KEY&format=json"
        
        // 4. 取得推薦商品
        const val GET_RECOMMENDATIONS = "GET https://api.bestbuy.com/v1/products/6443036/recommendations.json?apiKey=YOUR_KEY"
        
        // 5. 取得 Also Viewed
        const val GET_ALSO_VIEWED = "GET https://api.bestbuy.com/v1/products/6443036/alsoViewed.json?apiKey=YOUR_KEY"
    }
    
    /**
     * 常見的查詢欄位
     */
    object CommonFields {
        const val BASIC_FIELDS = "sku,name,regularPrice,salePrice,image"
        const val DETAILED_FIELDS = "sku,name,regularPrice,salePrice,onSale,image,largeFrontImage,mediumImage,thumbnailImage,longDescription,shortDescription,manufacturer,modelNumber,upc,productUrl,addToCartUrl,customerReviewAverage,customerReviewCount,freeShipping,inStoreAvailability,onlineAvailability"
    }
    
    /**
     * API 限制說明
     */
    object RateLimits {
        const val REQUESTS_PER_SECOND = 5
        const val REQUESTS_PER_DAY = 50000
        const val NOTE = "免費版 API 限制：每秒 5 次請求，每天 50,000 次請求"
    }
    
    /**
     * 錯誤代碼說明
     */
    object ErrorCodes {
        val CODES = mapOf(
            400 to "Bad Request - 請求格式錯誤",
            401 to "Unauthorized - API Key 無效",
            403 to "Forbidden - 超過請求限制",
            404 to "Not Found - 找不到產品",
            500 to "Internal Server Error - 伺服器錯誤",
            503 to "Service Unavailable - 服務暫時無法使用"
        )
    }
}
