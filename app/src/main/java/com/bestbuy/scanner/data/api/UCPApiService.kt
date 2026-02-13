package com.bestbuy.scanner.data.api

import com.bestbuy.scanner.data.model.ChatHistory
import com.bestbuy.scanner.data.model.ChatRequest
import com.bestbuy.scanner.data.model.ChatResponse
import retrofit2.Response
import retrofit2.http.*

/**
 * UCP Server API Service
 * Provides chat and shopping assistant functionality
 */
interface UCPApiService {
    
    /**
     * Send a message to the AI shopping assistant
     * @param request Chat request with message and optional session ID
     * @return Chat response with AI message and function calls
     */
    @POST("chat")
    suspend fun sendMessage(
        @Body request: ChatRequest
    ): Response<ChatResponse>
    
    /**
     * Get conversation history for a session
     * @param sessionId Session ID
     * @return Chat history with all messages
     */
    @GET("chat/session/{sessionId}/history")
    suspend fun getHistory(
        @Path("sessionId") sessionId: String
    ): Response<ChatHistory>
    
    /**
     * Clear conversation session
     * @param sessionId Session ID to clear
     */
    @DELETE("chat/session/{sessionId}")
    suspend fun clearSession(
        @Path("sessionId") sessionId: String
    ): Response<Unit>
}
