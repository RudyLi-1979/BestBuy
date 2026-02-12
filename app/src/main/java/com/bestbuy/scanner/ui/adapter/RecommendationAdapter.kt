package com.bestbuy.scanner.ui.adapter

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.bestbuy.scanner.data.model.RecommendationProduct
import com.bestbuy.scanner.databinding.ItemProductRecommendationBinding
import com.bumptech.glide.Glide
import java.text.NumberFormat
import java.util.Locale

/**
 * 推薦商品 RecyclerView Adapter
 */
class RecommendationAdapter(
    private val onItemClick: (RecommendationProduct) -> Unit
) : ListAdapter<RecommendationProduct, RecommendationAdapter.ViewHolder>(ProductDiffCallback()) {
    
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
        private val onItemClick: (RecommendationProduct) -> Unit
    ) : RecyclerView.ViewHolder(binding.root) {
        
        fun bind(product: RecommendationProduct) {
            binding.tvProductName.text = product.names?.title ?: "未知產品"
            
            // 價格
            val priceFormat = NumberFormat.getCurrencyInstance(Locale.US)
            val price = product.prices?.current ?: product.prices?.regular
            if (price != null) {
                binding.tvPrice.text = priceFormat.format(price)
            } else {
                binding.tvPrice.text = "價格未提供"
            }
            
            // 圖片
            val imageUrl = product.images?.standard
            if (!imageUrl.isNullOrEmpty()) {
                Glide.with(binding.root.context)
                    .load(imageUrl)
                    .into(binding.ivProductImage)
            }
            
            // 點擊事件
            binding.root.setOnClickListener {
                onItemClick(product)
            }
        }
    }
    
    class ProductDiffCallback : DiffUtil.ItemCallback<RecommendationProduct>() {
        override fun areItemsTheSame(oldItem: RecommendationProduct, newItem: RecommendationProduct): Boolean {
            return oldItem.sku == newItem.sku
        }
        
        override fun areContentsTheSame(oldItem: RecommendationProduct, newItem: RecommendationProduct): Boolean {
            return oldItem == newItem
        }
    }
}
