package com.bestbuy.scanner.data.database

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase
import com.bestbuy.scanner.data.dao.CartDao
import com.bestbuy.scanner.data.dao.ChatMessageDao
import com.bestbuy.scanner.data.dao.UserInteractionDao
import com.bestbuy.scanner.data.model.CartItem
import com.bestbuy.scanner.data.model.ChatMessageEntity
import com.bestbuy.scanner.data.model.UserInteraction

/**
 * Room database for BestBuy Scanner app
 */
@Database(
    entities = [CartItem::class, UserInteraction::class, ChatMessageEntity::class],
    version = 4,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {
    
    abstract fun cartDao(): CartDao
    abstract fun userInteractionDao(): UserInteractionDao
    abstract fun chatMessageDao(): ChatMessageDao
    
    companion object {
        @Volatile
        private var INSTANCE: AppDatabase? = null
        
        /**
         * Migration from version 1 to 2: Add user_interactions table
         */
        private val MIGRATION_1_2 = object : Migration(1, 2) {
            override fun migrate(database: SupportSQLiteDatabase) {
                database.execSQL(
                    """
                    CREATE TABLE IF NOT EXISTS user_interactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        sku TEXT NOT NULL,
                        productName TEXT NOT NULL,
                        category TEXT,
                        manufacturer TEXT,
                        price REAL NOT NULL,
                        interactionType TEXT NOT NULL,
                        timestamp INTEGER NOT NULL
                    )
                    """.trimIndent()
                )
            }
        }
        
        /**
         * Migration from version 2 to 3: Add chat_messages table for local chat persistence
         */
        private val MIGRATION_2_3 = object : Migration(2, 3) {
            override fun migrate(database: SupportSQLiteDatabase) {
                database.execSQL(
                    """
                    CREATE TABLE IF NOT EXISTS chat_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        sessionId TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp INTEGER NOT NULL,
                        productsJson TEXT
                    )
                    """.trimIndent()
                )
            }
        }

        /**
         * Migration from version 3 to 4: Add regularPrice and onSale columns to cart_items
         */
        private val MIGRATION_3_4 = object : Migration(3, 4) {
            override fun migrate(database: SupportSQLiteDatabase) {
                database.execSQL("ALTER TABLE cart_items ADD COLUMN regularPrice REAL NOT NULL DEFAULT 0")
                database.execSQL("ALTER TABLE cart_items ADD COLUMN onSale INTEGER NOT NULL DEFAULT 0")
            }
        }

        /**
         * Get database instance (singleton pattern)
         */
        fun getDatabase(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "bestbuy_database"
                )
                    .addMigrations(MIGRATION_1_2, MIGRATION_2_3, MIGRATION_3_4)
                    .build()
                INSTANCE = instance
                instance
            }
        }
    }
}
