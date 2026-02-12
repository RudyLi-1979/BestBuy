package com.bestbuy.scanner.ui.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.LiveData
import androidx.lifecycle.asLiveData
import androidx.lifecycle.map
import androidx.lifecycle.viewModelScope
import com.bestbuy.scanner.data.database.AppDatabase
import com.bestbuy.scanner.data.model.CartItem
import com.bestbuy.scanner.data.model.Product
import com.bestbuy.scanner.data.repository.CartRepository
import kotlinx.coroutines.launch

/**
 * ViewModel for shopping cart
 */
class CartViewModel(application: Application) : AndroidViewModel(application) {
    
    private val repository: CartRepository
    
    /**
     * LiveData of all cart items
     */
    val cartItems: LiveData<List<CartItem>>
    
    /**
     * LiveData of total item count
     */
    val itemCount: LiveData<Int>
    
    /**
     * LiveData of total price
     */
    val totalPrice: LiveData<Double>
    
    init {
        val cartDao = AppDatabase.getDatabase(application).cartDao()
        repository = CartRepository(cartDao)
        cartItems = repository.allItems.asLiveData()
        itemCount = repository.itemCount.asLiveData()
        
        // Calculate total price from cart items
        totalPrice = cartItems.map { items ->
            items.sumOf { it.price * it.quantity }
        }
    }
    
    /**
     * Add product to cart
     */
    fun addToCart(product: Product) = viewModelScope.launch {
        repository.addItem(product)
    }
    
    /**
     * Update item quantity
     */
    fun updateQuantity(item: CartItem, quantity: Int) = viewModelScope.launch {
        repository.updateQuantity(item, quantity)
    }
    
    /**
     * Remove item from cart
     */
    fun removeItem(item: CartItem) = viewModelScope.launch {
        repository.removeItem(item)
    }
    
    /**
     * Clear all items from cart
     */
    fun clearCart() = viewModelScope.launch {
        repository.clearCart()
    }
}
