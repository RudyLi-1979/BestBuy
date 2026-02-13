package com.bestbuy.scanner.ui.adapter

import android.content.Intent
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.bestbuy.scanner.R
import com.bestbuy.scanner.data.model.ChatMessage
import com.bestbuy.scanner.data.model.Product
import com.bestbuy.scanner.ui.ProductDetailActivity
import java.text.SimpleDateFormat
import java.util.*

/**
 * Adapter for displaying chat messages
 */
class ChatAdapter : RecyclerView.Adapter<RecyclerView.ViewHolder>() {
    
    private val messages = mutableListOf<ChatMessage>()
    private val dateFormat = SimpleDateFormat("HH:mm", Locale.getDefault())
    
    companion object {
        private const val VIEW_TYPE_USER = 1
        private const val VIEW_TYPE_AI = 2
    }
    
    override fun getItemViewType(position: Int): Int {
        return if (messages[position].role == "user") {
            VIEW_TYPE_USER
        } else {
            VIEW_TYPE_AI
        }
    }
    
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): RecyclerView.ViewHolder {
        return when (viewType) {
            VIEW_TYPE_USER -> {
                val view = LayoutInflater.from(parent.context)
                    .inflate(R.layout.item_chat_message_user, parent, false)
                UserMessageViewHolder(view)
            }
            VIEW_TYPE_AI -> {
                val view = LayoutInflater.from(parent.context)
                    .inflate(R.layout.item_chat_message_ai, parent, false)
                AIMessageViewHolder(view)
            }
            else -> throw IllegalArgumentException("Invalid view type")
        }
    }
    
    override fun onBindViewHolder(holder: RecyclerView.ViewHolder, position: Int) {
        val message = messages[position]
        when (holder) {
            is UserMessageViewHolder -> holder.bind(message)
            is AIMessageViewHolder -> holder.bind(message)
        }
    }
    
    override fun getItemCount(): Int = messages.size
    
    /**
     * Update messages list
     */
    fun submitList(newMessages: List<ChatMessage>) {
        messages.clear()
        messages.addAll(newMessages)
        notifyDataSetChanged()
    }
    
    /**
     * Add a single message
     */
    fun addMessage(message: ChatMessage) {
        messages.add(message)
        notifyItemInserted(messages.size - 1)
    }
    
    /**
     * ViewHolder for user messages
     */
    inner class UserMessageViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val messageText: TextView = itemView.findViewById(R.id.messageText)
        private val timestampText: TextView = itemView.findViewById(R.id.timestampText)
        
        fun bind(message: ChatMessage) {
            messageText.text = message.content
            timestampText.text = dateFormat.format(Date(message.timestamp))
        }
    }
    
    /**
     * ViewHolder for AI messages
     */
    inner class AIMessageViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val messageText: TextView = itemView.findViewById(R.id.messageText)
        private val timestampText: TextView = itemView.findViewById(R.id.timestampText)
        private val productsRecyclerView: RecyclerView = itemView.findViewById(R.id.productsRecyclerView)
        
        fun bind(message: ChatMessage) {
            messageText.text = message.content
            timestampText.text = dateFormat.format(Date(message.timestamp))
            
            // Display product cards if message contains products
            message.products?.let { products ->
                if (products.isNotEmpty()) {
                    productsRecyclerView.visibility = View.VISIBLE
                    
                    // Setup horizontal RecyclerView for product cards
                    productsRecyclerView.layoutManager = LinearLayoutManager(
                        itemView.context,
                        LinearLayoutManager.HORIZONTAL,
                        false
                    )
                    
                    // Create adapter with click listener
                    val productAdapter = ChatProductAdapter { product ->
                        // Open ProductDetailActivity when product card is clicked
                        val context = itemView.context
                        val intent = Intent(context, ProductDetailActivity::class.java).apply {
                            putExtra("PRODUCT_SKU", product.sku.toString())
                        }
                        context.startActivity(intent)
                    }
                    
                    productsRecyclerView.adapter = productAdapter
                    productAdapter.submitList(products)
                } else {
                    productsRecyclerView.visibility = View.GONE
                }
            } ?: run {
                productsRecyclerView.visibility = View.GONE
            }
        }
    }
}
