package com.example.yahooordermanager.data

import kotlinx.serialization.Serializable

@Serializable
data class OrderDto(
    val id: Int,
    val po_number: String? = null,
    val booking_number: String? = null,
    val buyer_name: String? = null,
    val order_type: String? = null,
    val category: String? = "Other",
    val total_quantity: Double = 0.0,
    val quantity_unit: String = "PCS",
    val currency: String = "USD",
    val total_amount: Double = 0.0,
    val confidence_score: Double = 0.0,
    val status: String = "CONFIRMED",
    val notes: String? = null,
    val created_at: String = ""
)

@Serializable
data class DashboardMetricsDto(
    val total_orders: Int = 0,
    val confirmed_orders: Int = 0,
    val review_needed: Int = 0,
    val duplicate_orders: Int = 0,
    val total_buyers: Int = 0,
    val total_quantity: Double = 0.0,
    val today_orders: Int = 0,
    val today_quantity: Double = 0.0,
    val past_7_days_orders: Int = 0
)

@Serializable
data class DailySummaryDto(
    val date: String = "",
    val day_name: String = "",
    val label_en: String = "",
    val label_bn: String = "",
    val order_count: Int = 0,
    val total_quantity: Double = 0.0,
    val total_amount: Double = 0.0,
    val is_today: Boolean = false
)
