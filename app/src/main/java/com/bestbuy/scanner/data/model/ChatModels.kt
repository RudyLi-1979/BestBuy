package com.bestbuy.scanner.data.model

import com.google.gson.annotations.SerializedName

/**
 * Chat message data model
 */
data class ChatMessage(
    @SerializedName("role")
    val role: String, // "user" or "assistant"
    
    @SerializedName("content")
    val content: String,
    
    @SerializedName("timestamp")
    val timestamp: Long = System.currentTimeMillis(),
    
    // Optional: product recommendations from AI
    @SerializedName("products")
    val products: List<Product>? = null,
    
    // Optional: function call information
    @SerializedName("function_call")
    val functionCall: FunctionCall? = null
)

/**
 * Function call information
 */
data class FunctionCall(
    @SerializedName("name")
    val name: String,
    
    @SerializedName("arguments")
    val arguments: Map<String, Any>
)

/**
 * Chat request to UCP Server
 */
data class ChatRequest(
    @SerializedName("message")
    val message: String,
    
    @SerializedName("session_id")
    val sessionId: String? = null,
    
    @SerializedName("user_id")
    val userId: String? = null
)

/**
 * Chat response from UCP Server
 */
data class ChatResponse(
    @SerializedName("message")
    val message: String,
    
    @SerializedName("session_id")
    val sessionId: String,
    
    @SerializedName("function_calls")
    val functionCalls: List<FunctionCall>? = null,
    
    @SerializedName("products")
    val products: List<Product>? = null
)

/**
 * Chat history response
 */
data class ChatHistory(
    @SerializedName("session_id")
    val sessionId: String,
    
    @SerializedName("messages")
    val messages: List<ChatMessage>,
    
    @SerializedName("created_at")
    val createdAt: String
)
