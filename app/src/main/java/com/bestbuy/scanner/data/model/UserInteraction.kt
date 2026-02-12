package com.bestbuy.scanner.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * Entity representing user interactions with products
 * Used for tracking user behavior to generate personalized recommendations
 */
@Entity(tableName = "user_interactions")
data class UserInteraction(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val sku: String,
    val productName: String,
    val category: String?,
    val manufacturer: String?,
    val price: Double,
    val interactionType: InteractionType,
    val timestamp: Long = System.currentTimeMillis()
)

/**
 * Types of user interactions with products
 */
enum class InteractionType {
    VIEW,           // User viewed product details
    SCAN,           // User scanned product barcode
    ADD_TO_CART     // User added product to cart
}
