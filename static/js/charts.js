// Реальные графики с Chart.js
function createRealChart(canvasId, prices, labels, color) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Определяем цвет графика на основе тренда
    const isPositive = prices[prices.length - 1] >= prices[0];
    const chartColor = isPositive ? '#00ff00' : '#ff4444';
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Price',
                data: prices,
                borderColor: chartColor,
                backgroundColor: isPositive ? 'rgba(0, 255, 0, 0.1)' : 'rgba(255, 0, 0, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff'
                }
            },
            scales: {
                x: {
                    display: false
                },
                y: {
                    display: false
                }
            },
            interaction: {
                intersect: false,
                mode: 'nearest'
            }
        }
    });
}

// Загрузка данных графика
async function loadChartData(cryptoId, symbol) {
    try {
        const response = await fetch(`/crypto/chart/${cryptoId}?days=30`);
        const data = await response.json();
        
        if (data.prices) {
            // Берем последние 20 точек для красивого графика
            const recentPrices = data.prices.slice(-20);
            const prices = recentPrices.map(item => item[1]);
            const labels = recentPrices.map((item, index) => index);
            
            createRealChart(`chart-${symbol.toLowerCase()}`, prices, labels);
        }
    } catch (error) {
        console.error(`Error loading chart for ${symbol}:`, error);
    }
}