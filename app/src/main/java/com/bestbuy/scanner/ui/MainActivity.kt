package com.bestbuy.scanner.ui

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.util.Log
import android.view.Menu
import android.view.MenuItem
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.core.content.ContextCompat
import androidx.lifecycle.ViewModelProvider
import com.bestbuy.scanner.databinding.ActivityMainBinding
import com.bestbuy.scanner.ui.viewmodel.CartViewModel
import com.bestbuy.scanner.ui.viewmodel.ProductViewModel
import com.bestbuy.scanner.ui.viewmodel.RecommendationViewModel
import com.bestbuy.scanner.utils.ApiDebugHelper
import com.bestbuy.scanner.utils.BarcodeScannerAnalyzer
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

/**
 * Main Activity - Barcode scanning interface
 */
class MainActivity : AppCompatActivity() {
    
    companion object {
        private const val TAG = "MainActivity"
    }
    
    private lateinit var binding: ActivityMainBinding
    private lateinit var viewModel: ProductViewModel
    private lateinit var cartViewModel: CartViewModel
    private lateinit var recommendationViewModel: RecommendationViewModel
    private lateinit var cameraExecutor: ExecutorService
    private var isNavigating = false  // Prevent duplicate navigation
    
    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (isGranted) {
            startCamera()
        } else {
            Toast.makeText(
                this,
                getString(com.bestbuy.scanner.R.string.camera_permission_required),
                Toast.LENGTH_SHORT
            ).show()
        }
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        // Initialize ViewModels
        viewModel = ViewModelProvider(this)[ProductViewModel::class.java]
        cartViewModel = ViewModelProvider(this)[CartViewModel::class.java]
        recommendationViewModel = ViewModelProvider(this)[RecommendationViewModel::class.java]
        
        // Initialize camera executor
        cameraExecutor = Executors.newSingleThreadExecutor()
        
        // Setup UI
        setupObservers()
        checkCameraPermission()
        
        // Manual input button
        binding.btnManualInput.setOnClickListener {
            showManualInputDialog()
        }
    }
    
    override fun onResume() {
        super.onResume()
        // Reset navigation flag to allow next scan
        isNavigating = false
    }
    
    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menuInflater.inflate(com.bestbuy.scanner.R.menu.menu_main, menu)
        return true
    }
    
    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            com.bestbuy.scanner.R.id.action_cart -> {
                startActivity(Intent(this, CartActivity::class.java))
                true
            }
            else -> super.onOptionsItemSelected(item)
        }
    }
    
    private fun setupObservers() {
        viewModel.product.observe(this) { product ->
            if (product != null && !isNavigating) {
                // Prevent duplicate navigation
                isNavigating = true
                
                // Track scan interaction
                recommendationViewModel.trackScan(product)
                
                // Product found, navigate to product detail page with product object
                val intent = Intent(this, ProductDetailActivity::class.java)
                intent.putExtra("PRODUCT_DATA", product)
                startActivity(intent)
                
                // Clear product data for next scan
                viewModel.clearProduct()
            }
        }
        
        viewModel.loading.observe(this) { isLoading ->
            if (isLoading) {
                binding.tvStatus.text = getString(com.bestbuy.scanner.R.string.searching)
                binding.progressBar.visibility = android.view.View.VISIBLE
            } else {
                binding.tvStatus.text = getString(com.bestbuy.scanner.R.string.scan_instruction)
                binding.progressBar.visibility = android.view.View.GONE
            }
        }
        
        viewModel.error.observe(this) { error ->
            if (error != null) {
                Log.e(TAG, "Error from ViewModel: $error")
                
                // Provide user-friendly error messages based on error type
                val userMessage = when {
                    error.contains("400") -> "Bad request format, please check API settings"
                    error.contains("401") -> "Invalid API Key, please check settings"
                    error.contains("404") || error.contains("找不到產品") -> "Product not found"
                    error.contains("網路") || error.contains("Network") -> "Network connection failed"
                    error.contains("timeout") -> "Request timeout, please try again later"
                    else -> "Search failed: $error"
                }
                
                Toast.makeText(this, userMessage, Toast.LENGTH_LONG).show()
                binding.tvStatus.text = userMessage
            }
        }
    }
    
    private fun checkCameraPermission() {
        when {
            ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.CAMERA
            ) == PackageManager.PERMISSION_GRANTED -> {
                startCamera()
            }
            else -> {
                requestPermissionLauncher.launch(Manifest.permission.CAMERA)
            }
        }
    }
    
    private fun startCamera() {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(this)
        
        cameraProviderFuture.addListener({
            val cameraProvider = cameraProviderFuture.get()
            
            // Preview
            val preview = Preview.Builder()
                .build()
                .also {
                    it.setSurfaceProvider(binding.previewView.surfaceProvider)
                }
            
            // Image analysis
            val imageAnalyzer = ImageAnalysis.Builder()
                .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                .build()
                .also {
                    it.setAnalyzer(
                        cameraExecutor,
                        BarcodeScannerAnalyzer { barcode ->
                            runOnUiThread {
                                onBarcodeScanned(barcode)
                            }
                        }
                    )
                }
            
            // Select back camera
            val cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA
            
            try {
                cameraProvider.unbindAll()
                cameraProvider.bindToLifecycle(
                    this,
                    cameraSelector,
                    preview,
                    imageAnalyzer
                )
            } catch (e: Exception) {
                Toast.makeText(
                    this,
                    "Camera failed to start: ${e.message}",
                    Toast.LENGTH_SHORT
                ).show()
            }
            
        }, ContextCompat.getMainExecutor(this))
    }
    
    private fun onBarcodeScanned(barcode: String) {
        Log.d(TAG, "===========================================")
        Log.d(TAG, "=== Barcode Scanned ===")
        Log.d(TAG, "Raw barcode: [$barcode]")
        Log.d(TAG, "Length: ${barcode.length} digits")
        Log.d(TAG, "Type: ${when(barcode.length) {
            8 -> "EAN-8"
            12 -> "UPC-A"
            13 -> "EAN-13"
            14 -> "ITF-14"
            else -> "Unknown (${barcode.length} digits)"
        }}")
        Log.d(TAG, "Is numeric: ${barcode.all { it.isDigit() }}")
        Log.d(TAG, "===========================================")
        
        // Display scanned barcode on UI
        binding.tvBarcode.text = "Scanned: $barcode (${barcode.length} digits)"
        
        // Validate UPC format
        val validation = ApiDebugHelper.validateUPC(barcode)
        if (!validation.isValid) {
            Log.w(TAG, "❌ Invalid UPC: ${validation.message}")
            binding.tvStatus.text = "Invalid barcode: ${validation.message}"
            Toast.makeText(this, validation.message, Toast.LENGTH_SHORT).show()
            return
        }
        
        Log.d(TAG, "✅ UPC validation passed, searching for product...")
        binding.tvStatus.text = "Searching for product (UPC: $barcode)..."
        
        // Search product via ViewModel
        viewModel.searchProductByUPC(barcode)
    }
    
    private fun showManualInputDialog() {
        val builder = android.app.AlertDialog.Builder(this)
        builder.setTitle("Manual UPC Input")
        
        val input = android.widget.EditText(this)
        input.inputType = android.text.InputType.TYPE_CLASS_NUMBER
        builder.setView(input)
        
        builder.setPositiveButton("Search") { _, _ ->
            val upc = input.text.toString()
            if (upc.isNotEmpty()) {
                onBarcodeScanned(upc)
            }
        }
        builder.setNegativeButton("Cancel") { dialog, _ ->
            dialog.cancel()
        }
        
        builder.show()
    }
    
    override fun onDestroy() {
        super.onDestroy()
        cameraExecutor.shutdown()
    }
}
