package com.example.yahooordermanager.ui.main

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation3.runtime.NavKey
import com.example.yahooordermanager.data.DashboardMetricsDto
import com.example.yahooordermanager.data.DefaultDataRepository
import com.example.yahooordermanager.data.OrderDto

val YahooPurple = Color(0xFF6001D2)
val StatusGreen = Color(0xFF10B981)
val StatusAmber = Color(0xFFF59E0B)

@Composable
fun MainScreen(
    onItemClick: (NavKey) -> Unit,
    modifier: Modifier = Modifier,
    viewModel: MainScreenViewModel = viewModel { MainScreenViewModel(DefaultDataRepository()) },
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    when (val state = uiState) {
        MainScreenUiState.Loading -> {
            Box(
                modifier = modifier.fillMaxSize(),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator(color = YahooPurple)
            }
        }
        is MainScreenUiState.Success -> {
            OrdersDashboard(
                orders = state.orders,
                metrics = state.metrics,
                onSyncClick = { viewModel.triggerSync() },
                modifier = modifier
            )
        }
        is MainScreenUiState.Error -> {
            Box(
                modifier = modifier.fillMaxSize(),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("Error: ${state.throwable.message}", color = MaterialTheme.colorScheme.error)
                    Spacer(modifier = Modifier.height(16.dp))
                    Button(onClick = { viewModel.loadData() }) {
                        Text("Retry")
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
internal fun OrdersDashboard(
    orders: List<OrderDto>,
    metrics: DashboardMetricsDto,
    onSyncClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    var searchQuery by remember { mutableStateOf("") }

    val filteredOrders = remember(orders, searchQuery) {
        if (searchQuery.isBlank()) orders
        else orders.filter {
            (it.po_number?.contains(searchQuery, ignoreCase = true) == true) ||
            (it.booking_number?.contains(searchQuery, ignoreCase = true) == true) ||
            (it.buyer_name?.contains(searchQuery, ignoreCase = true) == true)
        }
    }

    Scaffold(
        modifier = modifier,
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            "Yahoo Mail Orders",
                            fontSize = 18.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color.White
                        )
                        Text(
                            "Intelligent Order Extraction",
                            fontSize = 11.sp,
                            color = Color.White.copy(alpha = 0.8f)
                        )
                    }
                },
                actions = {
                    Button(
                        onClick = onSyncClick,
                        colors = ButtonDefaults.buttonColors(containerColor = Color.White.copy(alpha = 0.2f)),
                        shape = RoundedCornerShape(8.dp),
                        contentPadding = PaddingValues(horizontal = 12.dp, vertical = 6.dp)
                    ) {
                        Text("Sync Now", color = Color.White, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = YahooPurple
                )
            )
        }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .background(Color(0xFFF8FAFC))
                .padding(16.dp)
        ) {
            // Metrics Summary Row
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                MetricCard(
                    title = "Total Orders",
                    value = metrics.total_orders.toString(),
                    color = YahooPurple,
                    modifier = Modifier.weight(1f)
                )
                MetricCard(
                    title = "Confirmed",
                    value = metrics.confirmed_orders.toString(),
                    color = StatusGreen,
                    modifier = Modifier.weight(1f)
                )
                MetricCard(
                    title = "Total Qty",
                    value = metrics.total_quantity.toInt().toString(),
                    color = Color(0xFF2563EB),
                    modifier = Modifier.weight(1f)
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Search Bar
            OutlinedTextField(
                value = searchQuery,
                onValueChange = { searchQuery = it },
                label = { Text("Search PO, Booking, Buyer...") },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = YahooPurple,
                    focusedLabelColor = YahooPurple
                ),
                singleLine = true
            )

            Spacer(modifier = Modifier.height(12.dp))

            // Orders List
            Text(
                "Extracted Orders (${filteredOrders.size})",
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold,
                color = Color(0xFF1E293B)
            )

            Spacer(modifier = Modifier.height(8.dp))

            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                items(filteredOrders) { order ->
                    OrderCard(order = order)
                }
            }
        }
    }
}

@Composable
fun MetricCard(title: String, value: String, color: Color, modifier: Modifier = Modifier) {
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp)
    ) {
        Column(modifier = Modifier.padding(10.dp)) {
            Text(title, fontSize = 10.sp, color = Color.Gray, fontWeight = FontWeight.Medium)
            Text(value, fontSize = 18.sp, fontWeight = FontWeight.Bold, color = color)
        }
    }
}

@Composable
fun OrderCard(order: OrderDto) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    order.po_number ?: "NO PO",
                    fontSize = 15.sp,
                    fontWeight = FontWeight.Bold,
                    color = YahooPurple
                )
                StatusPill(status = order.status)
            }

            Spacer(modifier = Modifier.height(6.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    "Booking: ${order.booking_number ?: "N/A"}",
                    fontSize = 12.sp,
                    color = Color(0xFF334155),
                    fontWeight = FontWeight.Medium
                )
                Text(
                    "Buyer: ${order.buyer_name ?: "Unknown"}",
                    fontSize = 12.sp,
                    color = Color(0xFF475569),
                    fontWeight = FontWeight.Bold
                )
            }

            Spacer(modifier = Modifier.height(4.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    order.order_type ?: "Order",
                    fontSize = 11.sp,
                    color = Color.Gray
                )
                Text(
                    "Qty: ${order.total_quantity.toInt()} ${order.quantity_unit} • ${order.currency} ${order.total_amount}",
                    fontSize = 12.sp,
                    fontWeight = FontWeight.SemiBold,
                    color = Color(0xFF0F172A)
                )
            }
        }
    }
}

@Composable
fun StatusPill(status: String) {
    val (bgColor, textColor) = when (status) {
        "CONFIRMED" -> Color(0xFFD1FAE5) to Color(0xFF065F46)
        "REVIEW_NEEDED" -> Color(0xFFFEF3C7) to Color(0xFF92400E)
        "DUPLICATE" -> Color(0xFFF1F5F9) to Color(0xFF475569)
        else -> Color(0xFFFFE4E6) to Color(0xFF9F1239)
    }

    Box(
        modifier = Modifier
            .background(bgColor, RoundedCornerShape(16.dp))
            .padding(horizontal = 8.dp, vertical = 2.dp)
    ) {
        Text(status, fontSize = 10.sp, fontWeight = FontWeight.Bold, color = textColor)
    }
}
