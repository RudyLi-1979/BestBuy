package com.bestbuy.scanner.ui.viewmodel

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bestbuy.scanner.data.model.Product
import com.bestbuy.scanner.data.model.RecommendationProduct
import com.bestbuy.scanner.data.repository.ProductRepository
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

/**
 * Product ViewModel
 */
class ProductViewModel : ViewModel() {
    
    private val repository = ProductRepository()
    
    // Debounce job for recommendations
    private var recommendationsJob: Job? = null
    
    private val _product = MutableLiveData<Product?>()
    val product: LiveData<Product?> = _product
    
    // Combined recommendations (Also Viewed + Similar Products)
    private val _recommendations = MutableLiveData<List<RecommendationProduct>>()
    val recommendations: LiveData<List<RecommendationProduct>> = _recommendations
    
    private val _loading = MutableLiveData<Boolean>()
    val loading: LiveData<Boolean> = _loading
    
    private val _error = MutableLiveData<String?>()
    val error: LiveData<String?> = _error
    
    /**
     * Search product by UPC barcode
     */
    fun searchProductByUPC(upc: String) {
        viewModelScope.launch {
            _loading.value = true
            _error.value = null
            
            val result = repository.searchProductByUPC(upc)
            result.onSuccess { product ->
                _product.value = product
                
                // [DISABLED] Auto-load recommendations when product is found
                // product?.sku?.let { sku ->
                //     loadRecommendations(sku.toString())
                // }
            }.onFailure { exception ->
                _error.value = exception.message
            }
            
            _loading.value = false
        }
    }
    
    /**
     * Get product information by SKU
     */
    fun getProductBySKU(sku: String) {
        viewModelScope.launch {
            _loading.value = true
            _error.value = null
            
            android.util.Log.d("ProductViewModel", "🔍 getProductBySKU called with SKU: $sku")
            
            val result = repository.getProductBySKU(sku)
            result.onSuccess { product ->
                android.util.Log.d("ProductViewModel", "✅ Product fetched successfully")
                android.util.Log.d("ProductViewModel", "Product: ${product?.name}, SKU: ${product?.sku}")
                _product.value = product
                android.util.Log.d("ProductViewModel", "📤 _product.value updated")
                
                // Load recommendations
                loadRecommendations(sku)
            }.onFailure { exception ->
                android.util.Log.e("ProductViewModel", "❌ Failed to fetch product: ${exception.message}")
                _error.value = exception.message
            }
            
            _loading.value = false
        }
    }
    
    /**
     * Load combined recommendations (Also Viewed + Similar Products)
     * Delayed by 2 seconds to avoid API rate limiting (403 Over Quota)
     * Can be called externally
     */
    fun loadRecommendations(sku: String) {
        android.util.Log.d("ProductViewModel", "=========================================")
        android.util.Log.d("ProductViewModel", "📥 loadRecommendations called")
        android.util.Log.d("ProductViewModel", "SKU: $sku")
        android.util.Log.d("ProductViewModel", "Current Job Status: ${if (recommendationsJob?.isActive == true) "ACTIVE" else "IDLE"}")
        android.util.Log.d("ProductViewModel", "Stack trace:")
        Thread.currentThread().stackTrace.take(5).forEach {
            android.util.Log.d("ProductViewModel", "  at ${it.className}.${it.methodName}(${it.fileName}:${it.lineNumber})")
        }
        android.util.Log.d("ProductViewModel", "=========================================")
        
        // Cancel previous request
        if (recommendationsJob?.isActive == true) {
            android.util.Log.d("ProductViewModel", "⚠️ Cancelling previous request")
            recommendationsJob?.cancel()
        }
        
        recommendationsJob = viewModelScope.launch {
            // Delay 2000ms to prevent API rate limiting
            delay(2000)
            
            val result = repository.getRecommendations(sku)
            result.onSuccess { products ->
                _recommendations.value = products
            }.onFailure {
                // Silent failure, doesn't affect main product display
                _recommendations.value = emptyList()
            }
        }
    }
    
    /**
     * Clear product data
     */
    fun clearProduct() {
        // Cancel all ongoing requests
        recommendationsJob?.cancel()
        
        _product.value = null
        _recommendations.value = emptyList()
        _error.value = null
    }
}
