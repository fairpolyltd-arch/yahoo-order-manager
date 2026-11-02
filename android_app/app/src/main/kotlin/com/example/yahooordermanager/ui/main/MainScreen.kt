package com.example.yahooordermanager.ui.main

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation3.runtime.NavKey
import com.example.yahooordermanager.data.DailySummaryDto
import com.example.yahooordermanager.data.DashboardMetricsDto
import com.example.yahooordermanager.data.DefaultDataRepository
import com.example.yahooordermanager.data.OrderDto
import com.example.yahooordermanager.data.ServerConfig
import kotlinx.coroutines.launch

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
    var showServerDialog by remember { mutableStateOf(false) }

    if (showServerDialog) {
        ServerSettingsDialog(
            onDismiss = { showServerDialog = false },
            onSaved = {
                showServerDialog = false
                viewModel.loadData()
            }
        )
    }

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
                dailySummary = state.dailySummary,
                selectedDayFilter = state.selectedDayFilter,
                onSelectDay = { filter -> viewModel.selectDayFilter(filter) },
                onSyncClick = { viewModel.triggerSync() },
                onOpenSettings = { showServerDialog = true },
                modifier = modifier
            )
        }
        is MainScreenUiState.Error -> {
            Box(
                modifier = modifier
                    .fillMaxSize()
                    .padding(24.dp),
                contentAlignment = Alignment.Center
            ) {
                Card(
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(containerColor = Color.White),
                    elevation = CardDefaults.cardElevation(defaultElevation = 3.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(
                        modifier = Modifier.padding(20.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text(
                            "⚠️",
                            fontSize = 32.sp
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            "Cannot Reach Server",
                            fontSize = 18.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFF1E293B)
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            "Server URL: ${ServerConfig.currentUrl}",
                            fontSize = 12.sp,
                            color = YahooPurple,
                            fontWeight = FontWeight.SemiBold
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            "Please make sure your phone and PC are connected to the same WiFi network, or update the PC IP address in settings.",
                            fontSize = 12.sp,
                            color = Color(0xFF64748B),
                            lineHeight = 16.sp
                        )
                        Spacer(modifier = Modifier.height(20.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                            OutlinedButton(
                                onClick = { showServerDialog = true },
                                shape = RoundedCornerShape(8.dp)
                            ) {
                                Text("⚙️ Server Settings", fontSize = 12.sp)
                            }
                            Button(
                                onClick = { viewModel.loadData() },
                                colors = ButtonDefaults.buttonColors(containerColor = YahooPurple),
                                shape = RoundedCornerShape(8.dp)
                            ) {
                                Text("Retry", fontSize = 12.sp)
                            }
                        }
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
    dailySummary: List<DailySummaryDto>,
    selectedDayFilter: String,
    onSelectDay: (String) -> Unit,
    onSyncClick: () -> Unit,
    onOpenSettings: () -> Unit,
    modifier: Modifier = Modifier
) {
    var searchQuery by remember { mutableStateOf("") }

    val filteredOrders = remember(orders, searchQuery) {
        if (searchQuery.isBlank()) orders
        else orders.filter {
            (it.po_number?.contains(searchQuery, ignoreCase = true) == true) ||
            (it.booking_number?.contains(searchQuery, ignoreCase = true) == true) ||
            (it.buyer_name?.contains(searchQuery, ignoreCase = true) == true) ||
            (it.category?.contains(searchQuery, ignoreCase = true) == true)
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
                            fontSize = 17.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color.White
                        )
                        Text(
                            "Server: ${ServerConfig.currentUrl.removePrefix("http://")}",
                            fontSize = 10.sp,
                            color = Color.White.copy(alpha = 0.85f)
                        )
                    }
                },
                actions = {
                    Button(
                        onClick = onSyncClick,
                        colors = ButtonDefaults.buttonColors(containerColor = Color.White.copy(alpha = 0.2f)),
                        shape = RoundedCornerShape(8.dp),
                        contentPadding = PaddingValues(horizontal = 10.dp, vertical = 4.dp)
                    ) {
                        Text("Sync", color = Color.White, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                    }
                    Spacer(modifier = Modifier.width(4.dp))
                    IconButton(onClick = onOpenSettings) {
                        Text("⚙️", fontSize = 16.sp)
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
                .padding(14.dp)
        ) {
            // Metrics Summary Row
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                // Today's Orders Highlight Card
                Card(
                    modifier = Modifier
                        .weight(1.1f)
                        .clickable { onSelectDay("today") },
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(containerColor = if (selectedDayFilter == "today") YahooPurple else Color(0xFF4C1D95)),
                    elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
                ) {
                    Column(modifier = Modifier.padding(10.dp)) {
                        Text("Today's Orders", fontSize = 10.sp, color = Color.White.copy(alpha = 0.8f), fontWeight = FontWeight.SemiBold)
                        Spacer(modifier = Modifier.height(2.dp))
                        Row(verticalAlignment = Alignment.Bottom) {
                            Text(metrics.today_orders.toString(), fontSize = 20.sp, fontWeight = FontWeight.ExtraBold, color = Color.White)
                            Spacer(modifier = Modifier.width(4.dp))
                            Text("${metrics.today_quantity.toInt()} pcs", fontSize = 10.sp, color = Color.White.copy(alpha = 0.7f))
                        }
                    }
                }

                MetricCard(
                    title = "7-Day Total",
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
            }

            Spacer(modifier = Modifier.height(10.dp))

            // Past 7 Days Horizontal Filter Chips
            Text(
                "Daily Orders (Past 7 Days)",
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold,
                color = Color(0xFF334155)
            )

            Spacer(modifier = Modifier.height(6.dp))

            LazyRow(
                horizontalArrangement = Arrangement.spacedBy(6.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                item {
                    val isAll = selectedDayFilter == "all"
                    DayChip(
                        label = "All Days",
                        count = metrics.total_orders,
                        isSelected = isAll,
                        onClick = { onSelectDay("all") }
                    )
                }

                items(dailySummary) { day ->
                    val isSelected = (selectedDayFilter == day.date) || (selectedDayFilter == "today" && day.is_today)
                    DayChip(
                        label = if (day.is_today) "Today" else day.label_en.split(" ")[0],
                        count = day.order_count,
                        isSelected = isSelected,
                        onClick = { onSelectDay(day.date) }
                    )
                }
            }

            Spacer(modifier = Modifier.height(10.dp))

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

            Spacer(modifier = Modifier.height(10.dp))

            // Orders List
            Text(
                "Orders List (${filteredOrders.size})",
                fontSize = 13.sp,
                fontWeight = FontWeight.Bold,
                color = Color(0xFF1E293B)
            )

            Spacer(modifier = Modifier.height(6.dp))

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
fun DayChip(
    label: String,
    count: Int,
    isSelected: Boolean,
    onClick: () -> Unit
) {
    Surface(
        modifier = Modifier.clickable { onClick() },
        shape = RoundedCornerShape(8.dp),
        color = if (isSelected) YahooPurple else Color.White,
        border = if (isSelected) null else androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFE2E8F0)),
        shadowElevation = if (isSelected) 2.dp else 0.dp
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                label,
                fontSize = 11.sp,
                fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Medium,
                color = if (isSelected) Color.White else Color(0xFF334155)
            )
            Spacer(modifier = Modifier.width(4.dp))
            Box(
                modifier = Modifier
                    .background(
                        if (isSelected) Color.White.copy(alpha = 0.25f) else Color(0xFFF1F5F9),
                        RoundedCornerShape(10.dp)
                    )
                    .padding(horizontal = 5.dp, vertical = 1.dp)
            ) {
                Text(
                    count.toString(),
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold,
                    color = if (isSelected) Color.White else Color(0xFF475569)
                )
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
        elevation = CardDefaults.cardElevation(defaultElevation = 1.5.dp)
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    order.po_number ?: "NO PO",
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold,
                    color = YahooPurple
                )
                StatusPill(status = order.status)
            }

            Spacer(modifier = Modifier.height(4.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    "Booking: ${order.booking_number ?: "N/A"}",
                    fontSize = 11.sp,
                    color = Color(0xFF334155),
                    fontWeight = FontWeight.Medium
                )
                Text(
                    "Buyer: ${order.buyer_name ?: "Unknown"}",
                    fontSize = 11.sp,
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
                    "${order.category ?: "Other"} • ${order.order_type ?: "Order"}",
                    fontSize = 10.sp,
                    color = Color(0xFF6B21A8),
                    fontWeight = FontWeight.Medium
                )
                Text(
                    "Qty: ${order.total_quantity.toInt()} ${order.quantity_unit} • ${order.currency} ${order.total_amount}",
                    fontSize = 11.sp,
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
        Text(status, fontSize = 9.sp, fontWeight = FontWeight.Bold, color = textColor)
    }
}

@Composable
fun ServerSettingsDialog(
    onDismiss: () -> Unit,
    onSaved: () -> Unit
) {
    val context = LocalContext.current
    var urlText by remember { mutableStateOf(ServerConfig.currentUrl) }
    var testResult by remember { mutableStateOf<String?>(null) }
    var isTesting by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Text(
                "Server Connection Settings",
                fontSize = 16.sp,
                fontWeight = FontWeight.Bold,
                color = Color(0xFF1E293B)
            )
        },
        text = {
            Column(modifier = Modifier.fillMaxWidth()) {
                Text(
                    "Enter your PC Backend Server URL (e.g. your PC's WiFi IP address or public tunnel URL):",
                    fontSize = 12.sp,
                    color = Color(0xFF64748B),
                    lineHeight = 16.sp
                )
                Spacer(modifier = Modifier.height(10.dp))
                OutlinedTextField(
                    value = urlText,
                    onValueChange = {
                        urlText = it
                        testResult = null
                    },
                    label = { Text("Server Base URL", fontSize = 11.sp) },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(8.dp)
                )

                Spacer(modifier = Modifier.height(10.dp))
                Text("Quick Presets:", fontSize = 11.sp, fontWeight = FontWeight.SemiBold, color = Color(0xFF475569))
                Spacer(modifier = Modifier.height(4.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    OutlinedButton(
                        onClick = {
                            urlText = "http://192.168.0.108:8000"
                            testResult = null
                        },
                        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 2.dp),
                        shape = RoundedCornerShape(6.dp)
                    ) {
                        Text("PC WiFi (192.168.0.108)", fontSize = 10.sp)
                    }
                    OutlinedButton(
                        onClick = {
                            urlText = "http://10.0.2.2:8000"
                            testResult = null
                        },
                        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 2.dp),
                        shape = RoundedCornerShape(6.dp)
                    ) {
                        Text("Emulator", fontSize = 10.sp)
                    }
                }

                Spacer(modifier = Modifier.height(12.dp))
                Button(
                    onClick = {
                        isTesting = true
                        testResult = null
                        scope.launch {
                            val res = ServerConfig.testConnection(urlText)
                            isTesting = false
                            testResult = if (res.isSuccess) {
                                "✅ " + res.getOrNull()
                            } else {
                                "❌ Failed: " + (res.exceptionOrNull()?.message ?: "Unreachable")
                            }
                        }
                    },
                    modifier = Modifier.fillMaxWidth(),
                    enabled = !isTesting,
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF4C1D95)),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    if (isTesting) {
                        CircularProgressIndicator(color = Color.White, modifier = Modifier.size(16.dp), strokeWidth = 2.dp)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Testing Connection...", fontSize = 12.sp)
                    } else {
                        Text("Test Connection", fontSize = 12.sp)
                    }
                }

                if (testResult != null) {
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        testResult ?: "",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Medium,
                        color = if (testResult?.startsWith("✅") == true) Color(0xFF166534) else Color(0xFF991B1B)
                    )
                }
            }
        },
        confirmButton = {
            Button(
                onClick = {
                    ServerConfig.saveUrl(context, urlText)
                    onSaved()
                },
                colors = ButtonDefaults.buttonColors(containerColor = YahooPurple),
                shape = RoundedCornerShape(8.dp)
            ) {
                Text("Save & Connect", fontSize = 12.sp, fontWeight = FontWeight.Bold)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel", fontSize = 12.sp)
            }
        }
    )
}
