package com.bestbuy.scanner.data.database

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase
import com.bestbuy.scanner.data.dao.CartDao
import com.bestbuy.scanner.data.dao.UserInteractionDao
import com.bestbuy.scanner.data.model.CartItem
import com.bestbuy.scanner.data.model.UserInteraction

/**
 * Room database for BestBuy Scanner app
 */
@Database(
    entities = [CartItem::class, UserInteraction::class],
    version = 2,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {
    
    abstract fun cartDao(): CartDao
    abstract fun userInteractionDao(): UserInteractionDao
    
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
         * Get database instance (singleton pattern)
         */
        fun getDatabase(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "bestbuy_database"
                )
                    .addMigrations(MIGRATION_1_2)
                    .build()
                INSTANCE = instance
                instance
            }
        }
    }
}
