package com.bestbuy.scanner.ui.adapter

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.bestbuy.scanner.data.model.Product
import com.bestbuy.scanner.databinding.ItemProductRecommendationBinding
import com.bumptech.glide.Glide
import java.text.NumberFormat
import java.util.Locale

/**
 * Adapter for displaying product cards in chat messages
 * Reuses the same layout as RecommendationAdapter for consistency
 */
class ChatProductAdapter(
    private val onItemClick: (Product) -> Unit
) : ListAdapter<Product, ChatProductAdapter.ViewHolder>(ProductDiffCallback()) {
    
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemProductRecommendationBinding.inflate(
            LayoutInflater.from(parent.context),
            parent,
            false
        )
        return ViewHolder(binding, onItemClick)
    }
    
    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(getItem(position))
    }
    
    class ViewHolder(
        private val binding: ItemProductRecommendationBinding,
        private val onItemClick: (Product) -> Unit
    ) : RecyclerView.ViewHolder(binding.root) {
        
        fun bind(product: Product) {
            // Product name
            binding.tvProductName.text = product.name ?: "Unknown Product"
            
            // Price formatting
            val priceFormat = NumberFormat.getCurrencyInstance(Locale.US)
            val salePrice = product.salePrice
            val regularPrice = product.regularPrice
            val isOnSale = product.onSale == true && salePrice != null && regularPrice != null && regularPrice > salePrice

            if (isOnSale) {
                // Sale price (bold, black)
                binding.tvPrice.text = priceFormat.format(salePrice)

                // Original price with strikethrough
                binding.tvOriginalPrice.text = priceFormat.format(regularPrice)
                binding.tvOriginalPrice.paintFlags =
                    binding.tvOriginalPrice.paintFlags or android.graphics.Paint.STRIKE_THRU_TEXT_FLAG
                binding.tvOriginalPrice.visibility = android.view.View.VISIBLE

                // Red sale badge: "Save $X"
                val savings = regularPrice!! - salePrice!!
                binding.tvSaleBadge.text = "Save ${priceFormat.format(savings)}"
                binding.tvSaleBadge.visibility = android.view.View.VISIBLE
            } else {
                val price = salePrice ?: regularPrice
                binding.tvPrice.text = if (price != null) priceFormat.format(price) else "Price not available"
                binding.tvOriginalPrice.visibility = android.view.View.GONE
                binding.tvSaleBadge.visibility = android.view.View.GONE
            }
            
            // Product image
            val imageUrl = product.image ?: product.thumbnailImage ?: product.mediumImage
            if (!imageUrl.isNullOrEmpty()) {
                Glide.with(binding.root.context)
                    .load(imageUrl)
                    .centerInside()
                    .into(binding.ivProductImage)
            } else {
                // Set placeholder if no image
                binding.ivProductImage.setImageResource(android.R.drawable.ic_menu_gallery)
            }
            
            // Click listener - open ProductDetailActivity
            binding.root.setOnClickListener {
                onItemClick(product)
            }

            // Star rating + sale badge visibility
            // ratingRow is always visible to keep consistent card height
            val rating = product.customerReviewAverage
            if (rating != null && rating > 0.0) {
                binding.tvStarIcon.visibility = android.view.View.VISIBLE
                binding.tvRating.text = String.format("%.1f", rating)
                binding.tvRating.visibility = android.view.View.VISIBLE
            } else {
                binding.tvStarIcon.visibility = android.view.View.INVISIBLE
                binding.tvRating.visibility = android.view.View.GONE
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
