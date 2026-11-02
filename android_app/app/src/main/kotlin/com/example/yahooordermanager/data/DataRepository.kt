package com.example.yahooordermanager.data

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.net.HttpURLConnection
import java.net.URL

interface DataRepository {
    fun getOrdersFlow(): Flow<List<OrderDto>>
    suspend fun fetchOrders(baseUrl: String = ServerConfig.currentUrl, dayFilter: String? = null): List<OrderDto>
    suspend fun fetchMetrics(baseUrl: String = ServerConfig.currentUrl): DashboardMetricsDto
    suspend fun fetchDailySummary(baseUrl: String = ServerConfig.currentUrl): List<DailySummaryDto>
    suspend fun triggerSync(baseUrl: String = ServerConfig.currentUrl): Boolean
}

class DefaultDataRepository : DataRepository {

    override fun getOrdersFlow(): Flow<List<OrderDto>> = flow {
        emit(fetchOrders())
    }

    override suspend fun fetchOrders(baseUrl: String, dayFilter: String?): List<OrderDto> = withContext(Dispatchers.IO) {
        val targetUrl = if (baseUrl.isBlank() || baseUrl == "http://10.0.2.2:8000") ServerConfig.currentUrl else baseUrl
        val orders = mutableListOf<OrderDto>()
        val queryStr = if (dayFilter != null && dayFilter != "all") "?day_filter=$dayFilter" else ""
        val url = URL("$targetUrl/api/v1/orders$queryStr")
        val conn = url.openConnection() as HttpURLConnection
        conn.requestMethod = "GET"
        conn.connectTimeout = 4000
        conn.readTimeout = 4000

        if (conn.responseCode == 200) {
            val reader = BufferedReader(InputStreamReader(conn.inputStream))
            val response = reader.readText()
            reader.close()

            val jsonArray = JSONArray(response)
            for (i in 0 until jsonArray.length()) {
                val obj = jsonArray.getJSONObject(i)
                orders.add(
                    OrderDto(
                        id = obj.optInt("id"),
                        po_number = obj.optString("po_number", "N/A"),
                        booking_number = obj.optString("booking_number", "N/A"),
                        buyer_name = obj.optString("buyer_name", "Unknown"),
                        order_type = obj.optString("order_type", "Purchase Order"),
                        category = obj.optString("category", "Other"),
                        total_quantity = obj.optDouble("total_quantity", 0.0),
                        quantity_unit = obj.optString("quantity_unit", "PCS"),
                        currency = obj.optString("currency", "USD"),
                        total_amount = obj.optDouble("total_amount", 0.0),
                        confidence_score = obj.optDouble("confidence_score", 0.0),
                        status = obj.optString("status", "CONFIRMED"),
                        created_at = obj.optString("created_at", "")
                    )
                )
            }
        } else {
            throw Exception("Server returned HTTP ${conn.responseCode} for $targetUrl")
        }
        orders
    }

    override suspend fun fetchMetrics(baseUrl: String): DashboardMetricsDto = withContext(Dispatchers.IO) {
        val targetUrl = if (baseUrl.isBlank() || baseUrl == "http://10.0.2.2:8000") ServerConfig.currentUrl else baseUrl
        val url = URL("$targetUrl/api/v1/orders/metrics")
        val conn = url.openConnection() as HttpURLConnection
        conn.requestMethod = "GET"
        conn.connectTimeout = 4000
        conn.readTimeout = 4000

        if (conn.responseCode == 200) {
            val reader = BufferedReader(InputStreamReader(conn.inputStream))
            val response = reader.readText()
            reader.close()

            val obj = JSONObject(response)
            DashboardMetricsDto(
                total_orders = obj.optInt("total_orders", 0),
                confirmed_orders = obj.optInt("confirmed_orders", 0),
                review_needed = obj.optInt("review_needed", 0),
                duplicate_orders = obj.optInt("duplicate_orders", 0),
                total_buyers = obj.optInt("total_buyers", 0),
                total_quantity = obj.optDouble("total_quantity", 0.0),
                today_orders = obj.optInt("today_orders", 0),
                today_quantity = obj.optDouble("today_quantity", 0.0),
                past_7_days_orders = obj.optInt("past_7_days_orders", 0)
            )
        } else {
            DashboardMetricsDto()
        }
    }

    override suspend fun fetchDailySummary(baseUrl: String): List<DailySummaryDto> = withContext(Dispatchers.IO) {
        val targetUrl = if (baseUrl.isBlank() || baseUrl == "http://10.0.2.2:8000") ServerConfig.currentUrl else baseUrl
        val days = mutableListOf<DailySummaryDto>()
        try {
            val url = URL("$targetUrl/api/v1/orders/daily-summary")
            val conn = url.openConnection() as HttpURLConnection
            conn.requestMethod = "GET"
            conn.connectTimeout = 4000
            conn.readTimeout = 4000

            if (conn.responseCode == 200) {
                val reader = BufferedReader(InputStreamReader(conn.inputStream))
                val response = reader.readText()
                reader.close()

                val jsonArray = JSONArray(response)
                for (i in 0 until jsonArray.length()) {
                    val obj = jsonArray.getJSONObject(i)
                    days.add(
                        DailySummaryDto(
                            date = obj.optString("date"),
                            day_name = obj.optString("day_name"),
                            label_en = obj.optString("label_en"),
                            label_bn = obj.optString("label_bn"),
                            order_count = obj.optInt("order_count"),
                            total_quantity = obj.optDouble("total_quantity"),
                            total_amount = obj.optDouble("total_amount"),
                            is_today = obj.optBoolean("is_today")
                        )
                    )
                }
            }
        } catch (e: Exception) {
            // Keep empty on error
        }
        days
    }

    override suspend fun triggerSync(baseUrl: String): Boolean = withContext(Dispatchers.IO) {
        val targetUrl = if (baseUrl.isBlank() || baseUrl == "http://10.0.2.2:8000") ServerConfig.currentUrl else baseUrl
        try {
            val url = URL("$targetUrl/api/v1/sync/trigger")
            val conn = url.openConnection() as HttpURLConnection
            conn.requestMethod = "POST"
            conn.setRequestProperty("Content-Type", "application/json")
            conn.doOutput = true
            val os = conn.outputStream
            os.write("""{"max_emails": 20}""".toByteArray())
            os.flush()
            os.close()
            conn.responseCode in 200..299
        } catch (e: Exception) {
            false
        }
    }
}
