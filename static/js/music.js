let currentTrackId = null;
let isPlaying = false;
let currentTrackIndex = 0;
let tracksList = [];
let audioElement = null;
let currentTrackData = null;
let userLikedTracks = [];

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    audioElement = document.getElementById('audioElement');
    setupAudioEvents();
    setupVolumeControl();
    loadUserPreferences();
});

// Настройка событий аудио
function setupAudioEvents() {
    audioElement.onended = async function() {
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

// Настройка громкости
function setupVolumeControl() {
    const volumeSlider = document.getElementById('volumeSlider');
    if (volumeSlider && audioElement) {
        audioElement.volume = volumeSlider.value;
        
        volumeSlider.addEventListener('input', function() {
            audioElement.volume = this.value;
        });
    }
}

// Загрузка предпочтений пользователя
async function loadUserPreferences() {
    try {
        const response = await fetch('/api/liked-tracks');
        const data = await response.json();
        
        if (data.tracks && data.tracks.length > 0) {
            userLikedTracks = data.tracks;
            console.log('Загружено лайкнутых треков:', userLikedTracks.length);
        }
    } catch (error) {
        console.error('Ошибка загрузки предпочтений:', error);
    }
}

// Запуск радио с учетом предпочтений
async function startRadio() {
    const listenBtn = document.querySelector('.listen-btn');
    const audioPlayer = document.getElementById('audioPlayer');
    
    listenBtn.innerHTML = '🔄 Анализируем ваши вкусы...';
    listenBtn.disabled = true;
    
    try {
        // Сначала пробуем загрузить треки на основе лайков
        if (userLikedTracks.length > 0) {
            console.log('Используем лайкнутые треки для рекомендаций');
            await loadTracksBasedOnLikes();
        } else {
            console.log('Лайков нет, загружаем популярные треки');
            await loadNewTracks();
        }
        
        listenBtn.style.display = 'none';
        audioPlayer.style.display = 'block';
        
        if (tracksList.length > 0) {
            await playTrack(tracksList[0]);
        }
        
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка при загрузке музыки');
        listenBtn.innerHTML = '🎵 Слушать музыку';
        listenBtn.disabled = false;
    }
}

// Загрузка треков на основе лайков пользователя
async function loadTracksBasedOnLikes() {
    if (userLikedTracks.length === 0) {
        await loadNewTracks();
        return;
    }
    
    console.log('Ищем похожие треки на основе ваших лайков...');
    
    // Берем случайный лайкнутый трек для поиска похожих
    const randomLikedTrack = userLikedTracks[Math.floor(Math.random() * userLikedTracks.length)];
    
    // Ищем по артистам из лайкнутых треков
    let searchQuery = '';
    if (randomLikedTrack.artists && randomLikedTrack.artists.length > 0) {
        searchQuery = randomLikedTrack.artists[0]; // Берем первого артиста
    } else {
        searchQuery = randomLikedTrack.title; // Или по названию трека
    }
    
    try {
        const response = await fetch(`/api/similar?query=${encodeURIComponent(searchQuery)}`);
        const data = await response.json();
        
        if (data.tracks && data.tracks.length > 0) {
            tracksList = data.tracks;
            console.log('Найдено похожих треков:', tracksList.length);
        } else {
            // Если не нашли похожих - грузим популярные
            await loadNewTracks();
        }
    } catch (error) {
        console.error('Ошибка поиска похожих треков:', error);
        await loadNewTracks();
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

// Воспроизведение трека
async function playTrack(track) {
    currentTrackData = track;
    currentTrackId = track.id;
    
    await playTrackById(track.id, track.title, track.artists.join(', '), track.cover_uri, track);
    checkIfLiked();
}

// Воспроизведение следующего трека
async function playNextTrack() {
    if (tracksList.length === 0) {
        await loadNewTracks();
    }
    
    if (tracksList.length > 0) {
        const randomIndex = Math.floor(Math.random() * tracksList.length);
        await playTrack(tracksList[randomIndex]);
    }
}

// Воспроизведение предыдущего трека
async function playPrevTrack() {
    await playNextTrack(); // Всегда новые треки
}

// Воспроизведение трека по ID
async function playTrackById(trackId, title, artist, coverUri, trackData = null) {
    const audioPlayer = document.getElementById('audioPlayer');
    const nowPlayingTitle = document.getElementById('nowPlayingTitle');
    const nowPlayingArtist = document.getElementById('nowPlayingArtist');
    const trackCover = document.getElementById('trackCover');
    const likeBtn = document.getElementById('likeBtn');
    
    currentTrackId = trackId;
    currentTrackData = trackData || {
        id: trackId,
        title: title,
        artists: [artist],
        cover_uri: coverUri,
        album: "Альбом"
    };
    
    // Обновляем информацию о треке
    nowPlayingTitle.textContent = title;
    nowPlayingArtist.textContent = artist;
    
    // Обновляем обложку
    if (coverUri) {
        trackCover.innerHTML = `<img src="${coverUri}" alt="${title}" class="cover-image">`;
    } else {
        trackCover.innerHTML = '<div class="cover-placeholder">🎵</div>';
    }
    
    // Проверяем лайк
    await checkIfLiked();
    
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
        setTimeout(() => playNextTrack(), 1000);
    }
}

// Переключение воспроизведения/паузы
function togglePlayPause() {
    if (isPlaying) {
        audioElement.pause();
    } else {
        audioElement.play();
    }
}

// Обновление кнопки воспроизведения
function updatePlayButton() {
    const playPauseBtn = document.getElementById('playPauseBtn');
    const playPauseIcon = document.getElementById('playPauseIcon');
    
    if (isPlaying) {
        playPauseIcon.innerHTML = '<path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>';
        playPauseBtn.setAttribute('title', 'Пауза');
    } else {
        playPauseIcon.innerHTML = '<path d="M8 5v14l11-7z"/>';
        playPauseBtn.setAttribute('title', 'Воспроизвести');
    }
}

// Проверка лайка
async function checkIfLiked() {
    if (!currentTrackId) return;
    
    try {
        const response = await fetch(`/api/is-liked/${currentTrackId}`);
        const data = await response.json();
        
        const likeBtn = document.getElementById('likeBtn');
        if (data.liked) {
            likeBtn.innerHTML = '❤️';
            likeBtn.classList.add('liked');
        } else {
            likeBtn.innerHTML = '♡';
            likeBtn.classList.remove('liked');
        }
    } catch (error) {
        console.error('Ошибка проверки лайка:', error);
    }
}

// Переключение лайка
async function toggleLike() {
    if (!currentTrackId || !currentTrackData) return;
    
    const likeBtn = document.getElementById('likeBtn');
    
    try {
        if (likeBtn.classList.contains('liked')) {
            // Удаляем лайк
            const response = await fetch(`/api/unlike/${currentTrackId}`, {
                method: 'DELETE'
            });
            const data = await response.json();
            
            if (data.status === 'unliked') {
                likeBtn.innerHTML = '♡';
                likeBtn.classList.remove('liked');
                // Обновляем список предпочтений
                await loadUserPreferences();
            }
        } else {
            // Добавляем лайк
            const response = await fetch(`/api/like/${currentTrackId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(currentTrackData)
            });
            const data = await response.json();
            
            if (data.status === 'liked') {
                likeBtn.innerHTML = '❤️';
                likeBtn.classList.add('liked');
                // Обновляем список предпочтений
                await loadUserPreferences();
            }
        }
    } catch (error) {
        console.error('Ошибка лайка:', error);
    }
}

// Горячие клавиши
document.addEventListener('keydown', function(e) {
    if (e.code === 'Space' && audioElement) {
        e.preventDefault();
        togglePlayPause();
    } else if (e.code === 'ArrowRight') {
        playNextTrack();
    } else if (e.code === 'ArrowLeft') {
        playPrevTrack();
    } else if (e.code === 'KeyL') {
        toggleLike();
    }
});