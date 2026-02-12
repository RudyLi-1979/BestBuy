package com.bestbuy.scanner.ui.viewmodel

import android.app.Application
import android.util.Log
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.viewModelScope
import com.bestbuy.scanner.BuildConfig
import com.bestbuy.scanner.data.api.RetrofitClient
import com.bestbuy.scanner.data.database.AppDatabase
import com.bestbuy.scanner.data.model.InteractionType
import com.bestbuy.scanner.data.model.Product
import com.bestbuy.scanner.data.recommendation.RecommendationEngine
import com.bestbuy.scanner.data.repository.RecommendationRepository
import com.bestbuy.scanner.data.repository.UserBehaviorRepository
import kotlinx.coroutines.launch

/**
 * ViewModel for managing personalized recommendations
 */
class RecommendationViewModel(application: Application) : AndroidViewModel(application) {
    
    private val database = AppDatabase.getDatabase(application)
    private val userBehaviorRepository = UserBehaviorRepository(database.userInteractionDao())
    private val apiKey = BuildConfig.BESTBUY_API_KEY
    
    private val recommendationEngine = RecommendationEngine(
        userBehaviorRepository,
        RetrofitClient.apiService,
        apiKey
    )
    
    private val repository = RecommendationRepository(recommendationEngine)
    
    private val _recommendations = MutableLiveData<List<Product>>()
    val recommendations: LiveData<List<Product>> = _recommendations
    
    private val _isLoading = MutableLiveData<Boolean>()
    val isLoading: LiveData<Boolean> = _isLoading
    
    /**
     * Load personalized recommendations
     */
    fun loadRecommendations() {
        viewModelScope.launch {
            _isLoading.value = true
            try {
                val results = repository.getRecommendations(10)
                _recommendations.value = results
                Log.d(TAG, "Loaded ${results.size} recommendations")
            } catch (e: Exception) {
                Log.e(TAG, "Error loading recommendations", e)
                _recommendations.value = emptyList()
            } finally {
                _isLoading.value = false
            }
        }
    }
    
    /**
     * Track product view interaction
     */
    fun trackView(product: Product) {
        viewModelScope.launch {
            try {
                userBehaviorRepository.trackInteraction(product, InteractionType.VIEW)
                Log.d(TAG, "Tracked VIEW for product: ${product.name}")
            } catch (e: Exception) {
                Log.e(TAG, "Error tracking view", e)
            }
        }
    }
    
    /**
     * Track product scan interaction
     */
    fun trackScan(product: Product) {
        viewModelScope.launch {
            try {
                userBehaviorRepository.trackInteraction(product, InteractionType.SCAN)
                Log.d(TAG, "Tracked SCAN for product: ${product.name}")
            } catch (e: Exception) {
                Log.e(TAG, "Error tracking scan", e)
            }
        }
    }
    
    /**
     * Track add to cart interaction
     */
    fun trackAddToCart(product: Product) {
        viewModelScope.launch {
            try {
                userBehaviorRepository.trackInteraction(product, InteractionType.ADD_TO_CART)
                Log.d(TAG, "Tracked ADD_TO_CART for product: ${product.name}")
            } catch (e: Exception) {
                Log.e(TAG, "Error tracking add to cart", e)
            }
        }
    }
    
    companion object {
        private const val TAG = "RecommendationViewModel"
    }
}
