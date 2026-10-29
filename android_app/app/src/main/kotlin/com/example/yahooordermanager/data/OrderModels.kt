package com.example.yahooordermanager.data

import kotlinx.serialization.Serializable

@Serializable
data class OrderDto(
    val id: Int,
    val po_number: String? = null,
    val booking_number: String? = null,
    val buyer_name: String? = null,
    val order_type: String? = null,
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
    val total_quantity: Double = 0.0
)
