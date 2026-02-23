package com.bestbuy.scanner.ui

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.text.Html
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.ViewModelProvider
import androidx.recyclerview.widget.LinearLayoutManager
import com.bestbuy.scanner.databinding.ActivityProductDetailBinding
import com.bestbuy.scanner.data.model.Product
import com.bestbuy.scanner.ui.adapter.PersonalizedRecommendationAdapter
import com.bestbuy.scanner.ui.adapter.RecommendationAdapter
import com.bestbuy.scanner.ui.viewmodel.CartViewModel
import com.bestbuy.scanner.ui.viewmodel.ProductViewModel
import com.bestbuy.scanner.ui.viewmodel.RecommendationViewModel
import com.bumptech.glide.Glide
import java.text.NumberFormat
import java.util.Locale

/**
 * Product Detail Activity
 */
class ProductDetailActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivityProductDetailBinding
    private lateinit var viewModel: ProductViewModel
    private lateinit var cartViewModel: CartViewModel
    private lateinit var recommendationViewModel: RecommendationViewModel
    private lateinit var recommendationAdapter: RecommendationAdapter
    private lateinit var alsoViewedAdapter: RecommendationAdapter
    private lateinit var forYouAdapter: PersonalizedRecommendationAdapter
    private var hasLoadedRecommendations = false  // Prevent duplicate recommendation loading
    private var currentProduct: Product? = null  // Track current product for behavior tracking
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityProductDetailBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        viewModel = ViewModelProvider(this)[ProductViewModel::class.java]
        cartViewModel = ViewModelProvider(this)[CartViewModel::class.java]
        recommendationViewModel = ViewModelProvider(this)[RecommendationViewModel::class.java]
        
        setupToolbar()
        setupRecyclerViews()
        setupObservers()
        
        // Load product data from Intent
        // Support two ways: PRODUCT_DATA (from scanner) or PRODUCT_SKU (from recommendations)
        @Suppress("DEPRECATION")
        val product = intent.getSerializableExtra("PRODUCT_DATA") as? Product
        val productSku = intent.getStringExtra("PRODUCT_SKU")
        
        if (product != null) {
            // Product data passed directly (from scanner)
            android.util.Log.d("ProductDetailActivity", "=========================================")
            android.util.Log.d("ProductDetailActivity", "📱 Displaying product details (from PRODUCT_DATA)")
            android.util.Log.d("ProductDetailActivity", "SKU: ${product.sku}")
            android.util.Log.d("ProductDetailActivity", "Name: ${product.name}")
            android.util.Log.d("ProductDetailActivity", "=========================================")
            
            // Display product directly
            displayProduct(product)
            
            // Load recommendations
            product.sku?.let { sku ->
                android.util.Log.d("ProductDetailActivity", "🔍 Requesting recommendations (SKU: $sku)")
                viewModel.loadRecommendations(sku.toString())
            }
        } else if (!productSku.isNullOrEmpty()) {
            // Only SKU passed (from recommendation click)
            android.util.Log.d("ProductDetailActivity", "=========================================")
            android.util.Log.d("ProductDetailActivity", "📱 Loading product by SKU: $productSku")
            android.util.Log.d("ProductDetailActivity", "=========================================")
            
            // Fetch product by SKU
            viewModel.getProductBySKU(productSku)
        } else {
            Toast.makeText(this, "Product information error", Toast.LENGTH_SHORT).show()
            finish()
        }
    }
    
    private fun setupToolbar() {
        setSupportActionBar(binding.toolbar)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.setDisplayShowHomeEnabled(true)
        binding.toolbar.setNavigationOnClickListener {
            finish()
        }
    }
    
    private fun setupRecyclerViews() {
        // Personalized Recommendations (For You)
        forYouAdapter = PersonalizedRecommendationAdapter { product ->
            // Click on personalized recommendation to open product detail
            product.sku?.let { sku ->
                val intent = Intent(this, ProductDetailActivity::class.java)
                intent.putExtra("PRODUCT_SKU", sku.toString())
                startActivity(intent)
            }
        }
        binding.rvForYou.layoutManager = LinearLayoutManager(
            this,
            LinearLayoutManager.HORIZONTAL,
            false
        )
        binding.rvForYou.adapter = forYouAdapter
        
        // Recommendations
        recommendationAdapter = RecommendationAdapter { product ->
            // Click on recommendation to open new product detail page
            product.sku?.let { sku ->
                val intent = Intent(this, ProductDetailActivity::class.java)
                intent.putExtra("PRODUCT_SKU", sku)
                startActivity(intent)
            }
        }
        binding.rvRecommendations.layoutManager = LinearLayoutManager(
            this,
            LinearLayoutManager.HORIZONTAL,
            false
        )
        binding.rvRecommendations.adapter = recommendationAdapter
        
        // Also Viewed
        alsoViewedAdapter = RecommendationAdapter { product ->
            product.sku?.let { sku ->
                val intent = Intent(this, ProductDetailActivity::class.java)
                intent.putExtra("PRODUCT_SKU", sku)
                startActivity(intent)
            }
        }
        binding.rvAlsoViewed.layoutManager = LinearLayoutManager(
            this,
            LinearLayoutManager.HORIZONTAL,
            false
        )
        binding.rvAlsoViewed.adapter = alsoViewedAdapter
    }
    
    private fun setupObservers() {
        viewModel.product.observe(this) { product ->
            android.util.Log.d("ProductDetailActivity", "🔔 product observer triggered")
            android.util.Log.d("ProductDetailActivity", "Product is null: ${product == null}")
            if (product != null) {
                displayProduct(product)
            }
        }
        
        // Observe combined recommendations (Also Viewed + Similar Products)
        viewModel.recommendations.observe(this) { recommendations ->
            if (recommendations.isNotEmpty()) {
                // Show recommendations section
                binding.tvRecommendationsTitle.visibility = View.VISIBLE
                binding.rvRecommendations.visibility = View.VISIBLE
                
                // Hide "Also Viewed" section (now merged into Recommendations)
                binding.tvAlsoViewedTitle.visibility = View.GONE
                binding.rvAlsoViewed.visibility = View.GONE
                
                // Display combined recommendations
                recommendationAdapter.submitList(recommendations)
            } else {
                // Hide when no recommendations
                binding.tvRecommendationsTitle.visibility = View.GONE
                binding.rvRecommendations.visibility = View.GONE
                binding.tvAlsoViewedTitle.visibility = View.GONE
                binding.rvAlsoViewed.visibility = View.GONE
            }
        }
        
        // Observe personalized recommendations (For You)
        recommendationViewModel.recommendations.observe(this) { personalizedRecs ->
            if (personalizedRecs.isNotEmpty()) {
                // Show "For You" section
                binding.tvForYouTitle.visibility = View.VISIBLE
                binding.rvForYou.visibility = View.VISIBLE
                binding.dividerForYou.visibility = View.VISIBLE
                
                // Display personalized recommendations
                forYouAdapter.submitList(personalizedRecs)
            } else {
                // Hide when no personalized recommendations
                binding.tvForYouTitle.visibility = View.GONE
                binding.rvForYou.visibility = View.GONE
                binding.dividerForYou.visibility = View.GONE
            }
        }
        

        viewModel.loading.observe(this) { isLoading ->
            binding.progressBar.visibility = if (isLoading) View.VISIBLE else View.GONE
            binding.scrollView.visibility = if (isLoading) View.GONE else View.VISIBLE
        }
        
        viewModel.error.observe(this) { error ->
            if (error != null) {
                Toast.makeText(this, "Error: $error", Toast.LENGTH_SHORT).show()
            }
        }
    }
    
    private fun displayProduct(product: com.bestbuy.scanner.data.model.Product) {
        android.util.Log.d("ProductDetailActivity", "=========================================")
        android.util.Log.d("ProductDetailActivity", "📺 displayProduct called")
        android.util.Log.d("ProductDetailActivity", "Product Name: ${product.name}")
        android.util.Log.d("ProductDetailActivity", "Product SKU: ${product.sku}")
        android.util.Log.d("ProductDetailActivity", "=========================================")
        
        // Track user viewing this product
        currentProduct = product
        recommendationViewModel.trackView(product)
        
        // Load personalized recommendations
        recommendationViewModel.loadRecommendations()
        
        // Product name
        binding.tvProductName.text = product.name ?: "Unknown Product"
        supportActionBar?.title = product.name
        
        // Manufacturer
        binding.tvManufacturer.text = product.manufacturer ?: ""
        
        // Model number
        if (!product.modelNumber.isNullOrEmpty()) {
            binding.tvModelNumber.text = "Model: ${product.modelNumber}"
            binding.tvModelNumber.visibility = View.VISIBLE
        } else {
            binding.tvModelNumber.visibility = View.GONE
        }
        
        // Price
        val priceFormat = NumberFormat.getCurrencyInstance(Locale.US)
        if (product.onSale == true && product.salePrice != null) {
            binding.tvPrice.text = priceFormat.format(product.salePrice)
            binding.tvOriginalPrice.text = priceFormat.format(product.regularPrice)
            binding.tvOriginalPrice.visibility = View.VISIBLE
            binding.tvOriginalPrice.paintFlags = 
                binding.tvOriginalPrice.paintFlags or android.graphics.Paint.STRIKE_THRU_TEXT_FLAG
            binding.tvOnSale.visibility = View.VISIBLE
        } else {
            binding.tvPrice.text = priceFormat.format(product.regularPrice)
            binding.tvOriginalPrice.visibility = View.GONE
            binding.tvOnSale.visibility = View.GONE
        }
        
        // Product image
        val imageUrl = product.largeFrontImage ?: product.image ?: product.mediumImage
        if (!imageUrl.isNullOrEmpty()) {
            Glide.with(this)
                .load(imageUrl)
                .into(binding.ivProductImage)
        }
        
        // Rating
        if (product.customerReviewAverage != null && product.customerReviewCount != null) {
            binding.tvRating.text = String.format(
                "%.1f ★ (%d reviews)",
                product.customerReviewAverage,
                product.customerReviewCount
            )
            binding.tvRating.visibility = View.VISIBLE
        } else {
            binding.tvRating.visibility = View.GONE
        }
        
        // Availability status
        val availabilityText = when {
            product.onlineAvailability == true && product.inStoreAvailability == true -> 
                getString(com.bestbuy.scanner.R.string.both_available)
            product.onlineAvailability == true -> getString(com.bestbuy.scanner.R.string.online_available)
            product.inStoreAvailability == true -> getString(com.bestbuy.scanner.R.string.store_available)
            else -> getString(com.bestbuy.scanner.R.string.out_of_stock)
        }
        binding.tvAvailability.text = "✓ $availabilityText"
        
        // Free shipping
        if (product.freeShipping == true) {
            binding.tvFreeShipping.text = "✓ ${getString(com.bestbuy.scanner.R.string.free_shipping)}"
            binding.tvFreeShipping.visibility = View.VISIBLE
        } else {
            binding.tvFreeShipping.visibility = View.GONE
        }
        
        // Product description
        val description = product.longDescription ?: product.shortDescription ?: "No product description"
        binding.tvDescription.text = if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.N) {
            Html.fromHtml(description, Html.FROM_HTML_MODE_COMPACT)
        } else {
            @Suppress("DEPRECATION")
            Html.fromHtml(description)
        }
        
        // UPC
        if (!product.upc.isNullOrEmpty()) {
            binding.tvUpc.text = "UPC: ${product.upc}"
            binding.tvUpc.visibility = View.VISIBLE
        }
        
        // View more button
        binding.btnViewOnBestBuy.setOnClickListener {
            product.productUrl?.let { url ->
                val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                startActivity(intent)
            }
        }
        
        // Add to cart button
        binding.btnAddToCart.setOnClickListener {
            cartViewModel.addToCart(product)
            
            // Track add to cart interaction
            recommendationViewModel.trackAddToCart(product)
            
            // Show confirmation with option to view cart
            com.google.android.material.snackbar.Snackbar.make(
                binding.root,
                "Added to cart",
                com.google.android.material.snackbar.Snackbar.LENGTH_LONG
            ).setAction("View Cart") {
                val intent = Intent(this, CartActivity::class.java)
                startActivity(intent)
            }.show()
        }
    }
}
