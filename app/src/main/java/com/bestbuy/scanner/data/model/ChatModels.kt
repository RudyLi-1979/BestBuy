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
 * User behavior context for Sparky-like personalized recommendations.
 * Collected from the device's Room DB (UserInteraction table) and sent
 * with every chat request so Gemini can tailor its suggestions.
 */
data class UserBehaviorContext(
    /** Top product categories user has been browsing (e.g. ["Televisions", "Laptops"]) */
    @SerializedName("recent_categories")
    val recentCategories: List<String> = emptyList(),

    /** SKUs of products the user recently viewed or scanned (last 5) */
    @SerializedName("recent_skus")
    val recentSkus: List<String> = emptyList(),

    /** Brands the user favours based on interaction frequency (top 2) */
    @SerializedName("favorite_manufacturers")
    val favoriteManufacturers: List<String> = emptyList(),

    /** Total number of interactions tracked in Room DB */
    @SerializedName("interaction_count")
    val interactionCount: Int = 0
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
    val userId: String? = null,

    /** Optionally included for personalized recommendations (may be null for new users) */
    @SerializedName("user_context")
    val userContext: UserBehaviorContext? = null
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
