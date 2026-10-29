package com.example.yahooordermanager.ui.main

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.yahooordermanager.data.DailySummaryDto
import com.example.yahooordermanager.data.DashboardMetricsDto
import com.example.yahooordermanager.data.DataRepository
import com.example.yahooordermanager.data.OrderDto
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class MainScreenViewModel(private val dataRepository: DataRepository) : ViewModel() {

    private val _uiState = MutableStateFlow<MainScreenUiState>(MainScreenUiState.Loading)
    val uiState: StateFlow<MainScreenUiState> = _uiState.asStateFlow()

    private var currentFilter: String = "all"

    init {
        loadData()
    }

    fun loadData(dayFilter: String = currentFilter) {
        currentFilter = dayFilter
        viewModelScope.launch {
            _uiState.value = MainScreenUiState.Loading
            try {
                val orders = dataRepository.fetchOrders(dayFilter = dayFilter)
                val metrics = dataRepository.fetchMetrics()
                val dailySummary = dataRepository.fetchDailySummary()
                _uiState.value = MainScreenUiState.Success(
                    orders = orders,
                    metrics = metrics,
                    dailySummary = dailySummary,
                    selectedDayFilter = dayFilter
                )
            } catch (e: Throwable) {
                _uiState.value = MainScreenUiState.Error(e)
            }
        }
    }

    fun selectDayFilter(dayFilter: String) {
        loadData(dayFilter)
    }

    fun triggerSync() {
        viewModelScope.launch {
            dataRepository.triggerSync()
            loadData()
        }
    }
}

sealed interface MainScreenUiState {
    object Loading : MainScreenUiState
    data class Error(val throwable: Throwable) : MainScreenUiState
    data class Success(
        val orders: List<OrderDto>,
        val metrics: DashboardMetricsDto,
        val dailySummary: List<DailySummaryDto>,
        val selectedDayFilter: String
    ) : MainScreenUiState
}
