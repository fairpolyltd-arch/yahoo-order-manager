package com.example.yahooordermanager.ui.main

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
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

    init {
        loadData()
    }

    fun loadData() {
        viewModelScope.launch {
            _uiState.value = MainScreenUiState.Loading
            try {
                val orders = dataRepository.fetchOrders()
                val metrics = dataRepository.fetchMetrics()
                _uiState.value = MainScreenUiState.Success(orders = orders, metrics = metrics)
            } catch (e: Throwable) {
                _uiState.value = MainScreenUiState.Error(e)
            }
        }
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
        val metrics: DashboardMetricsDto
    ) : MainScreenUiState
}
