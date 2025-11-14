let likedTracks = [];
let currentTrackId = null;
let currentTrackIndex = -1;
let isPlaying = false;
let audioElement = null;

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    audioElement = document.getElementById('compactAudioElement');
    setupAudioEvents();
    loadLikedTracks();
});

// Настройка событий аудио
function setupAudioEvents() {
    audioElement.onended = function() {
        console.log('Трек закончился, включаем следующий');
        playNextLikedTrack();
    };
    
    audioElement.onpause = () => {
        isPlaying = false;
        updateCompactPlayButton();
    };
    
    audioElement.onplay = () => {
        isPlaying = true;
        updateCompactPlayButton();
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

// Отображение лайкнутых треков в столбик
function displayLikedTracks() {
    const tracksList = document.getElementById('likedTracksList');
    const noTracksMessage = document.getElementById('noTracksMessage');
    
    tracksList.innerHTML = '';
    noTracksMessage.style.display = 'none';
    
    likedTracks.forEach((track, index) => {
        const trackItem = createTrackItem(track, index);
        tracksList.appendChild(trackItem);
    });
}

// Создание элемента трека в столбик
function createTrackItem(track, index) {
    const item = document.createElement('div');
    item.className = 'track-item';
    item.setAttribute('data-track-id', track.id);
    item.setAttribute('data-track-index', index);
    
    const artists = Array.isArray(track.artists) ? track.artists.join(', ') : track.artists;
    
    item.innerHTML = `
        <div class="track-item-image">
            ${track.cover_uri ? 
                `<img src="${track.cover_uri}" alt="${track.title}" class="track-item-cover">` : 
                `<div class="track-item-placeholder">🎵</div>`
            }
        </div>
        
        <div class="track-item-info">
            <div class="track-item-title">${track.title}</div>
            <div class="track-item-artist">${artists}</div>
            <div class="track-item-album">${track.album || 'Неизвестный альбом'}</div>
        </div>
        
        <div class="track-item-actions">
            <button class="play-item-btn" onclick="playLikedTrackFromList(${index})" title="Воспроизвести">
                ▶
            </button>
            <button class="remove-item-btn" onclick="removeLikedTrack('${track.id}')" title="Удалить">
                ❌
            </button>
        </div>
    `;
    
    return item;
}

// Воспроизведение трека из списка
async function playLikedTrackFromList(index) {
    if (index < 0 || index >= likedTracks.length) return;
    
    const track = likedTracks[index];
    currentTrackIndex = index;
    
    await playTrackById(track.id, track.title, track.artists, track.cover_uri);
}

// Воспроизведение следующего лайкнутого трека
function playNextLikedTrack() {
    if (likedTracks.length === 0) return;
    
    const nextIndex = (currentTrackIndex + 1) % likedTracks.length;
    playLikedTrackFromList(nextIndex);
}

// Воспроизведение предыдущего лайкнутого трека
function playPrevLikedTrack() {
    if (likedTracks.length === 0) return;
    
    const prevIndex = (currentTrackIndex - 1 + likedTracks.length) % likedTracks.length;
    playLikedTrackFromList(prevIndex);
}

// Воспроизведение трека по ID
async function playTrackById(trackId, title, artists, coverUri) {
    const compactPlayer = document.getElementById('compactPlayer');
    const compactTitle = document.getElementById('compactTitle');
    const compactArtist = document.getElementById('compactArtist');
    const compactCover = document.getElementById('compactCover');
    const compactLikeBtn = document.getElementById('compactLikeBtn');
    
    currentTrackId = trackId;
    
    // Показываем компактный плеер
    compactPlayer.style.display = 'block';
    
    // Обновляем информацию о треке
    compactTitle.textContent = title;
    compactArtist.textContent = Array.isArray(artists) ? artists.join(', ') : artists;
    
    // Обновляем обложку
    if (coverUri) {
        compactCover.innerHTML = `<img src="${coverUri}" alt="${title}" class="compact-cover-image">`;
    } else {
        compactCover.innerHTML = '<div class="compact-placeholder">🎵</div>';
    }
    
    // Устанавливаем лайк как активный
    compactLikeBtn.innerHTML = '❤️';
    compactLikeBtn.classList.add('liked');
    
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
        // При ошибке пробуем следующий трек
        setTimeout(() => playNextLikedTrack(), 1000);
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
            
            // Если удаляемый трек сейчас играет - останавливаем и включаем следующий
            if (currentTrackId === trackId) {
                audioElement.pause();
                audioElement.src = '';
                currentTrackId = null;
                currentTrackIndex = -1;
                
                // Если есть другие треки - включаем следующий
                if (likedTracks.length > 0) {
                    playNextLikedTrack();
                } else {
                    // Скрываем плеер если треков не осталось
                    document.getElementById('compactPlayer').style.display = 'none';
                }
            }
        }
    } catch (error) {
        console.error('Ошибка удаления трека:', error);
        alert('Ошибка при удалении трека');
    }
}

// Переключение воспроизведения/паузы в компактном плеере
function toggleCompactPlayPause() {
    if (isPlaying) {
        audioElement.pause();
    } else {
        audioElement.play();
    }
}

// Обновление кнопки воспроизведения в компактном плеере
function updateCompactPlayButton() {
    const playBtn = document.getElementById('compactPlayBtn');
    const playIcon = document.getElementById('compactPlayIcon');
    
    if (isPlaying) {
        playIcon.innerHTML = '<path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>';
        playBtn.setAttribute('title', 'Пауза');
    } else {
        playIcon.innerHTML = '<path d="M8 5v14l11-7z"/>';
        playBtn.setAttribute('title', 'Воспроизвести');
    }
}

// Переключение лайка в компактном плеере
async function toggleCompactLike() {
    if (!currentTrackId) return;
    
    await removeLikedTrack(currentTrackId);
}

// Показать сообщение когда нет треков
function showNoTracksMessage() {
    const tracksList = document.getElementById('likedTracksList');
    const noTracksMessage = document.getElementById('noTracksMessage');
    
    tracksList.innerHTML = '';
    noTracksMessage.style.display = 'block';
}