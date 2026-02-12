package com.bestbuy.scanner.data.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Query
import com.bestbuy.scanner.data.model.InteractionType
import com.bestbuy.scanner.data.model.UserInteraction
import kotlinx.coroutines.flow.Flow

/**
 * Data Access Object for user interactions
 */
@Dao
interface UserInteractionDao {
    
    /**
     * Insert a new user interaction
     */
    @Insert
    suspend fun insertInteraction(interaction: UserInteraction)
    
    /**
     * Get all user interactions ordered by timestamp
     */
    @Query("SELECT * FROM user_interactions ORDER BY timestamp DESC")
    fun getAllInteractions(): Flow<List<UserInteraction>>
    
    /**
     * Get interactions by type
     */
    @Query("SELECT * FROM user_interactions WHERE interactionType = :type ORDER BY timestamp DESC LIMIT :limit")
    suspend fun getInteractionsByType(type: InteractionType, limit: Int): List<UserInteraction>
    
    /**
     * Get most viewed categories with count
     */
    @Query("SELECT category, COUNT(*) as count FROM user_interactions WHERE category IS NOT NULL GROUP BY category ORDER BY count DESC LIMIT :limit")
    suspend fun getMostViewedCategories(limit: Int): List<CategoryCount>
    
    /**
     * Get all SKUs that user has viewed
     */
    @Query("SELECT DISTINCT sku FROM user_interactions")
    suspend fun getAllViewedSkus(): List<String>
    
    /**
     * Get total count of all user interactions
     */
    @Query("SELECT COUNT(*) FROM user_interactions")
    suspend fun getTotalCount(): Int
    
    /**
     * Delete old interactions before cutoff time
     */
    @Query("DELETE FROM user_interactions WHERE timestamp < :cutoffTime")
    suspend fun deleteOldInteractions(cutoffTime: Long)
}

/**
 * Data class for category count query result
 */
data class CategoryCount(
    val category: String,
    val count: Int
)
