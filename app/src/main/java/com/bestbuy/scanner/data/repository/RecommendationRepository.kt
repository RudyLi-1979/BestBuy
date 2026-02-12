package com.bestbuy.scanner.data.repository

import com.bestbuy.scanner.data.model.Product
import com.bestbuy.scanner.data.recommendation.RecommendationEngine

/**
 * Repository for managing product recommendations
 */
class RecommendationRepository(
    private val recommendationEngine: RecommendationEngine
) {
    
    /**
     * Get personalized product recommendations
     */
    suspend fun getRecommendations(limit: Int = 10): List<Product> {
        return recommendationEngine.getPersonalizedRecommendations(limit)
    }
}
