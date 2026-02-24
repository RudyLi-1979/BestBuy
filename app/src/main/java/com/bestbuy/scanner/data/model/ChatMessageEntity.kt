package com.bestbuy.scanner.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * Room Entity for persisting chat messages (including product cards) locally.
 * Products are stored as a JSON string and converted back via TypeConverter.
 */
@Entity(tableName = "chat_messages")
data class ChatMessageEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,

    val sessionId: String,

    val role: String, // "user" or "assistant"

    val content: String,

    val timestamp: Long,

    /** Serialised JSON of List<Product>; null when no products */
    val productsJson: String? = null
)
