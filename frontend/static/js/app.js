// Constants
const API_BASE_URL = 'http://localhost:8000';
const ENDPOINTS = {
    health: '/health',
    schedule: '/schedule',
    games: '/games',
    generateStory: '/generate-story',
    generateAudio: '/api/audio/generate-audio'
};

// DOM Elements
const elements = {
    healthStatus: document.getElementById('healthStatus'),
    seasonSelect: document.getElementById('seasonSelect'),
    gameTypeSelect: document.getElementById('gameTypeSelect'),
    gamesList: document.getElementById('gamesList'),
    storyPreferences: document.getElementById('storyPreferences'),
    preferencesForm: document.getElementById('preferencesForm'),
    storyOutput: document.getElementById('storyOutput'),
    storyText: document.getElementById('storyText'),
    copyStoryBtn: document.getElementById('copyStoryBtn'),
    voiceSelect: document.getElementById('voiceSelect'),
    speedRange: document.getElementById('speedRange'),
    pitchRange: document.getElementById('pitchRange'),
    generateAudioBtn: document.getElementById('generateAudioBtn'),
    audioPlayer: document.getElementById('audioPlayer'),
    storyAudio: document.getElementById('storyAudio'),
    downloadLink: document.getElementById('downloadLink'),
    shareAudioBtn: document.getElementById('shareAudioBtn'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    scrollProgress: document.querySelector('.scroll-progress'),
    header: document.querySelector('.header'),
    generateStoryBtn: document.getElementById('generateStoryBtn'),
    formError: document.getElementById('formError'),
    formErrorMessage: document.getElementById('formError').querySelector('.error-message')
};

// State
let selectedGameId = null;
let currentStoryText = '';
let lastScrollTop = 0;

// Initialize the application
async function init() {
    await checkHealth();
    await loadGames();
    setupEventListeners();
    setupScrollHandlers();
    setupRangeInputs();
}

// Setup scroll handlers
function setupScrollHandlers() {
    window.addEventListener('scroll', () => {
        // Update scroll progress
        const winScroll = document.documentElement.scrollTop;
        const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        const scrolled = (winScroll / height) * 100;
        elements.scrollProgress.style.width = `${scrolled}%`;

        // Handle header visibility
        const currentScrollTop = window.pageYOffset || document.documentElement.scrollTop;
        if (currentScrollTop > lastScrollTop && currentScrollTop > 100) {
            elements.header.classList.add('header-hidden');
        } else {
            elements.header.classList.remove('header-hidden');
        }
        lastScrollTop = currentScrollTop;
    });
}

// Setup range inputs
function setupRangeInputs() {
    const updateRangeProgress = (input) => {
        const min = input.min || 0;
        const max = input.max || 100;
        const value = input.value;
        const percentage = ((value - min) / (max - min)) * 100;
        input.style.setProperty('--range-progress', `${percentage}%`);
        
        const valueDisplay = input.parentElement.querySelector('.range-value');
        if (valueDisplay) {
            valueDisplay.textContent = input.id === 'speedRange' ? `${value}x` : value;
        }
    };

    [elements.speedRange, elements.pitchRange].forEach(input => {
        updateRangeProgress(input);
        input.addEventListener('input', () => updateRangeProgress(input));
    });
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = document.createElement('i');
    icon.className = type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle';
    
    const text = document.createElement('span');
    text.textContent = message;
    
    toast.appendChild(icon);
    toast.appendChild(text);
    
    document.getElementById('toastContainer').appendChild(toast);
    
    // Trigger reflow for animation
    toast.offsetHeight;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Health check with enhanced error handling
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}${ENDPOINTS.health}`);
        const data = await response.json();
        
        const statusDot = elements.healthStatus.querySelector('.status-dot');
        const statusText = elements.healthStatus.querySelector('.status-text');
        
        if (data.status === 'healthy') {
            statusDot.classList.add('healthy');
            statusText.textContent = 'System is healthy';
            showToast('Connected to server successfully', 'success');
        } else {
            statusDot.classList.remove('healthy');
            statusText.textContent = 'System is experiencing issues';
            showToast('System is experiencing issues', 'error');
        }
    } catch (error) {
        console.error('Health check failed:', error);
        elements.healthStatus.querySelector('.status-text').textContent = 'Unable to connect to server';
        showToast('Failed to connect to server', 'error');
    }
}

// Load games with enhanced error handling
async function loadGames() {
    showLoading();
    try {
        const season = elements.seasonSelect.value;
        const gameType = elements.gameTypeSelect.value;
        
        const response = await fetch(`${API_BASE_URL}${ENDPOINTS.schedule}?season=${season}&game_type=${gameType}`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to load games');
        }
        
        renderGames(data.dates || []);
        showToast('Games loaded successfully', 'success');
    } catch (error) {
        console.error('Failed to load games:', error);
        elements.gamesList.innerHTML = '<p class="error">Failed to load games. Please try again later.</p>';
        showToast(error.message, 'error');
    }
    hideLoading();
}

// Render games with enhanced UI
function renderGames(dates) {
    elements.gamesList.innerHTML = '';
    
    if (dates.length === 0) {
        elements.gamesList.innerHTML = '<p class="no-games">No games available for the selected criteria</p>';
        return;
    }
    
    dates.forEach(date => {
        date.games.forEach(game => {
            const card = document.createElement('div');
            card.className = 'game-card';
            card.dataset.gameId = game.gamePk;
            
            const homeTeam = game.teams.home.team.name;
            const awayTeam = game.teams.away.team.name;
            const gameDate = new Date(game.gameDate).toLocaleDateString();
            const gameTime = new Date(game.gameDate).toLocaleTimeString();
            const status = game.status.detailedState;
            
            card.innerHTML = `
                <h3>${awayTeam} @ ${homeTeam}</h3>
                <p><i class="far fa-calendar"></i> ${gameDate}</p>
                <p><i class="far fa-clock"></i> ${gameTime}</p>
                <p class="game-status"><i class="fas fa-info-circle"></i> ${status}</p>
            `;
            
            card.addEventListener('click', () => selectGame(game.gamePk, card));
            elements.gamesList.appendChild(card);
        });
    });
}

// Select game with enhanced feedback
function selectGame(gameId, card) {
    selectedGameId = gameId;
    
    // Update UI
    document.querySelectorAll('.game-card').forEach(c => {
        c.classList.remove('selected');
        c.setAttribute('aria-selected', 'false');
    });
    
    card.classList.add('selected');
    card.setAttribute('aria-selected', 'true');
    
    elements.storyPreferences.classList.remove('hidden');
    elements.storyOutput.classList.add('hidden');
    
    // Smooth scroll to preferences
    elements.storyPreferences.scrollIntoView({ behavior: 'smooth' });
    showToast('Game selected', 'success');
}

// Add these utility functions
function setButtonLoading(button, isLoading) {
    const btnText = button.querySelector('.btn-text');
    const btnLoader = button.querySelector('.btn-loader');
    
    button.disabled = isLoading;
    btnText.style.opacity = isLoading ? '0.7' : '1';
    btnLoader.classList.toggle('hidden', !isLoading);
}

function showFormError(message) {
    elements.formErrorMessage.textContent = message;
    elements.formError.classList.remove('hidden');
    elements.formError.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function hideFormError() {
    elements.formError.classList.add('hidden');
}

// Generate story with enhanced error handling and validation
async function generateStory(preferences) {
    if (!selectedGameId) {
        showFormError('Please select a game first');
        return;
    }

    // Validate preferences
    if (!preferences.focus || preferences.focus.length === 0) {
        showFormError('Please select at least one focus area');
        return;
    }
    
    hideFormError();
    setButtonLoading(elements.generateStoryBtn, true);
    showLoading();

    try {
        // Format game_id as string and ensure preferences are valid
        const requestData = {
            game_id: String(selectedGameId),
            preferences: {
                style: preferences.style || 'dramatic',
                focus: preferences.focus,
                length: preferences.length || 'medium'
            }
        };

        const response = await fetch(`${API_BASE_URL}${ENDPOINTS.generateStory}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            const errorMessage = data.detail || data.message || 'Failed to generate story';
            throw new Error(errorMessage);
        }
        
        // Handle different response formats
        currentStoryText = typeof data === 'string' ? data : 
                         data.story ? data.story :
                         data.content ? data.content : '';
        
        if (!currentStoryText) {
            throw new Error('No story content received');
        }

        // Update UI
        elements.storyText.textContent = currentStoryText;
        elements.storyOutput.classList.remove('hidden');
        elements.audioPlayer.classList.add('hidden');
        
        // Smooth scroll to story
        elements.storyOutput.scrollIntoView({ behavior: 'smooth' });
        showToast('Story generated successfully', 'success');
    } catch (error) {
        console.error('Failed to generate story:', error);
        showFormError(error.message || 'Failed to generate story. Please try again.');
        
        // Clear previous story if error occurs
        elements.storyText.textContent = '';
        elements.storyOutput.classList.add('hidden');
    } finally {
        setButtonLoading(elements.generateStoryBtn, false);
        hideLoading();
    }
}

// Generate audio with enhanced error handling
async function generateAudio() {
    if (!currentStoryText) {
        showToast('Please generate a story first', 'error');
        return;
    }
    
    showLoading();
    try {
        const response = await fetch(`${API_BASE_URL}${ENDPOINTS.generateAudio}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'audio/mpeg'
            },
            body: JSON.stringify({
                text: currentStoryText,
                voice: elements.voiceSelect.value,
                language_code: 'en-US',
                speaking_rate: parseFloat(elements.speedRange.value),
                pitch: parseFloat(elements.pitchRange.value)
            })
        });
        
        if (!response.ok) {
            throw new Error(`Audio generation failed: ${response.statusText}`);
        }
        
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        
        elements.storyAudio.src = audioUrl;
        elements.downloadLink.href = audioUrl;
        elements.audioPlayer.classList.remove('hidden');
        
        showToast('Audio generated successfully', 'success');
    } catch (error) {
        console.error('Failed to generate audio:', error);
        showToast('Failed to generate audio. Please try again.', 'error');
    }
    hideLoading();
}

// Copy story text to clipboard
async function copyStoryText() {
    try {
        await navigator.clipboard.writeText(currentStoryText);
        showToast('Story copied to clipboard', 'success');
    } catch (error) {
        console.error('Failed to copy text:', error);
        showToast('Failed to copy text', 'error');
    }
}

// Share audio
async function shareAudio() {
    try {
        if (navigator.share) {
            await navigator.share({
                title: 'MLB Game Story',
                text: 'Listen to this MLB game story!',
                url: elements.downloadLink.href
            });
            showToast('Story shared successfully', 'success');
        } else {
            throw new Error('Share not supported');
        }
    } catch (error) {
        console.error('Failed to share:', error);
        showToast('Failed to share. Try downloading instead.', 'error');
    }
}

// Setup event listeners with enhanced interaction handling
function setupEventListeners() {
    elements.seasonSelect.addEventListener('change', loadGames);
    elements.gameTypeSelect.addEventListener('change', loadGames);
    
    elements.preferencesForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideFormError();

        const formData = new FormData(e.target);
        
        // Validate form data
        const focus = Array.from(formData.getAll('focus'));
        if (focus.length === 0) {
            showFormError('Please select at least one focus area');
            return;
        }

        const preferences = {
            style: formData.get('style'),
            focus: focus,
            length: formData.get('length')
        };

        // Validate all required fields
        if (!preferences.style || !preferences.length) {
            showFormError('Please fill in all required fields');
            return;
        }

        await generateStory(preferences);
    });
    
    elements.generateAudioBtn.addEventListener('click', generateAudio);
    elements.copyStoryBtn.addEventListener('click', copyStoryText);
    elements.shareAudioBtn.addEventListener('click', shareAudio);
    
    // Add keyboard navigation for game cards
    elements.gamesList.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            const card = e.target.closest('.game-card');
            if (card) {
                e.preventDefault();
                selectGame(card.dataset.gameId, card);
            }
        }
    });

    // Add error reset on form changes
    elements.preferencesForm.querySelectorAll('input, select').forEach(input => {
        input.addEventListener('change', hideFormError);
    });
}

// Loading overlay
function showLoading() {
    elements.loadingOverlay.classList.remove('hidden');
}

function hideLoading() {
    elements.loadingOverlay.classList.add('hidden');
}

// Initialize the app
document.addEventListener('DOMContentLoaded', init); 