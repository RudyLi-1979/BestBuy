package com.bestbuy.scanner.ui.adapter

import android.content.Intent
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.TextView
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.button.MaterialButton
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

    /** Called when a suggested follow-up question chip is tapped */
    var onSuggestionClick: ((String) -> Unit)? = null
    
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
        private val recommendationHeader: android.widget.LinearLayout = itemView.findViewById(R.id.recommendationHeader)
        private val productsRecyclerView: RecyclerView = itemView.findViewById(R.id.productsRecyclerView)
        private val suggestedQuestionsChipGroup: LinearLayout = itemView.findViewById(R.id.suggestedQuestionsChipGroup)
        
        fun bind(message: ChatMessage) {
            // Hide text bubble completely when content is blank (e.g. response only has product cards)
            if (message.content.isBlank()) {
                messageText.visibility = View.GONE
                timestampText.visibility = View.GONE
            } else {
                messageText.visibility = View.VISIBLE
                timestampText.visibility = View.VISIBLE
                messageText.text = message.content
                timestampText.text = dateFormat.format(Date(message.timestamp))
            }

            // Display product cards if message contains products
            message.products?.let { products ->
                if (products.isNotEmpty()) {
                    recommendationHeader.visibility = View.VISIBLE
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
                    recommendationHeader.visibility = View.GONE
                    productsRecyclerView.visibility = View.GONE
                }
            } ?: run {
                recommendationHeader.visibility = View.GONE
                productsRecyclerView.visibility = View.GONE
            }

            // Display AI-generated suggested follow-up question chips
            val questions = message.suggestedQuestions
            if (!questions.isNullOrEmpty()) {
                suggestedQuestionsChipGroup.removeAllViews()
                val context = itemView.context
                val blueInt = androidx.core.content.ContextCompat.getColor(context, R.color.bestbuy_blue)
                val bgColor = androidx.core.content.ContextCompat.getColor(context, R.color.chip_bg)
                val dp6 = (context.resources.displayMetrics.density * 6).toInt()
                val dp12 = (context.resources.displayMetrics.density * 12).toInt()

                questions.forEach { question ->
                    val btn = MaterialButton(
                        context,
                        null,
                        com.google.android.material.R.attr.materialButtonOutlinedStyle
                    ).apply {
                        text = question
                        textSize = 13f
                        isSingleLine = false  // native multi-line support
                        setTextColor(blueInt)
                        backgroundTintList = android.content.res.ColorStateList.valueOf(bgColor)
                        strokeColor = android.content.res.ColorStateList.valueOf(blueInt)
                        strokeWidth = (context.resources.displayMetrics.density * 1.5f).toInt()
                        cornerRadius = (context.resources.displayMetrics.density * 20).toInt()
                        setPadding(dp12, dp6, dp12, dp6)
                        setOnClickListener { onSuggestionClick?.invoke(question) }
                    }

                    val lp = LinearLayout.LayoutParams(
                        LinearLayout.LayoutParams.MATCH_PARENT,
                        LinearLayout.LayoutParams.WRAP_CONTENT
                    ).also { it.bottomMargin = dp6 }
                    suggestedQuestionsChipGroup.addView(btn, lp)
                }
                suggestedQuestionsChipGroup.visibility = View.VISIBLE
            } else {
                suggestedQuestionsChipGroup.visibility = View.GONE
            }
        }
    }
}
