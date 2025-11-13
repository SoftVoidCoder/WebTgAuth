// Управление воспроизведением музыки
let currentTrack = null;
let audioPlayer = document.getElementById('audioPlayer');
let audioElement = document.getElementById('audioElement');
let nowPlaying = document.getElementById('nowPlaying');

async function playTrack(button) {
    const trackCard = button.closest('.track-card');
    const trackId = trackCard.dataset.trackId;
    const trackTitle = trackCard.querySelector('.track-title').textContent;
    const trackArtist = trackCard.querySelector('.track-artist').textContent;
    
    // Показываем плеер
    audioPlayer.style.display = 'block';
    
    // Обновляем информацию о текущем треке
    nowPlaying.textContent = `Сейчас играет: ${trackArtist} - ${trackTitle}`;
    
    try {
        // Получаем ссылку на трек через API Яндекс.Музыки
        const response = await fetch(`/music/track/${trackId}`);
        const data = await response.json();
        
        if (data.download_url) {
            audioElement.src = data.download_url;
            audioElement.play().catch(e => {
                console.error('Ошибка воспроизведения:', e);
                alert('Не удалось воспроизвести трек. Возможно, требуется авторизация.');
            });
        } else {
            alert('Не удалось загрузить трек');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка при загрузке трека');
    }
}

// Закрытие плеера
function closePlayer() {
    audioPlayer.style.display = 'none';
    audioElement.pause();
    audioElement.src = '';
}

// Поиск в реальном времени (опционально)
const searchInput = document.querySelector('.search-input');
if (searchInput) {
    let searchTimeout;
    
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            if (this.value.length > 2) {
                // Можно добавить AJAX поиск здесь
            }
        }, 500);
    });
}

// Форматирование времени
function formatDuration(ms) {
    const minutes = Math.floor(ms / 60000);
    const seconds = ((ms % 60000) / 1000).toFixed(0);
    return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
}