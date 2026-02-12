package com.bestbuy.scanner.utils

import android.annotation.SuppressLint
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import com.google.mlkit.vision.barcode.BarcodeScanning
import com.google.mlkit.vision.barcode.common.Barcode
import com.google.mlkit.vision.common.InputImage

/**
 * 條碼掃描分析器
 */
class BarcodeScannerAnalyzer(
    private val onBarcodeDetected: (String) -> Unit
) : ImageAnalysis.Analyzer {
    
    private val scanner = BarcodeScanning.getClient()
    private var lastScannedTime = 0L
    private val SCAN_COOLDOWN = 2000L // 2 秒冷卻時間，避免重複掃描
    
    @SuppressLint("UnsafeOptInUsageError")
    override fun analyze(imageProxy: ImageProxy) {
        val mediaImage = imageProxy.image
        if (mediaImage != null) {
            val image = InputImage.fromMediaImage(
                mediaImage,
                imageProxy.imageInfo.rotationDegrees
            )
            
            scanner.process(image)
                .addOnSuccessListener { barcodes ->
                    for (barcode in barcodes) {
                        when (barcode.valueType) {
                            Barcode.TYPE_PRODUCT -> {
                                // 產品條碼 (UPC, EAN)
                                val rawValue = barcode.rawValue
                                if (rawValue != null && System.currentTimeMillis() - lastScannedTime > SCAN_COOLDOWN) {
                                    lastScannedTime = System.currentTimeMillis()
                                    onBarcodeDetected(rawValue)
                                }
                            }
                            Barcode.TYPE_ISBN -> {
                                // ISBN 條碼
                                val rawValue = barcode.rawValue
                                if (rawValue != null && System.currentTimeMillis() - lastScannedTime > SCAN_COOLDOWN) {
                                    lastScannedTime = System.currentTimeMillis()
                                    onBarcodeDetected(rawValue)
                                }
                            }
                            else -> {
                                // 其他類型的條碼也嘗試處理
                                val rawValue = barcode.rawValue
                                if (rawValue != null && System.currentTimeMillis() - lastScannedTime > SCAN_COOLDOWN) {
                                    lastScannedTime = System.currentTimeMillis()
                                    onBarcodeDetected(rawValue)
                                }
                            }
                        }
                    }
                }
                .addOnFailureListener {
                    // 處理錯誤
                }
                .addOnCompleteListener {
                    imageProxy.close()
                }
        } else {
            imageProxy.close()
        }
    }
}
