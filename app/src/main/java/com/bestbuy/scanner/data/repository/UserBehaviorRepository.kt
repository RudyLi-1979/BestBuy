package com.bestbuy.scanner.data.repository

import com.bestbuy.scanner.data.dao.UserInteractionDao
import com.bestbuy.scanner.data.model.InteractionType
import com.bestbuy.scanner.data.model.Product
import com.bestbuy.scanner.data.model.UserInteraction

/**
 * Repository for managing user behavior tracking
 */
class UserBehaviorRepository(private val dao: UserInteractionDao) {
    
    /**
     * Track user interaction with a product
     */
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
    
    /**
     * Get user's favorite categories based on interaction frequency
     */
    suspend fun getFavoriteCategories(limit: Int = 3): List<String> {
        return dao.getMostViewedCategories(limit).map { it.category }
    }
    
    /**
     * Get all SKUs that user has viewed
     */
    suspend fun getViewedSkus(): List<String> {
        return dao.getAllViewedSkus()
    }
    
    /**
     * Get total count of user interactions
     */
    suspend fun getTotalInteractionCount(): Int {
        return dao.getTotalCount()
    }
    
    /**
     * Clean old interaction data
     */
    suspend fun cleanOldData(daysToKeep: Int = 30) {
        val cutoffTime = System.currentTimeMillis() - (daysToKeep * 24 * 60 * 60 * 1000L)
        dao.deleteOldInteractions(cutoffTime)
    }
}
