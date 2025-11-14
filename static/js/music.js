let currentTrackId = null;
let isPlaying = false;
let currentTrackIndex = 0;
let tracksList = [];
let audioElement = null;

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    audioElement = document.getElementById('audioElement');
    addPlayerControls();
});

// Загрузка и воспроизведение музыки
async function loadAndPlayMusic() {
    const musicContainer = document.getElementById('musicContainer');
    const tracksGrid = document.getElementById('tracksGrid');
    const listenBtn = document.querySelector('.listen-btn');
    
    listenBtn.innerHTML = '🔄 Загружаем треки...';
    listenBtn.disabled = true;
    
    try {
        await loadNewTracks();
        
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка при загрузке музыки: ' + (error.message || 'Неизвестная ошибка'));
        listenBtn.innerHTML = '🎵 Слушать музыку';
        listenBtn.disabled = false;
    }
}

// Загрузка новых треков
async function loadNewTracks() {
    const musicContainer = document.getElementById('musicContainer');
    const tracksGrid = document.getElementById('tracksGrid');
    const listenBtn = document.querySelector('.listen-btn');
    
    const response = await fetch('/api/popular');
    const data = await response.json();
    
    if (data.tracks && data.tracks.length > 0) {
        tracksList = data.tracks;
        currentTrackIndex = 0;
        
        listenBtn.style.display = 'none';
        musicContainer.style.display = 'block';
        
        // Добавляем треки в сетку
        tracksGrid.innerHTML = '';
        tracksList.forEach((track, index) => {
            const trackCard = createTrackCard(track, index === 0);
            tracksGrid.appendChild(trackCard);
        });
        
        // Автоматически играем первый трек
        await playTrackByIndex(0);
        
    } else {
        throw new Error(data.error || 'Не удалось загрузить треки');
    }
}

// Воспроизведение трека по индексу
async function playTrackByIndex(index) {
    if (index < 0 || index >= tracksList.length) return;
    
    const track = tracksList[index];
    currentTrackIndex = index;
    
    await playTrackById(track.id, track.title, track.artists.join(', '));
}

// Воспроизведение следующего трека
async function playNextTrack() {
    const nextIndex = currentTrackIndex + 1;
    
    if (nextIndex >= tracksList.length) {
        // Если это последний трек в списке - загружаем новые треки
        console.log('Загружаем новые треки...');
        await loadNewTracks();
    } else {
        // Иначе играем следующий трек
        playTrackByIndex(nextIndex);
    }
}

// Воспроизведение предыдущего трека
function playPrevTrack() {
    if (currentTrackIndex > 0) {
        playTrackByIndex(currentTrackIndex - 1);
    }
}

// Воспроизведение трека по ID
async function playTrackById(trackId, title, artist) {
    const audioPlayer = document.getElementById('audioPlayer');
    const nowPlaying = document.getElementById('nowPlaying');
    
    currentTrackId = trackId;
    
    audioPlayer.style.display = 'block';
    nowPlaying.textContent = `Сейчас играет: ${artist} - ${title}`;
    
    // Обновляем кнопки на всех карточках
    updatePlayButtons(trackId);
    
    try {
        const response = await fetch(`/music/track/${trackId}`);
        const data = await response.json();
        
        if (data.download_url) {
            audioElement.src = data.download_url;
            
            // Сбрасываем все предыдущие обработчики
            audioElement.onended = null;
            audioElement.onpause = null;
            audioElement.onplay = null;
            
            // Устанавливаем новые обработчики
            audioElement.onended = async function() {
                console.log('Трек закончился, включаем следующий');
                await playNextTrack();
            };
            
            audioElement.onpause = () => {
                isPlaying = false;
                updatePlayButtons(null);
            };
            
            audioElement.onplay = () => {
                isPlaying = true;
                updatePlayButtons(trackId);
            };
            
            // Воспроизводим без задержки
            await audioElement.play().catch(e => {
                console.error('Ошибка воспроизведения:', e);
            });
            isPlaying = true;
            
        } else {
            throw new Error(data.error || 'Не удалось загрузить трек');
        }
        
    } catch (error) {
        console.error('Ошибка:', error);
        // Автоматически переходим к следующему треку при ошибке
        setTimeout(() => playNextTrack(), 1000);
    }
}

// Создание карточки трека
function createTrackCard(track, isPlaying = false) {
    const card = document.createElement('div');
    card.className = 'track-card';
    card.setAttribute('data-track-id', track.id);
    card.setAttribute('data-track-index', tracksList.indexOf(track));
    
    if (isPlaying) {
        card.classList.add('playing');
    }
    
    card.innerHTML = `
        <div class="track-image">
            ${track.cover_uri ? 
                `<img src="${track.cover_uri}" alt="${track.title}" class="track-cover">` : 
                `<div class="track-placeholder">🎵</div>`
            }
        </div>
        
        <div class="track-info">
            <h3 class="track-title">${track.title}</h3>
            <p class="track-artist">${track.artists.join(', ')}</p>
            <p class="track-album">${track.album}</p>
        </div>
        
        <button class="play-btn ${isPlaying ? 'playing' : ''}" onclick="playTrack(this)">
            ${isPlaying ? '⏸️' : '▶'}
        </button>
    `;
    
    return card;
}

// Воспроизведение трека при клике
async function playTrack(button) {
    const trackCard = button.closest('.track-card');
    const trackId = trackCard.dataset.trackId;
    const trackIndex = parseInt(trackCard.dataset.trackIndex);
    
    // Если кликаем на текущий трек - пауза/плей
    if (trackId === currentTrackId) {
        if (isPlaying) {
            await audioElement.pause();
        } else {
            await audioElement.play();
        }
    } else {
        // Иначе играем новый трек по индексу
        currentTrackIndex = trackIndex;
        const trackTitle = trackCard.querySelector('.track-title').textContent;
        const trackArtist = trackCard.querySelector('.track-artist').textContent;
        await playTrackById(trackId, trackTitle, trackArtist);
    }
}

// Обновление кнопок воспроизведения
function updatePlayButtons(playingTrackId) {
    const allTrackCards = document.querySelectorAll('.track-card');
    
    allTrackCards.forEach(card => {
        const playBtn = card.querySelector('.play-btn');
        const cardTrackId = card.dataset.trackId;
        
        if (cardTrackId === playingTrackId && isPlaying) {
            card.classList.add('playing');
            playBtn.classList.add('playing');
            playBtn.innerHTML = '⏸️';
        } else {
            card.classList.remove('playing');
            playBtn.classList.remove('playing');
            playBtn.innerHTML = '▶';
        }
    });
}

// Кнопки управления для плеера
function addPlayerControls() {
    const audioPlayer = document.getElementById('audioPlayer');
    if (!audioPlayer.querySelector('.player-controls')) {
        const controlsHTML = `
            <div class="player-controls">
                <button class="control-btn" onclick="playPrevTrack()" title="Предыдущий">⏮️</button>
                <button class="control-btn" onclick="playNextTrack()" title="Следующий">⏭️</button>
                <button class="control-btn" onclick="loadNewTracks()" title="Новые треки">🔄</button>
            </div>
        `;
        audioPlayer.insertAdjacentHTML('beforeend', controlsHTML);
    }
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
    } else if (e.code === 'ArrowLeft') {
        playPrevTrack();
    } else if (e.code === 'KeyN') {
        loadNewTracks();
    }
});