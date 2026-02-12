package com.bestbuy.scanner.utils

import android.util.Log

/**
 * API 調試工具
 */
object ApiDebugHelper {
    
    private const val TAG = "BestBuyAPI"
    
    /**
     * 記錄 API 請求
     */
    fun logRequest(endpoint: String, params: Map<String, String>) {
        Log.d(TAG, "=== API Request ===")
        Log.d(TAG, "Endpoint: $endpoint")
        params.forEach { (key, value) ->
            // 不記錄完整的 API Key，只顯示前後幾個字符
            val displayValue = if (key == "apiKey" && value.length > 8) {
                "${value.take(4)}...${value.takeLast(4)}"
            } else {
                value
            }
            Log.d(TAG, "$key: $displayValue")
        }
    }
    
    /**
     * 記錄 API 回應
     */
    fun logResponse(code: Int, message: String, body: String?) {
        Log.d(TAG, "=== API Response ===")
        Log.d(TAG, "Code: $code")
        Log.d(TAG, "Message: $message")
        if (body != null) {
            Log.d(TAG, "Body: ${body.take(500)}${if (body.length > 500) "..." else ""}")
        }
    }
    
    /**
     * 記錄錯誤
     */
    fun logError(error: String, exception: Exception? = null) {
        Log.e(TAG, "=== API Error ===")
        Log.e(TAG, "Error: $error")
        exception?.let {
            Log.e(TAG, "Exception: ${it.javaClass.simpleName}")
            Log.e(TAG, "Message: ${it.message}")
            Log.e(TAG, "Stack trace:", it)
        }
    }
    
    /**
     * 驗證 UPC 格式
     */
    fun validateUPC(upc: String): ValidationResult {
        val cleanUpc = upc.trim()
        
        return when {
            cleanUpc.isEmpty() -> {
                ValidationResult(false, "UPC 不能為空")
            }
            cleanUpc.length < 8 -> {
                ValidationResult(false, "UPC 長度過短（至少需要 8 位數字）")
            }
            cleanUpc.length > 14 -> {
                ValidationResult(false, "UPC 長度過長（最多 14 位數字）")
            }
            !cleanUpc.all { it.isDigit() } -> {
                ValidationResult(false, "UPC 只能包含數字")
            }
            else -> {
                ValidationResult(true, "UPC 格式正確")
            }
        }
    }
    
    /**
     * 驗證結果
     */
    data class ValidationResult(
        val isValid: Boolean,
        val message: String
    )
    
    /**
     * 建構 BestBuy API URL（用於調試）
     */
    fun buildApiUrl(baseUrl: String, search: String, apiKey: String): String {
        val maskedKey = "${apiKey.take(4)}...${apiKey.takeLast(4)}"
        return "$baseUrl?search=$search&apiKey=$maskedKey&format=json"
    }
}
