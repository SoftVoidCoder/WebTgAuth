// music.js
let currentTrackId = null;
let isPlaying = false;
let currentTrackIndex = 0;
let tracksList = [];
let audioElement = null;
let currentTrackData = null;
let userLikedTracks = [];
let musicPreference = 'liked'; // По умолчанию - любимое

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    audioElement = document.getElementById('audioElement');
    setupAudioEvents();
    setupVolumeControl();
    loadUserPreferences();
    
    // Загружаем сохраненные настройки
    const savedPreference = localStorage.getItem('musicPreference');
    if (savedPreference) {
        musicPreference = savedPreference;
    }
});

// Настройка событий аудио
function setupAudioEvents() {
    audioElement.onended = async function() {
        await playNextTrack();
    };
    
    audioElement.onpause = () => {
        isPlaying = false;
        updatePlayButton();
        const listenBtn = document.querySelector('.listen-btn');
        if (listenBtn && audioElement.src) {
            listenBtn.innerHTML = '🎵 Продолжить';
            listenBtn.classList.remove('playing');
        }
    };
    
    audioElement.onplay = () => {
        isPlaying = true;
        updatePlayButton();
        const listenBtn = document.querySelector('.listen-btn');
        if (listenBtn) {
            listenBtn.innerHTML = '⏸️ Пауза';
            listenBtn.classList.add('playing');
        }
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

// Показать настройки
function showPreferences() {
    const preferencesSection = document.getElementById('preferencesSection');
    preferencesSection.style.display = 'flex';
    
    // Устанавливаем текущую настройку
    const currentPreference = document.querySelector(`input[name="musicPreference"][value="${musicPreference}"]`);
    if (currentPreference) {
        currentPreference.checked = true;
    }
}

// Скрыть настройки
function hidePreferences() {
    const preferencesSection = document.getElementById('preferencesSection');
    preferencesSection.style.display = 'none';
}

// Применить настройки
function applyPreferences() {
    const selectedPreference = document.querySelector('input[name="musicPreference"]:checked');
    if (selectedPreference) {
        musicPreference = selectedPreference.value;
        console.log('Выбрана настройка:', musicPreference);
        
        // Сохраняем в localStorage
        localStorage.setItem('musicPreference', musicPreference);
        
        hidePreferences();
        
        // Если музыка играет, перезапускаем с новыми настройками
        if (isPlaying) {
            restartRadioWithNewPreferences();
        }
    }
}

// Перезапуск радио с новыми настройками
async function restartRadioWithNewPreferences() {
    console.log('Перезапускаем радио с настройкой:', musicPreference);
    
    // Останавливаем текущее воспроизведение
    audioElement.pause();
    isPlaying = false;
    
    // Загружаем треки по новой настройке
    await loadTracksByPreference();
    
    if (tracksList.length > 0) {
        await playTrack(tracksList[0]);
    }
}

// Загрузка треков по выбранной настройке
async function loadTracksByPreference() {
    switch (musicPreference) {
        case 'liked':
            await loadTracksBasedOnLikes();
            break;
        case 'popular':
            await loadNewTracks();
            break;
        case 'discover':
            await loadDiscoveryTracks();
            break;
        default:
            await loadTracksBasedOnLikes();
    }
}

// Загрузка треков для открытия нового
async function loadDiscoveryTracks() {
    console.log('Загружаем незнакомые треки...');
    
    // Используем случайные популярные запросы для разнообразия
    const discoveryQueries = [
        "новинки музыки 2024",
        "русская музыка 2024",
        "зарубежная музыка 2024",
        "популярные треки",
        "хиты недели"
    ];
    
    const randomQuery = discoveryQueries[Math.floor(Math.random() * discoveryQueries.length)];
    const foundTracks = await searchTracks(randomQuery);
    
    if (foundTracks.length > 0) {
        tracksList = foundTracks;
        console.log('Найдено незнакомых треков:', tracksList.length);
    } else {
        // Если не нашли, используем популярные
        await loadNewTracks();
    }
}

// Запуск радио с учетом предпочтений
async function startRadio() {
    const listenBtn = document.querySelector('.listen-btn');
    
    // Если музыка уже играет - ставим на паузу
    if (isPlaying) {
        audioElement.pause();
        listenBtn.innerHTML = '🎵 Продолжить';
        listenBtn.classList.remove('playing');
        return;
    }
    
    // Если музыка на паузе - продолжаем
    if (audioElement.src && !isPlaying) {
        await audioElement.play();
        listenBtn.innerHTML = '⏸️ Пауза';
        listenBtn.classList.add('playing');
        return;
    }
    
    // Запускаем новое радио
    listenBtn.innerHTML = '🔄 Загружаем музыку...';
    listenBtn.disabled = true;
    
    try {
        // Загружаем треки по выбранной настройке
        await loadTracksByPreference();
        
        const audioPlayer = document.getElementById('audioPlayer');
        listenBtn.innerHTML = '⏸️ Пауза';
        listenBtn.disabled = false;
        listenBtn.classList.add('playing');
        audioPlayer.style.display = 'block';
        
        if (tracksList.length > 0) {
            await playTrack(tracksList[0]);
        }
        
    } catch (error) {
        console.error('Ошибка:', error);
        listenBtn.innerHTML = '🎵 Слушать музыку';
        listenBtn.disabled = false;
        listenBtn.classList.remove('playing');
    }
}

// Загрузка треков на основе лайков пользователя
async function loadTracksBasedOnLikes() {
    if (userLikedTracks.length === 0) {
        await loadNewTracks();
        return;
    }
    
    console.log('Анализируем ваши музыкальные вкусы...');
    
    // Анализируем предпочтения пользователя
    const userPreferences = analyzeUserPreferences();
    console.log('Найдены предпочтения:', userPreferences);
    
    // Стратегия 1: По самым частым артистам (самая точная)
    if (userPreferences.topArtists.length > 0) {
        const randomArtist = userPreferences.topArtists[0];
        console.log(`Ищем треки артиста: ${randomArtist}`);
        const foundTracks = await searchTracks(randomArtist);
        if (foundTracks.length > 0) {
            tracksList = foundTracks;
            console.log('Найдено треков по артисту:', tracksList.length);
            return;
        }
    }
    
    // Стратегия 2: По жанрам из лайков
    if (userPreferences.possibleGenres.length > 0) {
        for (let genre of userPreferences.possibleGenres) {
            console.log(`Ищем треки жанра: ${genre}`);
            const foundTracks = await searchTracks(genre + ' 2024');
            if (foundTracks.length > 0) {
                tracksList = foundTracks;
                console.log('Найдено треков по жанру:', tracksList.length);
                return;
            }
        }
    }
    
    // Стратегия 3: Похожие артисты
    if (userPreferences.topArtists.length > 1) {
        const similarArtist = userPreferences.topArtists[1];
        console.log(`Ищем похожих артистов: ${similarArtist}`);
        const foundTracks = await searchTracks(similarArtist);
        if (foundTracks.length > 0) {
            tracksList = foundTracks;
            console.log('Найдено треков похожих артистов:', tracksList.length);
            return;
        }
    }
    
    // Если ничего не нашли - используем популярные
    console.log('Не удалось найти рекомендации, используем популярные треки');
    await loadNewTracks();
}

// Анализ предпочтений пользователя
function analyzeUserPreferences() {
    const artistCount = {};
    const possibleGenres = new Set();
    
    userLikedTracks.forEach(track => {
        // Анализируем артистов
        if (track.artists && Array.isArray(track.artists)) {
            track.artists.forEach(artist => {
                artistCount[artist] = (artistCount[artist] || 0) + 1;
            });
        }
        
        // Пытаемся определить жанры по названию трека и артистам
        analyzeGenres(track, possibleGenres);
    });
    
    // Сортируем артистов по популярности
    const topArtists = Object.entries(artistCount)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(entry => entry[0]);
    
    return {
        topArtists: topArtists,
        possibleGenres: Array.from(possibleGenres)
    };
}

// Анализ возможных жанров по треку
function analyzeGenres(track, genresSet) {
    const title = track.title?.toLowerCase() || '';
    const artists = track.artists?.join(' ').toLowerCase() || '';
    const album = track.album?.toLowerCase() || '';
    
    const text = title + ' ' + artists + ' ' + album;
    
    // ТОЛЬКО нормальные жанры - русский рэп, фонк и т.д.
    const genreKeywords = {
        'рэп': ['рэп', 'rap', 'хип-хоп', 'hip-hop', 'бит', 'баттл', 'miyagi', 'kizaru', 'моргенштерн', 'face', 'scriptonite'],
        'фонк': ['фонк', 'phonk', 'дрилл', 'drill', 'memphis'],
        'треп': ['треп', 'trap'],
        'альтернатива': ['альтернатив', 'alternative', 'инди', 'indie'],
        'поп-рэп': ['поп-рэп', 'pop rap', 'лсп', 'max korzh']
    };
    
    Object.entries(genreKeywords).forEach(([genre, keywords]) => {
        if (keywords.some(keyword => text.includes(keyword))) {
            genresSet.add(genre);
        }
    });
    
    // Если жанр не определился, ставим рэп по умолчанию
    if (genresSet.size === 0) {
        genresSet.add('рэп');
    }
}

// Поиск треков по запросу
async function searchTracks(query) {
    try {
        const response = await fetch(`/api/similar?query=${encodeURIComponent(query)}`);
        const data = await response.json();
        return data.tracks || [];
    } catch (error) {
        console.error('Ошибка поиска треков:', error);
        return [];
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
    // Загружаем новые треки по текущей настройке
    await loadTracksByPreference();
    
    if (tracksList.length > 0) {
        const randomIndex = Math.floor(Math.random() * tracksList.length);
        await playTrack(tracksList[randomIndex]);
    } else {
        // Если не нашли - грузим популярные
        await loadNewTracks();
        if (tracksList.length > 0) {
            const randomIndex = Math.floor(Math.random() * tracksList.length);
            await playTrack(tracksList[randomIndex]);
        }
    }
}

// Воспроизведение предыдущего трека
async function playPrevTrack() {
    // Для предыдущего тоже новые треки
    await playNextTrack();
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
    const listenBtn = document.querySelector('.listen-btn');
    
    if (isPlaying) {
        audioElement.pause();
        if (listenBtn) {
            listenBtn.innerHTML = '🎵 Продолжить';
            listenBtn.classList.remove('playing');
        }
    } else {
        audioElement.play();
        if (listenBtn) {
            listenBtn.innerHTML = '⏸️ Пауза';
            listenBtn.classList.add('playing');
        }
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