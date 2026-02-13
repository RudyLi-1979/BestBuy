package com.bestbuy.scanner.data.api

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

/**
 * UCP Server Retrofit Client
 * Provides access to UCP Server API for chat functionality
 */
object UCPRetrofitClient {
    
    // UCP Server URL via Cloudflare Tunnel
    // This allows the app to access the server from anywhere with HTTPS
    private const val BASE_URL = "https://ucp.rudy.xx.kg/"
    
    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }
    
    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor(loggingInterceptor)
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()
    
    private val retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
    
    val apiService: UCPApiService = retrofit.create(UCPApiService::class.java)
}
