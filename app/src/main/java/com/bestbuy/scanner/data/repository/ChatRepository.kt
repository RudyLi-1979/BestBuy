package com.bestbuy.scanner.data.repository

import android.content.Context
import android.content.SharedPreferences
import android.util.Log
import com.bestbuy.scanner.data.api.UCPRetrofitClient
import com.bestbuy.scanner.data.database.AppDatabase
import com.bestbuy.scanner.data.model.ChatHistory
import com.bestbuy.scanner.data.model.ChatMessage
import com.bestbuy.scanner.data.model.ChatMessageEntity
import com.bestbuy.scanner.data.model.ChatRequest
import com.bestbuy.scanner.data.model.ChatResponse
import com.bestbuy.scanner.data.model.Product
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.util.UUID

/**
 * Repository for chat operations with UCP Server.
 * All sent/received messages (including product cards) are persisted locally
 * in Room so they survive app restarts.
 */
class ChatRepository(context: Context) {

    private val sharedPreferences: SharedPreferences =
        context.getSharedPreferences("chat_prefs", Context.MODE_PRIVATE)

    private val ucpApiService = UCPRetrofitClient.apiService
    private val chatMessageDao = AppDatabase.getDatabase(context).chatMessageDao()
    private val gson = Gson()

    companion object {
        private const val TAG = "ChatRepository"
        private const val KEY_SESSION_ID = "session_id"
        private const val KEY_USER_ID = "user_id"
    }

    // ─── Session / User helpers ────────────────────────────────────────────

    fun getSessionId(): String {
        var sessionId = sharedPreferences.getString(KEY_SESSION_ID, null)
        if (sessionId == null) {
            sessionId = UUID.randomUUID().toString()
            sharedPreferences.edit().putString(KEY_SESSION_ID, sessionId).apply()
        }
        return sessionId
    }

    fun getUserId(): String {
        var userId = sharedPreferences.getString(KEY_USER_ID, null)
        if (userId == null) {
            userId = "guest_${UUID.randomUUID()}"
            sharedPreferences.edit().putString(KEY_USER_ID, userId).apply()
        }
        return userId
    }

    // ─── Serialisation helpers ─────────────────────────────────────────────

    private fun productsToJson(products: List<Product>?): String? {
        if (products.isNullOrEmpty()) return null
        return gson.toJson(products)
    }

    private fun jsonToProducts(json: String?): List<Product>? {
        if (json.isNullOrBlank()) return null
        return try {
            val type = object : TypeToken<List<Product>>() {}.type
            gson.fromJson(json, type)
        } catch (e: Exception) {
            Log.w(TAG, "Failed to deserialise products JSON", e)
            null
        }
    }

    private fun entityToMessage(entity: ChatMessageEntity) = ChatMessage(
        role = entity.role,
        content = entity.content,
        timestamp = entity.timestamp,
        products = jsonToProducts(entity.productsJson)
    )

    // ─── Local persistence helpers ──────────────────────────────────────────

    private suspend fun saveMessageLocally(message: ChatMessage, sessionId: String) {
        val entity = ChatMessageEntity(
            sessionId = sessionId,
            role = message.role,
            content = message.content,
            timestamp = message.timestamp,
            productsJson = productsToJson(message.products)
        )
        chatMessageDao.insert(entity)
    }

    // ─── Public API ─────────────────────────────────────────────────────────

    /**
     * Load local chat history for the current session.
     * Returns messages from Room DB (products are preserved).
     */
    suspend fun getLocalHistory(): Result<List<ChatMessage>> = withContext(Dispatchers.IO) {
        try {
            val sessionId = getSessionId()
            val entities = chatMessageDao.getMessagesForSession(sessionId)
            Log.d(TAG, "Loaded ${entities.size} messages from local DB for session $sessionId")
            Result.success(entities.map { entityToMessage(it) })
        } catch (e: Exception) {
            Log.e(TAG, "Error loading local history", e)
            Result.failure(e)
        }
    }

    /**
     * Send a message to the AI assistant.
     * Both the user message and the AI response (with products) are saved locally.
     */
    suspend fun sendMessage(message: String): Result<ChatResponse> = withContext(Dispatchers.IO) {
        try {
            val sessionId = getSessionId()
            val request = ChatRequest(
                message = message,
                sessionId = sessionId,
                userId = getUserId()
            )

            Log.d(TAG, "Sending message: $message")
            val response = ucpApiService.sendMessage(request)

            if (response.isSuccessful && response.body() != null) {
                val chatResponse = response.body()!!
                Log.d(TAG, "Received response: ${chatResponse.message}")

                // Update session ID if server issued a new one
                if (chatResponse.sessionId != sessionId) {
                    sharedPreferences.edit()
                        .putString(KEY_SESSION_ID, chatResponse.sessionId)
                        .apply()
                }

                // Persist user message
                saveMessageLocally(
                    ChatMessage(role = "user", content = message),
                    chatResponse.sessionId
                )

                // Persist AI response (with products)
                saveMessageLocally(
                    ChatMessage(
                        role = "assistant",
                        content = chatResponse.message,
                        products = chatResponse.products
                    ),
                    chatResponse.sessionId
                )

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
     * Get conversation history from the server (text only, no products).
     * Prefer [getLocalHistory] for full fidelity including product cards.
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
     * Clear conversation history – removes local DB rows and resets the server session.
     */
    suspend fun clearHistory(): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            val sessionId = getSessionId()
            Log.d(TAG, "Clearing session: $sessionId")

            // Delete local messages first (best-effort; proceed even if server call fails)
            chatMessageDao.deleteSession(sessionId)

            val response = ucpApiService.clearSession(sessionId)

            if (response.isSuccessful) {
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
