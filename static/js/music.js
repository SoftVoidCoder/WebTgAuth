let currentTrackId = null;
let isPlaying = false;
let tracksList = [];
let audioElement = null;

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    audioElement = document.getElementById('audioElement');
    setupAudioEvents();
});

// Настройка событий аудио
function setupAudioEvents() {
    audioElement.onended = async function() {
        console.log('Трек закончился, загружаем следующий');
        await playNextTrack();
    };
    
    audioElement.onpause = () => {
        isPlaying = false;
        updatePlayButton();
    };
    
    audioElement.onplay = () => {
        isPlaying = true;
        updatePlayButton();
    };
}

// Запуск радио
async function startRadio() {
    const listenBtn = document.querySelector('.listen-btn');
    const audioPlayer = document.getElementById('audioPlayer');
    
    listenBtn.innerHTML = '🔄 Загружаем треки...';
    listenBtn.disabled = true;
    
    try {
        // Загружаем первые треки
        await loadNewTracks();
        
        // Скрываем кнопку и показываем плеер
        listenBtn.style.display = 'none';
        audioPlayer.style.display = 'block';
        
        // Автоматически играем первый трек
        if (tracksList.length > 0) {
            await playTrackById(tracksList[0].id, tracksList[0].title, tracksList[0].artists.join(', '), tracksList[0].cover_uri);
        }
        
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка при загрузке музыки');
        listenBtn.innerHTML = '🎵 Слушать музыку';
        listenBtn.disabled = false;
    }
}

// Загрузка новых треков
async function loadNewTracks() {
    const response = await fetch('/api/popular');
    const data = await response.json();
    
    if (data.tracks && data.tracks.length > 0) {
        tracksList = data.tracks;
        console.log('Загружено треков:', tracksList.length);
        return true;
    } else {
        throw new Error('Не удалось загрузить треки');
    }
}

// Воспроизведение следующего трека
async function playNextTrack() {
    if (tracksList.length === 0) {
        await loadNewTracks();
    }
    
    if (tracksList.length > 0) {
        // Берем случайный трек из списка
        const randomIndex = Math.floor(Math.random() * tracksList.length);
        const track = tracksList[randomIndex];
        
        await playTrackById(track.id, track.title, track.artists.join(', '), track.cover_uri);
    }
}

// Воспроизведение предыдущего трека
async function playPrevTrack() {
    // Для предыдущего трека тоже загружаем новые
    await playNextTrack();
}

// Воспроизведение трека по ID
async function playTrackById(trackId, title, artist, coverUri) {
    const nowPlayingTitle = document.getElementById('nowPlayingTitle');
    const nowPlayingArtist = document.getElementById('nowPlayingArtist');
    const trackCover = document.getElementById('trackCover');
    
    currentTrackId = trackId;
    
    // Обновляем информацию о треке
    nowPlayingTitle.textContent = title;
    nowPlayingArtist.textContent = artist;
    
    // Обновляем обложку
    if (coverUri) {
        trackCover.innerHTML = `<img src="${coverUri}" alt="${title}" class="cover-image">`;
    } else {
        trackCover.innerHTML = '<div class="cover-placeholder">🎵</div>';
    }
    
    try {
        const response = await fetch(`/music/track/${trackId}`);
        const data = await response.json();
        
        if (data.download_url) {
            audioElement.src = data.download_url;
            await audioElement.play();
            isPlaying = true;
        } else {
            throw new Error(data.error || 'Не удалось загрузить трек');
        }
        
    } catch (error) {
        console.error('Ошибка:', error);
        // При ошибке сразу пробуем следующий трек
        setTimeout(() => playNextTrack(), 1000);
    }
}

// Обновление кнопки воспроизведения
function updatePlayButton() {
    // Можно добавить логику если понадобится
}

// Горячие клавиши
document.addEventListener('keydown', function(e) {
    if (e.code === 'Space' && audioElement) {
        e.preventDefault();
        if (isPlaying) {
            audioElement.pause();
        } else {
            audioElement.play();
        }
    } else if (e.code === 'ArrowRight') {
        playNextTrack();
    }
});