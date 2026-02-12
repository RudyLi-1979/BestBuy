package com.bestbuy.scanner.ui.adapter

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.TextView
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.bestbuy.scanner.R
import com.bestbuy.scanner.data.model.Product
import com.bumptech.glide.Glide
import java.text.NumberFormat
import java.util.Locale

/**
 * Adapter for displaying personalized product recommendations
 */
class PersonalizedRecommendationAdapter(
    private val onItemClick: (Product) -> Unit
) : ListAdapter<Product, PersonalizedRecommendationAdapter.ViewHolder>(ProductDiffCallback()) {
    
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_recommendation_card, parent, false)
        return ViewHolder(view)
    }
    
    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val product = getItem(position)
        holder.bind(product, onItemClick)
    }
    
    class ViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val ivProductImage: ImageView = itemView.findViewById(R.id.ivProductImage)
        private val tvProductName: TextView = itemView.findViewById(R.id.tvProductName)
        private val tvPrice: TextView = itemView.findViewById(R.id.tvPrice)
        private val tvRating: TextView = itemView.findViewById(R.id.tvRating)
        
        fun bind(product: Product, onItemClick: (Product) -> Unit) {
            // Product name
            tvProductName.text = product.name ?: "Unknown Product"
            
            // Price
            val priceFormat = NumberFormat.getCurrencyInstance(Locale.US)
            val price = product.salePrice ?: product.regularPrice
            tvPrice.text = if (price != null) {
                priceFormat.format(price)
            } else {
                "Price unavailable"
            }
            
            // Rating
            if (product.customerReviewAverage != null && product.customerReviewCount != null) {
                tvRating.text = String.format(
                    "%.1f ★ (%d)",
                    product.customerReviewAverage,
                    product.customerReviewCount
                )
                tvRating.visibility = View.VISIBLE
            } else {
                tvRating.visibility = View.GONE
            }
            
            // Product image
            val imageUrl = product.mediumImage ?: product.image ?: product.thumbnailImage
            if (!imageUrl.isNullOrEmpty()) {
                Glide.with(itemView.context)
                    .load(imageUrl)
                    .placeholder(R.drawable.ic_launcher_foreground)
                    .into(ivProductImage)
            }
            
            // Click listener
            itemView.setOnClickListener {
                onItemClick(product)
            }
        }
    }
    
    class ProductDiffCallback : DiffUtil.ItemCallback<Product>() {
        override fun areItemsTheSame(oldItem: Product, newItem: Product): Boolean {
            return oldItem.sku == newItem.sku
        }
        
        override fun areContentsTheSame(oldItem: Product, newItem: Product): Boolean {
            return oldItem == newItem
        }
    }
}
