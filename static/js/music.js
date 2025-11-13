let currentTrackId = null;
let isPlaying = false;

/// В функции loadAndPlayMusic добавляем обработку ошибок
async function loadAndPlayMusic() {
    const musicContainer = document.getElementById('musicContainer');
    const tracksGrid = document.getElementById('tracksGrid');
    const listenBtn = document.querySelector('.listen-btn');
    
    listenBtn.innerHTML = '🔄 Загружаем треки...';
    listenBtn.disabled = true;
    
    try {
        const response = await fetch('/api/popular');
        const data = await response.json();
        
        if (data.tracks && data.tracks.length > 0) {
            listenBtn.style.display = 'none';
            musicContainer.style.display = 'block';
            
            tracksGrid.innerHTML = '';
            data.tracks.forEach((track, index) => {
                const trackCard = createTrackCard(track, index === 0);
                tracksGrid.appendChild(trackCard);
            });
            
            const firstTrack = data.tracks[0];
            await playTrackById(firstTrack.id, firstTrack.title, firstTrack.artists.join(', '));
            
        } else {
            throw new Error(data.error || 'Не удалось загрузить треки');
        }
        
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка при загрузке музыки: ' + (error.message || 'Неизвестная ошибка'));
        listenBtn.innerHTML = '🎵 Слушать музыку';
        listenBtn.disabled = false;
    }
}   

// Создание карточки трека
function createTrackCard(track, isFirst = false) {
    const card = document.createElement('div');
    card.className = 'track-card';
    card.setAttribute('data-track-id', track.id);
    
    if (isFirst) {
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
        
        <button class="play-btn ${isFirst ? 'playing' : ''}" onclick="playTrack(this)">
            ${isFirst ? '⏸️' : '▶'}
        </button>
    `;
    
    return card;
}

// Воспроизведение трека по ID
async function playTrackById(trackId, title, artist) {
    const audioPlayer = document.getElementById('audioPlayer');
    const audioElement = document.getElementById('audioElement');
    const nowPlaying = document.getElementById('nowPlaying');
    
    // Обновляем текущий трек
    currentTrackId = trackId;
    
    // Показываем плеер
    audioPlayer.style.display = 'block';
    nowPlaying.textContent = `Сейчас играет: ${artist} - ${title}`;
    
    // Обновляем кнопки на всех карточках
    updatePlayButtons(trackId);
    
    try {
        const response = await fetch(`/music/track/${trackId}`);
        const data = await response.json();
        
        if (data.download_url) {
            audioElement.src = data.download_url;
            await audioElement.play();
            isPlaying = true;
            
            // Слушаем события аудио
            audioElement.onpause = () => {
                isPlaying = false;
                updatePlayButtons(null);
            };
            
            audioElement.onplay = () => {
                isPlaying = true;
                updatePlayButtons(trackId);
            };
            
        } else {
            throw new Error(data.error || 'Не удалось загрузить трек');
        }
        
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка при загрузке трека: ' + error.message);
    }
}

// Воспроизведение трека при клике
async function playTrack(button) {
    const trackCard = button.closest('.track-card');
    const trackId = trackCard.dataset.trackId;
    const trackTitle = trackCard.querySelector('.track-title').textContent;
    const trackArtist = trackCard.querySelector('.track-artist').textContent;
    
    const audioElement = document.getElementById('audioElement');
    
    // Если кликаем на текущий трек - пауза/плей
    if (trackId === currentTrackId) {
        if (isPlaying) {
            await audioElement.pause();
        } else {
            await audioElement.play();
        }
    } else {
        // Иначе играем новый трек
        await playTrackById(trackId, trackTitle, trackArtist);
    }
}

// Обновление кнопок воспроизведения
function updatePlayButtons(playingTrackId) {
    const allTrackCards = document.querySelectorAll('.track-card');
    const audioElement = document.getElementById('audioElement');
    
    allTrackCards.forEach(card => {
        const playBtn = card.querySelector('.play-btn');
        const cardTrackId = card.dataset.trackId;
        
        if (cardTrackId === playingTrackId && !audioElement.paused) {
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