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
    val price: Double,          // 實際售價 (salePrice ?? regularPrice)
    val regularPrice: Double = 0.0,  // 原始定價 (未折扣)
    val onSale: Boolean = false,     // 是否正在促銷
    val imageUrl: String?,
    var quantity: Int = 1,
    val addedAt: Long = System.currentTimeMillis()
)
