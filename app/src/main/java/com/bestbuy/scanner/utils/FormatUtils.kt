package com.bestbuy.scanner.utils

import java.text.NumberFormat
import java.util.Locale

/**
 * 格式化工具類
 */
object FormatUtils {
    
    /**
     * 格式化價格
     */
    fun formatPrice(price: Double?): String {
        if (price == null) return "N/A"
        val format = NumberFormat.getCurrencyInstance(Locale.US)
        return format.format(price)
    }
    
    /**
     * 格式化評分
     */
    fun formatRating(rating: Double?, count: Int?): String {
        if (rating == null || count == null) return ""
        return String.format("%.1f ★ (%,d 評價)", rating, count)
    }
    
    /**
     * 移除 HTML 標籤（簡單版本）
     */
    fun stripHtmlTags(html: String?): String {
        if (html.isNullOrEmpty()) return ""
        return html.replace(Regex("<[^>]*>"), "")
            .replace("&nbsp;", " ")
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&quot;", "\"")
            .trim()
    }
    
    /**
     * 截斷文字
     */
    fun truncateText(text: String?, maxLength: Int): String {
        if (text.isNullOrEmpty() || text.length <= maxLength) return text ?: ""
        return text.substring(0, maxLength) + "..."
    }
}
