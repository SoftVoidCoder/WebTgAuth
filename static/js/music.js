async function playTrack(button) {
    const trackCard = button.closest('.track-card');
    const trackId = trackCard.dataset.trackId;
    const trackTitle = trackCard.querySelector('.track-title').textContent;
    const trackArtist = trackCard.querySelector('.track-artist').textContent;
    
    const audioPlayer = document.getElementById('audioPlayer');
    const audioElement = document.getElementById('audioElement');
    const nowPlaying = document.getElementById('nowPlaying');
    
    audioPlayer.style.display = 'block';
    nowPlaying.textContent = `Сейчас играет: ${trackArtist} - ${trackTitle}`;
    
    try {
        const response = await fetch(`/track/${trackId}`);
        const data = await response.json();
        
        if (data.download_url) {
            audioElement.src = data.download_url;
            audioElement.play().catch(e => {
                console.error('Ошибка воспроизведения:', e);
                alert('Не удалось воспроизвести трек');
            });
        } else {
            alert(data.error || 'Не удалось загрузить трек');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка при загрузке трека');
    }
}