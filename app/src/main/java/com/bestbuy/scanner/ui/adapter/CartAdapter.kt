package com.bestbuy.scanner.ui.adapter

import android.graphics.Paint
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.bestbuy.scanner.data.model.CartItem
import com.bestbuy.scanner.databinding.ItemCartBinding
import com.bumptech.glide.Glide
import java.text.NumberFormat
import java.util.Locale

/**
 * Adapter for shopping cart items
 */
class CartAdapter(
    private val onQuantityChanged: (CartItem, Int) -> Unit,
    private val onRemoveClicked: (CartItem) -> Unit,
    private val onItemClicked: (CartItem) -> Unit
) : ListAdapter<CartItem, CartAdapter.CartViewHolder>(CartDiffCallback()) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): CartViewHolder {
        val binding = ItemCartBinding.inflate(
            LayoutInflater.from(parent.context),
            parent,
            false
        )
        return CartViewHolder(binding, onQuantityChanged, onRemoveClicked, onItemClicked)
    }

    override fun onBindViewHolder(holder: CartViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    class CartViewHolder(
        private val binding: ItemCartBinding,
        private val onQuantityChanged: (CartItem, Int) -> Unit,
        private val onRemoveClicked: (CartItem) -> Unit,
        private val onItemClicked: (CartItem) -> Unit
    ) : RecyclerView.ViewHolder(binding.root) {

        fun bind(item: CartItem) {
            binding.apply {
                // Product name
                tvProductName.text = item.name

                val priceFormat = NumberFormat.getCurrencyInstance(Locale.US)

                // ============================================================
                // On Sale: show badge, strikethrough original price, sale price
                // ============================================================
                if (item.onSale && item.regularPrice > item.price) {
                    // Show red "ON SALE" badge
                    tvOnSaleBadge.visibility = View.VISIBLE

                    // Show original price with strikethrough
                    tvOriginalPrice.visibility = View.VISIBLE
                    tvOriginalPrice.text = priceFormat.format(item.regularPrice)
                    tvOriginalPrice.paintFlags =
                        tvOriginalPrice.paintFlags or Paint.STRIKE_THRU_TEXT_FLAG

                    // Sale price in primary blue
                    tvPrice.text = priceFormat.format(item.price)
                } else {
                    tvOnSaleBadge.visibility = View.GONE
                    tvOriginalPrice.visibility = View.GONE
                    tvPrice.text = priceFormat.format(item.price)
                }

                // Quantity
                tvQuantity.text = item.quantity.toString()

                // Subtotal
                val subtotal = item.price * item.quantity
                tvSubtotal.text = "Subtotal: ${priceFormat.format(subtotal)}"

                // Product image
                if (!item.imageUrl.isNullOrEmpty()) {
                    Glide.with(ivProductImage.context)
                        .load(item.imageUrl)
                        .into(ivProductImage)
                } else {
                    ivProductImage.setImageResource(android.R.drawable.ic_menu_gallery)
                }

                // Quantity controls
                btnIncrease.setOnClickListener {
                    onQuantityChanged(item, item.quantity + 1)
                }

                btnDecrease.setOnClickListener {
                    onQuantityChanged(item, item.quantity - 1)
                }

                // Remove button
                btnRemove.setOnClickListener {
                    onRemoveClicked(item)
                }

                // Item click - navigate to product details
                root.setOnClickListener {
                    onItemClicked(item)
                }
            }
        }
    }

    private class CartDiffCallback : DiffUtil.ItemCallback<CartItem>() {
        override fun areItemsTheSame(oldItem: CartItem, newItem: CartItem): Boolean {
            return oldItem.sku == newItem.sku
        }

        override fun areContentsTheSame(oldItem: CartItem, newItem: CartItem): Boolean {
            return oldItem == newItem
        }
    }
}
