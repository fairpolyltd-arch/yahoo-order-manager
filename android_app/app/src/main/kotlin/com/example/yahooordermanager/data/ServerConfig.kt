package com.example.yahooordermanager.data

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.net.HttpURLConnection
import java.net.URL

object ServerConfig {
    private const val PREFS_NAME = "yahoo_order_prefs"
    private const val KEY_SERVER_URL = "server_url"

    // Default to the host PC LAN IP on the local WiFi network
    const val DEFAULT_URL = "http://192.168.0.108:8000"
    const val EMULATOR_URL = "http://10.0.2.2:8000"

    var currentUrl: String = DEFAULT_URL
        private set

    fun init(context: Context) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        currentUrl = prefs.getString(KEY_SERVER_URL, DEFAULT_URL) ?: DEFAULT_URL
    }

    fun saveUrl(context: Context, newUrl: String): String {
        var clean = newUrl.trim()
        if (clean.endsWith("/")) {
            clean = clean.substring(0, clean.length - 1)
        }
        if (!clean.startsWith("http://") && !clean.startsWith("https://")) {
            clean = "http://$clean"
        }
        currentUrl = clean
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit()
            .putString(KEY_SERVER_URL, clean)
            .apply()
        return clean
    }

    suspend fun testConnection(testUrl: String): Result<String> = withContext(Dispatchers.IO) {
        try {
            var clean = testUrl.trim()
            if (clean.endsWith("/")) clean = clean.substring(0, clean.length - 1)
            if (!clean.startsWith("http://") && !clean.startsWith("https://")) clean = "http://$clean"

            val url = URL("$clean/api/v1/orders/metrics")
            val conn = url.openConnection() as HttpURLConnection
            conn.connectTimeout = 4000
            conn.readTimeout = 4000
            conn.requestMethod = "GET"
            val code = conn.responseCode
            if (code == 200) {
                val reader = BufferedReader(InputStreamReader(conn.inputStream))
                val response = reader.readText()
                reader.close()
                val obj = JSONObject(response)
                val total = obj.optInt("total_orders", 0)
                Result.success("Connected successfully! ($total live orders found)")
            } else {
                Result.failure(Exception("HTTP Error $code from server"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
