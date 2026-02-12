package com.bestbuy.scanner.data.dao

import androidx.room.*
import com.bestbuy.scanner.data.model.CartItem
import kotlinx.coroutines.flow.Flow

/**
 * Data Access Object for cart operations
 */
@Dao
interface CartDao {
    /**
     * Get all cart items ordered by added time (newest first)
     */
    @Query("SELECT * FROM cart_items ORDER BY addedAt DESC")
    fun getAllItems(): Flow<List<CartItem>>
    
    /**
     * Insert or replace a cart item
     */
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertItem(item: CartItem)
    
    /**
     * Update an existing cart item
     */
    @Update
    suspend fun updateItem(item: CartItem)
    
    /**
     * Delete a cart item
     */
    @Delete
    suspend fun deleteItem(item: CartItem)
    
    /**
     * Clear all items from cart
     */
    @Query("DELETE FROM cart_items")
    suspend fun clearCart()
    
    /**
     * Get total number of items in cart
     */
    @Query("SELECT COUNT(*) FROM cart_items")
    fun getItemCount(): Flow<Int>
    
    /**
     * Get cart item by SKU
     */
    @Query("SELECT * FROM cart_items WHERE sku = :sku")
    suspend fun getItemBySku(sku: Int): CartItem?
}
