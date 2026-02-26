package com.bestbuy.scanner.ui

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.speech.RecognizerIntent
import android.view.MenuItem
import android.view.View
import android.widget.EditText
import android.widget.ImageButton
import android.widget.ProgressBar
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.bestbuy.scanner.R
import com.bestbuy.scanner.ui.adapter.ChatAdapter
import com.bestbuy.scanner.ui.viewmodel.CartViewModel
import com.bestbuy.scanner.ui.viewmodel.ChatViewModel
import kotlinx.coroutines.launch
import java.util.Locale

/**
 * Chat Activity - AI Shopping Assistant (Main Entry Point)
 * Provides conversational shopping experience using UCP Server and Gemini AI
 */
class ChatActivity : AppCompatActivity() {
    
    private lateinit var messagesRecyclerView: RecyclerView
    private lateinit var messageInput: EditText
    private lateinit var sendButton: ImageButton
    private lateinit var voiceInputButton: ImageButton
    private lateinit var scanButton: ImageButton
    private lateinit var loadingIndicator: ProgressBar
    private lateinit var cartBadgeTextView: android.widget.TextView
    private lateinit var cartTotalTextView: android.widget.TextView
    
    private val chatViewModel: ChatViewModel by viewModels()
    private val cartViewModel: CartViewModel by viewModels()
    private val chatAdapter = ChatAdapter()
    
    // Activity Result Launchers
    private val voiceInputLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == RESULT_OK) {
            val spokenText = result.data?.getStringArrayListExtra(
                RecognizerIntent.EXTRA_RESULTS
            )?.firstOrNull()
            
            spokenText?.let {
                messageInput.setText(it)
                messageInput.setSelection(it.length) // Move cursor to end
            }
        }
    }
    
    private val scanBarcodeLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == RESULT_OK) {
            val scannedUpc = result.data?.getStringExtra("SCANNED_UPC")
            val productName = result.data?.getStringExtra("PRODUCT_NAME")
            
            if (scannedUpc != null && productName != null) {
                // Auto-send message about scanned product
                val message = "I just scanned: $productName (UPC: $scannedUpc). Can you tell me more about it?"
                chatViewModel.sendMessage(message)
            }
        }
    }
    
    private val requestAudioPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (isGranted) {
            startVoiceInput()
        } else {
            Toast.makeText(
                this,
                "Microphone permission is required for voice input",
                Toast.LENGTH_SHORT
            ).show()
        }
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_chat)

        // Setup Toolbar
        val toolbar = findViewById<androidx.appcompat.widget.Toolbar>(R.id.chatToolbar)
        setSupportActionBar(toolbar)

        // Cart button in toolbar
        cartBadgeTextView = toolbar.findViewById(R.id.cartBadge)
        cartTotalTextView = toolbar.findViewById(R.id.cartTotal)
        toolbar.findViewById<android.view.View>(R.id.cartButton).setOnClickListener {
            startActivity(Intent(this, CartActivity::class.java))
        }
        
        // Clear conversation button
        toolbar.findViewById<android.widget.ImageButton>(R.id.clearChatButton).setOnClickListener {
            showClearChatConfirmDialog()
        }

        // Suggestion chip click → auto-fill messageInput and send
        chatAdapter.onSuggestionClick = { question ->
            messageInput.setText(question)
            sendMessage()
        }

        // Initialize views
        messagesRecyclerView = findViewById(R.id.messagesRecyclerView)
        messageInput = findViewById(R.id.messageInput)
        sendButton = findViewById(R.id.sendButton)
        voiceInputButton = findViewById(R.id.voiceInputButton)
        scanButton = findViewById(R.id.scanButton)
        loadingIndicator = findViewById(R.id.loadingIndicator)
        
        // Setup RecyclerView
        messagesRecyclerView.apply {
            adapter = chatAdapter
            layoutManager = LinearLayoutManager(this@ChatActivity).apply {
                stackFromEnd = true // Start from bottom
            }
        }
        
        // Setup click listeners
        sendButton.setOnClickListener {
            sendMessage()
        }
        
        voiceInputButton.setOnClickListener {
            checkAudioPermissionAndStartVoiceInput()
        }
        
        scanButton.setOnClickListener {
            startBarcodeScanner()
        }
        
        // Setup observers
        setupObservers()
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            R.id.action_cart -> {
                startActivity(Intent(this, CartActivity::class.java))
                true
            }
            else -> super.onOptionsItemSelected(item)
        }
    }

    /**
     * Update the cart badge count
     */
    private fun updateCartBadge(count: Int) {
        cartBadgeTextView.text = count.toString()
    }
    
    /**
     * Setup observers for ViewModel state
     */
    private fun setupObservers() {
        // Observe cart item count (LiveData) – updates badge in ActionBar
        cartViewModel.itemCount.observe(this) { count ->
            updateCartBadge(count ?: 0)
        }

        // Observe cart total price – updates total text below cart icon
        cartViewModel.totalPrice.observe(this) { total ->
            val fmt = java.text.NumberFormat.getCurrencyInstance(java.util.Locale.US)
            cartTotalTextView.text = fmt.format(total ?: 0.0)
        }

        lifecycleScope.launch {
            // Observe messages
            chatViewModel.messages.collect { messages ->
                chatAdapter.submitList(messages)
                if (messages.isNotEmpty()) {
                    // First post: RecyclerView positions the last item into view.
                    // Second post (via Handler 250ms): fires after the nested product-
                    // card RecyclerView and suggestion chips have been measured, so
                    // the full message height is known and we can scroll to the bottom.
                    messagesRecyclerView.post {
                        messagesRecyclerView.scrollToPosition(messages.size - 1)
                    }
                    messagesRecyclerView.postDelayed({
                        messagesRecyclerView.smoothScrollToPosition(messages.size - 1)
                    }, 250)
                }
            }
        }
        
        lifecycleScope.launch {
            // Observe loading state
            chatViewModel.isLoading.collect { isLoading ->
                loadingIndicator.visibility = if (isLoading) View.VISIBLE else View.GONE
                sendButton.isEnabled = !isLoading
                voiceInputButton.isEnabled = !isLoading
                scanButton.isEnabled = !isLoading
            }
        }
        
        lifecycleScope.launch {
            // Observe error messages
            chatViewModel.errorMessage.collect { error ->
                error?.let {
                    Toast.makeText(this@ChatActivity, it, Toast.LENGTH_LONG).show()
                    chatViewModel.clearError()
                }
            }
        }
    }
    
    /**
     * Send message to AI assistant
     */
    private fun showClearChatConfirmDialog() {
        androidx.appcompat.app.AlertDialog.Builder(this)
            .setTitle(R.string.clear_chat_title)
            .setMessage(R.string.clear_chat_message)
            .setPositiveButton(R.string.clear_chat_confirm) { _, _ ->
                chatViewModel.clearChat()
            }
            .setNegativeButton(R.string.cancel, null)
            .show()
    }

    private fun sendMessage() {
        val message = messageInput.text.toString().trim()
        if (message.isEmpty()) {
            Toast.makeText(this, "Please enter a message", Toast.LENGTH_SHORT).show()
            return
        }
        
        // Clear input
        messageInput.text.clear()
        
        // Send to ViewModel
        chatViewModel.sendMessage(message)
    }
    
    /**
     * Check audio permission and start voice input
     */
    private fun checkAudioPermissionAndStartVoiceInput() {
        when {
            ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.RECORD_AUDIO
            ) == PackageManager.PERMISSION_GRANTED -> {
                startVoiceInput()
            }
            else -> {
                requestAudioPermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
            }
        }
    }
    
    /**
     * Start voice input using Speech Recognition
     */
    private fun startVoiceInput() {
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
            )
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.getDefault())
            putExtra(RecognizerIntent.EXTRA_PROMPT, "Speak now...")
        }
        
        try {
            voiceInputLauncher.launch(intent)
        } catch (e: Exception) {
            Toast.makeText(
                this,
                "Speech recognition not supported on this device",
                Toast.LENGTH_SHORT
            ).show()
        }
    }
    
    /**
     * Start barcode scanner activity
     */
    private fun startBarcodeScanner() {
        val intent = Intent(this, MainActivity::class.java)
        scanBarcodeLauncher.launch(intent)
    }
}
