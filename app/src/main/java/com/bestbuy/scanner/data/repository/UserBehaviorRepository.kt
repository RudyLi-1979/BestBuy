package com.bestbuy.scanner.data.repository

import com.bestbuy.scanner.data.dao.UserInteractionDao
import com.bestbuy.scanner.data.model.InteractionType
import com.bestbuy.scanner.data.model.Product
import com.bestbuy.scanner.data.model.UserBehaviorContext
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
     * Build a [UserBehaviorContext] snapshot to send with every chat request.
     * Returns null if the user has no interaction history yet (avoid sending
     * an empty context that wastes prompt tokens).
     *
     * Data collected:
     *  - Top 3 browsed categories
     *  - Last 5 viewed/scanned SKUs
     *  - Top 2 favourite manufacturers (brands)
     *  - Total interaction count
     */
    suspend fun getBehaviorSummary(): UserBehaviorContext? {
        val count = dao.getTotalCount()
        if (count == 0) return null   // no history yet — skip context injection

        val categories = dao.getMostViewedCategories(3).map { it.category }
        val skus = dao.getRecentSkus(5)
        val manufacturers = dao.getTopManufacturers(2).map { it.manufacturer }

        return UserBehaviorContext(
            recentCategories = categories,
            recentSkus = skus,
            favoriteManufacturers = manufacturers,
            interactionCount = count
        )
    }
    
    /**
     * Clean old interaction data
     */
    suspend fun cleanOldData(daysToKeep: Int = 30) {
        val cutoffTime = System.currentTimeMillis() - (daysToKeep * 24 * 60 * 60 * 1000L)
        dao.deleteOldInteractions(cutoffTime)
    }
}
