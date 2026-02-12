package com.bestbuy.scanner.data.repository

import com.bestbuy.scanner.data.dao.CartDao
import com.bestbuy.scanner.data.model.CartItem
import com.bestbuy.scanner.data.model.Product
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.withContext

/**
 * Repository for cart data operations
 */
class CartRepository(private val cartDao: CartDao) {
    
    /**
     * Flow of all cart items
     */
    val allItems: Flow<List<CartItem>> = cartDao.getAllItems()
    
    /**
     * Flow of total item count
     */
    val itemCount: Flow<Int> = cartDao.getItemCount()
    
    /**
     * Add a product to cart or increment quantity if already exists
     */
    suspend fun addItem(product: Product) = withContext(Dispatchers.IO) {
        val sku = product.sku ?: return@withContext
        
        // Check if item already exists
        val existingItem = cartDao.getItemBySku(sku)
        
        if (existingItem != null) {
            // Increment quantity if item exists
            cartDao.updateItem(existingItem.copy(quantity = existingItem.quantity + 1))
        } else {
            // Create new cart item
            val cartItem = CartItem(
                sku = sku,
                name = product.name ?: "Unknown Product",
                price = product.salePrice ?: product.regularPrice ?: 0.0,
                imageUrl = product.image
            )
            cartDao.insertItem(cartItem)
        }
    }
    
    /**
     * Update item quantity, remove if quantity is 0 or less
     */
    suspend fun updateQuantity(item: CartItem, newQuantity: Int) = withContext(Dispatchers.IO) {
        if (newQuantity <= 0) {
            cartDao.deleteItem(item)
        } else {
            cartDao.updateItem(item.copy(quantity = newQuantity))
        }
    }
    
    /**
     * Remove item from cart
     */
    suspend fun removeItem(item: CartItem) = withContext(Dispatchers.IO) {
        cartDao.deleteItem(item)
    }
    
    /**
     * Clear all items from cart
     */
    suspend fun clearCart() = withContext(Dispatchers.IO) {
        cartDao.clearCart()
    }
}
