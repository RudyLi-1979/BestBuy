package com.bestbuy.scanner.ui.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.bestbuy.scanner.data.model.ChatMessage
import com.bestbuy.scanner.data.repository.CartRepository
import com.bestbuy.scanner.data.repository.ChatRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * ViewModel for Chat functionality
 * Manages chat messages, loading state, and integration with cart
 */
class ChatViewModel(application: Application) : AndroidViewModel(application) {
    
    private val chatRepository = ChatRepository(application)
    
    // Chat messages
    private val _messages = MutableStateFlow<List<ChatMessage>>(emptyList())
    val messages: StateFlow<List<ChatMessage>> = _messages.asStateFlow()
    
    // Loading state
    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()
    
    // Error message
    private val _errorMessage = MutableStateFlow<String?>(null)
    val errorMessage: StateFlow<String?> = _errorMessage.asStateFlow()
    
    init {
        // Load conversation history on init
        loadHistory()
    }
    
    /**
     * Send a message to the AI assistant
     */
    fun sendMessage(message: String) {
        if (message.isBlank()) return
        
        viewModelScope.launch {
            try {
                _isLoading.value = true
                _errorMessage.value = null
                
                // Add user message to UI immediately
                val userMessage = ChatMessage(
                    role = "user",
                    content = message
                )
                _messages.value = _messages.value + userMessage
                
                // Send to server
                val result = chatRepository.sendMessage(message)
                
                result.onSuccess { response ->
                    // Determine the AI message content
                    val aiContent = when {
                        // If message is not empty, use it
                        response.message.isNotBlank() -> response.message
                        
                        // If message is empty but there are function calls, show a temporary message
                        !response.functionCalls.isNullOrEmpty() -> {
                            val functionName = response.functionCalls.first().name
                            when (functionName) {
                                "search_by_upc" -> "正在查詢產品資訊..."
                                "search_products" -> "正在搜尋產品..."
                                "add_to_cart" -> "正在加入購物車..."
                                "view_cart" -> "正在查看購物車..."
                                else -> "正在處理您的請求..."
                            }
                        }
                        
                        // If both are empty, show a default message
                        else -> "收到您的訊息"
                    }
                    
                    // Add AI response to UI
                    val aiMessage = ChatMessage(
                        role = "assistant",
                        content = aiContent,
                        products = response.products,
                        functionCall = response.functionCalls?.firstOrNull()
                    )
                    _messages.value = _messages.value + aiMessage
                    
                    // TODO: Handle function calls (e.g., add to cart)
                    response.functionCalls?.forEach { functionCall ->
                        handleFunctionCall(functionCall.name, functionCall.arguments)
                    }
                }
                
                result.onFailure { error ->
                    _errorMessage.value = error.message ?: "Unknown error occurred"
                }
                
            } catch (e: Exception) {
                _errorMessage.value = e.message ?: "Failed to send message"
            } finally {
                _isLoading.value = false
            }
        }
    }
    
    /**
     * Load conversation history from local Room DB.
     * The local DB persists products attached to each AI message,
     * so product cards are visible even after the app is restarted.
     */
    private fun loadHistory() {
        viewModelScope.launch {
            try {
                val result = chatRepository.getLocalHistory()
                result.onSuccess { history ->
                    _messages.value = history
                }
            } catch (e: Exception) {
                // Ignore errors when loading history
            }
        }
    }
    
    /**
     * Clear chat history and start new conversation
     */
    fun clearChat() {
        viewModelScope.launch {
            try {
                _isLoading.value = true
                val result = chatRepository.clearHistory()
                
                result.onSuccess {
                    _messages.value = emptyList()
                    _errorMessage.value = null
                }
                
                result.onFailure { error ->
                    _errorMessage.value = error.message ?: "Failed to clear chat"
                }
            } catch (e: Exception) {
                _errorMessage.value = e.message ?: "Failed to clear chat"
            } finally {
                _isLoading.value = false
            }
        }
    }
    
    /**
     * Clear error message
     */
    fun clearError() {
        _errorMessage.value = null
    }
    
    /**
     * Handle function calls from AI
     * TODO: Implement actual function handling (add to cart, etc.)
     */
    private fun handleFunctionCall(functionName: String, arguments: Map<String, Any>) {
        when (functionName) {
            "add_to_cart" -> {
                // TODO: Add product to cart
                // val sku = arguments["sku"] as? String
                // cartRepository.addItemBySku(sku)
            }
            "search_products" -> {
                // Products are already included in the response
            }
            "view_cart" -> {
                // Cart info is already included in the response
            }
            // Add more function handlers as needed
        }
    }
}
