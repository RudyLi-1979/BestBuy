package com.bestbuy.scanner.ui

import android.content.Intent
import android.os.Bundle
import android.view.View
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.ViewModelProvider
import androidx.recyclerview.widget.LinearLayoutManager
import com.bestbuy.scanner.databinding.ActivityCartBinding
import com.bestbuy.scanner.ui.adapter.CartAdapter
import com.bestbuy.scanner.ui.viewmodel.CartViewModel
import java.text.NumberFormat
import java.util.Locale

/**
 * Shopping cart activity
 */
class CartActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivityCartBinding
    private lateinit var viewModel: CartViewModel
    private lateinit var adapter: CartAdapter
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityCartBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        viewModel = ViewModelProvider(this)[CartViewModel::class.java]
        
        setupToolbar()
        setupRecyclerView()
        setupObservers()
        setupButtons()
    }
    
    private fun setupToolbar() {
        setSupportActionBar(binding.toolbar)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.setDisplayShowHomeEnabled(true)
        binding.toolbar.setNavigationOnClickListener {
            finish()
        }
    }
    
    private fun setupRecyclerView() {
        adapter = CartAdapter(
            onQuantityChanged = { item, newQuantity ->
                viewModel.updateQuantity(item, newQuantity)
            },
            onRemoveClicked = { item ->
                showRemoveConfirmation(item)
            },
            onItemClicked = { item ->
                // Navigate to product detail page
                val intent = Intent(this, ProductDetailActivity::class.java)
                intent.putExtra("PRODUCT_SKU", item.sku.toString())  // Convert Int to String
                startActivity(intent)
            }
        )
        
        binding.rvCartItems.layoutManager = LinearLayoutManager(this)
        binding.rvCartItems.adapter = adapter
    }
    
    private fun setupObservers() {
        val priceFormat = NumberFormat.getCurrencyInstance(Locale.US)

        // Observe cart items
        viewModel.cartItems.observe(this) { items ->
            adapter.submitList(items)

            // Show/hide empty state — bottom bar is ALWAYS visible
            if (items.isEmpty()) {
                binding.emptyView.visibility = View.VISIBLE
                binding.rvCartItems.visibility = View.GONE
            } else {
                binding.emptyView.visibility = View.GONE
                binding.rvCartItems.visibility = View.VISIBLE
            }
            binding.bottomBar.visibility = View.VISIBLE

            // Update item count
            val count = items.sumOf { it.quantity }
            binding.tvItemCount.text = if (count == 0) "0 items"
                                       else if (count == 1) "1 item"
                                       else "$count items"
        }

        // Observe total price
        viewModel.totalPrice.observe(this) { total ->
            binding.tvTotalPrice.text = priceFormat.format(total)
        }

        // Observe total savings — show green "You Save" banner when > 0
        viewModel.totalSavings.observe(this) { savings ->
            if (savings > 0.0) {
                binding.savingsRow.visibility = View.VISIBLE
                binding.tvTotalSavings.text = "-${priceFormat.format(savings)}"
            } else {
                binding.savingsRow.visibility = View.GONE
            }
        }
    }
    
    private fun setupButtons() {
        // Clear cart button
        binding.btnClearCart.setOnClickListener {
            showClearCartConfirmation()
        }
        
        // Checkout button
        binding.btnCheckout.setOnClickListener {
            showCheckoutDialog()
        }
    }
    
    private fun showRemoveConfirmation(item: com.bestbuy.scanner.data.model.CartItem) {
        AlertDialog.Builder(this)
            .setTitle("Remove Item")
            .setMessage("Remove \"${item.name}\" from cart?")
            .setPositiveButton("Remove") { _, _ ->
                viewModel.removeItem(item)
            }
            .setNegativeButton("Cancel", null)
            .show()
    }
    
    private fun showClearCartConfirmation() {
        AlertDialog.Builder(this)
            .setTitle("Clear Cart")
            .setMessage("Remove all items from cart?")
            .setPositiveButton("Clear") { _, _ ->
                viewModel.clearCart()
            }
            .setNegativeButton("Cancel", null)
            .show()
    }
    
    private fun showCheckoutDialog() {
        val priceFormat = NumberFormat.getCurrencyInstance(Locale.US)
        val total = viewModel.totalPrice.value ?: 0.0
        
        AlertDialog.Builder(this)
            .setTitle("Checkout")
            .setMessage("Total: ${priceFormat.format(total)}\n\nThis is a demo app. No actual payment will be processed.")
            .setPositiveButton("OK") { _, _ ->
                // Clear cart after "checkout"
                viewModel.clearCart()
                finish()
            }
            .setNegativeButton("Cancel", null)
            .show()
    }
}
