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
            val price = product.salePrice ?: product.regularPrice
            if (price != null) {
                binding.tvPrice.text = priceFormat.format(price)
                
                // Show sale indicator if on sale
                if (product.onSale == true && product.salePrice != null && product.regularPrice != null) {
                    val savings = product.regularPrice - product.salePrice
                    if (savings > 0) {
                        // Could add a sale badge here if needed
                        binding.tvPrice.text = "${priceFormat.format(product.salePrice)} (Save ${priceFormat.format(savings)})"
                    }
                }
            } else {
                binding.tvPrice.text = "Price not available"
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
