package com.bestbuy.scanner.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * Cart item data model for Room database
 */
@Entity(tableName = "cart_items")
data class CartItem(
    @PrimaryKey val sku: Int,
    val name: String,
    val price: Double,
    val imageUrl: String?,
    var quantity: Int = 1,
    val addedAt: Long = System.currentTimeMillis()
)
