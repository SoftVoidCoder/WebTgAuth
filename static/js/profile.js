let likedTracks = [];
let currentTrackId = null;
let isPlaying = false;
let audioElement = null;

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    audioElement = document.getElementById('audioElement');
    setupAudioEvents();
    loadLikedTracks();
});

// Настройка событий аудио
function setupAudioEvents() {
    audioElement.onended = function() {
        isPlaying = false;
        updatePlayButton();
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

// Загрузка лайкнутых треков
async function loadLikedTracks() {
    try {
        const response = await fetch('/api/liked-tracks');
        const data = await response.json();
        
        if (data.tracks && data.tracks.length > 0) {
            likedTracks = data.tracks;
            displayLikedTracks();
        } else {
            showNoTracksMessage();
        }
    } catch (error) {
        console.error('Ошибка загрузки лайкнутых треков:', error);
        showNoTracksMessage();
    }
}

// Отображение лайкнутых треков
function displayLikedTracks() {
    const tracksGrid = document.getElementById('likedTracksGrid');
    const noTracksMessage = document.getElementById('noTracksMessage');
    
    tracksGrid.innerHTML = '';
    noTracksMessage.style.display = 'none';
    
    likedTracks.forEach((track, index) => {
        const trackCard = createTrackCard(track, index);
        tracksGrid.appendChild(trackCard);
    });
}

// Показать сообщение когда нет треков
function showNoTracksMessage() {
    const tracksGrid = document.getElementById('likedTracksGrid');
    const noTracksMessage = document.getElementById('noTracksMessage');
    
    tracksGrid.innerHTML = '';
    noTracksMessage.style.display = 'block';
}

// Создание карточки трека
function createTrackCard(track, index) {
    const card = document.createElement('div');
    card.className = 'track-card';
    card.setAttribute('data-track-id', track.id);
    card.setAttribute('data-track-index', index);
    
    card.innerHTML = `
        <div class="track-image">
            ${track.cover_uri ? 
                `<img src="${track.cover_uri}" alt="${track.title}" class="track-cover">` : 
                `<div class="track-placeholder">🎵</div>`
            }
        </div>
        
        <div class="track-info">
            <h3 class="track-title">${track.title}</h3>
            <p class="track-artist">${Array.isArray(track.artists) ? track.artists.join(', ') : track.artists}</p>
            <p class="track-album">${track.album || 'Неизвестный альбом'}</p>
        </div>
        
        <div class="track-actions">
            <button class="play-track-btn" onclick="playLikedTrack(this)" title="Воспроизвести">
                ▶
            </button>
            <button class="remove-track-btn" onclick="removeLikedTrack('${track.id}')" title="Удалить">
                ❌
            </button>
        </div>
    `;
    
    return card;
}

// Воспроизведение лайкнутого трека
async function playLikedTrack(button) {
    const trackCard = button.closest('.track-card');
    const trackId = trackCard.dataset.trackId;
    const trackIndex = parseInt(trackCard.dataset.trackIndex);
    const track = likedTracks[trackIndex];
    
    await playTrackById(trackId, track.title, track.artists, track.cover_uri, track);
}

// Воспроизведение трека по ID
async function playTrackById(trackId, title, artists, coverUri, trackData) {
    const audioPlayer = document.getElementById('audioPlayer');
    const nowPlayingTitle = document.getElementById('nowPlayingTitle');
    const nowPlayingArtist = document.getElementById('nowPlayingArtist');
    const trackCover = document.getElementById('trackCover');
    const likeBtn = document.getElementById('likeBtn');
    
    currentTrackId = trackId;
    
    // Показываем плеер
    audioPlayer.style.display = 'block';
    
    // Обновляем информацию о треке
    nowPlayingTitle.textContent = title;
    nowPlayingArtist.textContent = Array.isArray(artists) ? artists.join(', ') : artists;
    
    // Обновляем обложку
    if (coverUri) {
        trackCover.innerHTML = `<img src="${coverUri}" alt="${title}" class="cover-image">`;
    } else {
        trackCover.innerHTML = '<div class="cover-placeholder">🎵</div>';
    }
    
    // Устанавливаем лайк как активный
    likeBtn.innerHTML = '❤️';
    likeBtn.classList.add('liked');
    
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
        alert('Ошибка при загрузке трека: ' + error.message);
    }
}

// Удаление трека из лайкнутых
async function removeLikedTrack(trackId) {
    if (!confirm('Удалить трек из "Мне нравится"?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/unlike/${trackId}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        
        if (data.status === 'unliked') {
            // Обновляем список треков
            await loadLikedTracks();
            
            // Если удаляемый трек сейчас играет - останавливаем
            if (currentTrackId === trackId) {
                audioElement.pause();
                audioElement.src = '';
                currentTrackId = null;
            }
        }
    } catch (error) {
        console.error('Ошибка удаления трека:', error);
        alert('Ошибка при удалении трека');
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

// Переключение лайка
async function toggleLike() {
    if (!currentTrackId) return;
    
    const likeBtn = document.getElementById('likeBtn');
    
    try {
        if (likeBtn.classList.contains('liked')) {
            // Удаляем лайк
            await removeLikedTrack(currentTrackId);
        }
    } catch (error) {
        console.error('Ошибка лайка:', error);
    }
}

// Воспроизведение следующего трека
function playNextTrack() {
    // Для профиля можно сделать последовательное воспроизведение
    // или оставить как есть
    console.log('Next track functionality for profile');
}

// Воспроизведение предыдущего трека
function playPrevTrack() {
    console.log('Previous track functionality for profile');
}