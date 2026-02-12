package com.bestbuy.scanner.data.recommendation

import android.util.Log
import com.bestbuy.scanner.data.api.BestBuyApiService
import com.bestbuy.scanner.data.model.Product
import com.bestbuy.scanner.data.repository.UserBehaviorRepository

/**
 * Recommendation engine for generating personalized product recommendations
 */
class RecommendationEngine(
    private val userBehaviorRepository: UserBehaviorRepository,
    private val bestBuyApi: BestBuyApiService,
    private val apiKey: String
) {
    
    /**
     * Get personalized recommendations based on user's favorite categories
     * Returns empty list if user doesn't have enough interaction history
     */
    suspend fun getPersonalizedRecommendations(limit: Int = 10): List<Product> {
        // 1. Check if user has minimum interaction count
        val totalInteractions = userBehaviorRepository.getTotalInteractionCount()
        
        if (totalInteractions < MIN_INTERACTIONS_FOR_RECOMMENDATIONS) {
            Log.d(TAG, "Insufficient interactions ($totalInteractions < $MIN_INTERACTIONS_FOR_RECOMMENDATIONS), skipping recommendations")
            return emptyList()
        }
        
        // 2. Get user's favorite categories
        val favoriteCategories = userBehaviorRepository.getFavoriteCategories(3)
        
        if (favoriteCategories.isEmpty()) {
            Log.d(TAG, "No favorite categories found, skipping recommendations")
            return emptyList()
        }
        
        // 3. Fetch most viewed products from each favorite category
        val recommendations = mutableListOf<Product>()
        favoriteCategories.forEach { categoryId ->
            try {
                val response = bestBuyApi.getMostViewed(categoryId, apiKey)
                if (response.isSuccessful) {
                    response.body()?.products?.let { products ->
                        recommendations.addAll(products)
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error fetching recommendations for category $categoryId", e)
            }
        }
        
        // 4. Filter out already viewed products
        val viewedSkus = userBehaviorRepository.getViewedSkus()
        val filtered = recommendations.filterNot { product ->
            product.sku?.toString() in viewedSkus
        }
        
        // 5. Remove duplicates and limit results
        return filtered
            .distinctBy { it.sku }
            .take(limit)
    }
    
    companion object {
        private const val TAG = "RecommendationEngine"
        
        /**
         * Minimum number of user interactions required before showing personalized recommendations
         * This ensures recommendations are based on meaningful user behavior patterns
         */
        private const val MIN_INTERACTIONS_FOR_RECOMMENDATIONS = 5
    }
}
