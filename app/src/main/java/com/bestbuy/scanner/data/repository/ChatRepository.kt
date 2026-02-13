package com.bestbuy.scanner.data.repository

import android.content.Context
import android.content.SharedPreferences
import android.util.Log
import com.bestbuy.scanner.data.api.UCPRetrofitClient
import com.bestbuy.scanner.data.model.ChatHistory
import com.bestbuy.scanner.data.model.ChatMessage
import com.bestbuy.scanner.data.model.ChatRequest
import com.bestbuy.scanner.data.model.ChatResponse
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.util.UUID

/**
 * Repository for chat operations with UCP Server
 */
class ChatRepository(context: Context) {
    
    private val sharedPreferences: SharedPreferences = 
        context.getSharedPreferences("chat_prefs", Context.MODE_PRIVATE)
    
    private val ucpApiService = UCPRetrofitClient.apiService
    
    companion object {
        private const val TAG = "ChatRepository"
        private const val KEY_SESSION_ID = "session_id"
        private const val KEY_USER_ID = "user_id"
    }
    
    /**
     * Get or create session ID
     */
    fun getSessionId(): String {
        var sessionId = sharedPreferences.getString(KEY_SESSION_ID, null)
        if (sessionId == null) {
            sessionId = UUID.randomUUID().toString()
            sharedPreferences.edit().putString(KEY_SESSION_ID, sessionId).apply()
        }
        return sessionId
    }
    
    /**
     * Get or create user ID (guest user)
     */
    fun getUserId(): String {
        var userId = sharedPreferences.getString(KEY_USER_ID, null)
        if (userId == null) {
            userId = "guest_${UUID.randomUUID()}"
            sharedPreferences.edit().putString(KEY_USER_ID, userId).apply()
        }
        return userId
    }
    
    /**
     * Send a message to the AI assistant
     * @param message User's message
     * @return Chat response from AI
     */
    suspend fun sendMessage(message: String): Result<ChatResponse> = withContext(Dispatchers.IO) {
        try {
            val request = ChatRequest(
                message = message,
                sessionId = getSessionId(),
                userId = getUserId()
            )
            
            Log.d(TAG, "Sending message: $message")
            val response = ucpApiService.sendMessage(request)
            
            if (response.isSuccessful && response.body() != null) {
                val chatResponse = response.body()!!
                Log.d(TAG, "Received response: ${chatResponse.message}")
                
                // Update session ID if server provides a new one
                if (chatResponse.sessionId != getSessionId()) {
                    sharedPreferences.edit()
                        .putString(KEY_SESSION_ID, chatResponse.sessionId)
                        .apply()
                }
                
                Result.success(chatResponse)
            } else {
                val errorMsg = "API Error: ${response.code()} - ${response.message()}"
                Log.e(TAG, errorMsg)
                Result.failure(Exception(errorMsg))
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error sending message", e)
            Result.failure(e)
        }
    }
    
    /**
     * Get conversation history
     * @return List of chat messages
     */
    suspend fun getHistory(): Result<List<ChatMessage>> = withContext(Dispatchers.IO) {
        try {
            val sessionId = getSessionId()
            Log.d(TAG, "Fetching history for session: $sessionId")
            
            val response = ucpApiService.getHistory(sessionId)
            
            if (response.isSuccessful && response.body() != null) {
                val history = response.body()!!
                Log.d(TAG, "Received ${history.messages.size} messages")
                Result.success(history.messages)
            } else {
                val errorMsg = "API Error: ${response.code()} - ${response.message()}"
                Log.e(TAG, errorMsg)
                Result.failure(Exception(errorMsg))
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error fetching history", e)
            Result.failure(e)
        }
    }
    
    /**
     * Clear conversation history and start a new session
     */
    suspend fun clearHistory(): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            val sessionId = getSessionId()
            Log.d(TAG, "Clearing session: $sessionId")
            
            val response = ucpApiService.clearSession(sessionId)
            
            if (response.isSuccessful) {
                // Generate new session ID
                val newSessionId = UUID.randomUUID().toString()
                sharedPreferences.edit()
                    .putString(KEY_SESSION_ID, newSessionId)
                    .apply()
                
                Log.d(TAG, "Session cleared, new session: $newSessionId")
                Result.success(Unit)
            } else {
                val errorMsg = "API Error: ${response.code()} - ${response.message()}"
                Log.e(TAG, errorMsg)
                Result.failure(Exception(errorMsg))
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error clearing history", e)
            Result.failure(e)
        }
    }
}
