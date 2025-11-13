// Загрузка и воспроизведение музыки
async function loadAndPlayMusic() {
    const musicContainer = document.getElementById('musicContainer');
    const tracksGrid = document.getElementById('tracksGrid');
    const listenBtn = document.querySelector('.listen-btn');
    
    // Показываем загрузку
    listenBtn.innerHTML = '🔄 Загружаем треки...';
    listenBtn.disabled = true;
    
    try {
        // Получаем популярные треки
        const response = await fetch('/api/popular');
        const data = await response.json();
        
        if (data.tracks && data.tracks.length > 0) {
            // Скрываем кнопку и показываем треки
            listenBtn.style.display = 'none';
            musicContainer.style.display = 'block';
            
            // Добавляем треки в сетку
            tracksGrid.innerHTML = '';
            data.tracks.forEach(track => {
                const trackCard = createTrackCard(track);
                tracksGrid.appendChild(trackCard);
            });
            
            // Автоматически играем первый трек
            const firstTrack = data.tracks[0];
            await playTrackById(firstTrack.id, firstTrack.title, firstTrack.artists.join(', '));
            
        } else {
            alert('Не удалось загрузить треки');
            listenBtn.innerHTML = '🎵 Слушать музыку';
            listenBtn.disabled = false;
        }
        
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка при загрузке музыки');
        listenBtn.innerHTML = '🎵 Слушать музыку';
        listenBtn.disabled = false;
    }
}

// Создание карточки трека
function createTrackCard(track) {
    const card = document.createElement('div');
    card.className = 'track-card';
    card.setAttribute('data-track-id', track.id);
    
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
        
        <button class="play-btn" onclick="playTrack(this)">▶</button>
    `;
    
    return card;
}

// Воспроизведение трека по ID
async function playTrackById(trackId, title, artist) {
    const audioPlayer = document.getElementById('audioPlayer');
    const audioElement = document.getElementById('audioElement');
    const nowPlaying = document.getElementById('nowPlaying');
    
    audioPlayer.style.display = 'block';
    nowPlaying.textContent = `Сейчас играет: ${artist} - ${title}`;
    
    try {
        const response = await fetch(`/music/track/${trackId}`);
        const data = await response.json();
        
        if (data.download_url) {
            audioElement.src = data.download_url;
            await audioElement.play();
        } else {
            alert(data.error || 'Не удалось загрузить трек');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка при загрузке трека');
    }
}

// Воспроизведение трека при клике
async function playTrack(button) {
    const trackCard = button.closest('.track-card');
    const trackId = trackCard.dataset.trackId;
    const trackTitle = trackCard.querySelector('.track-title').textContent;
    const trackArtist = trackCard.querySelector('.track-artist').textContent;
    
    await playTrackById(trackId, trackTitle, trackArtist);
}