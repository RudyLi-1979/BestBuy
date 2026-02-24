package com.bestbuy.scanner.data.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.bestbuy.scanner.data.model.ChatMessageEntity

/**
 * DAO for persisting and loading chat messages locally.
 */
@Dao
interface ChatMessageDao {

    /** Insert a single message. */
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(message: ChatMessageEntity)

    /** Insert a list of messages at once. */
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(messages: List<ChatMessageEntity>)

    /** Load all messages for a session, ordered by timestamp. */
    @Query("SELECT * FROM chat_messages WHERE sessionId = :sessionId ORDER BY timestamp ASC")
    suspend fun getMessagesForSession(sessionId: String): List<ChatMessageEntity>

    /** Delete all messages for a session (used when user clears chat). */
    @Query("DELETE FROM chat_messages WHERE sessionId = :sessionId")
    suspend fun deleteSession(sessionId: String)

    /** Delete all chat messages (full reset). */
    @Query("DELETE FROM chat_messages")
    suspend fun deleteAll()
}
