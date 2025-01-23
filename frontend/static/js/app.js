// Constants
const API_BASE_URL = 'http://localhost:8000';
const ENDPOINTS = {
    health: '/health',
    schedule: '/schedule',
    games: '/games',
    generateStory: '/generate-story',
    generateAudio: '/api/audio/generate-audio',
    voices: '/api/audio/voices'
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
    formErrorMessage: document.getElementById('formError').querySelector('.error-message'),
    languageSelect: document.getElementById('languageSelect')
};

// State
let selectedGameId = null;
let currentStoryText = '';
let lastScrollTop = 0;
let isGeneratingStory = false;
let storyDisplayTimeout = null;

// Initialize the application
async function init() {
    await checkHealth();
    await loadGames();
    await updateVoiceOptions('en-US');
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
    
    // Reset story section
    updateStoryDisplay('', false);
    elements.storyPreferences.classList.remove('hidden');
    
    // Smooth scroll to preferences
    elements.storyPreferences.scrollIntoView({ behavior: 'smooth' });
    showToast('Game selected', 'success');
}

// Add these utility functions
function setButtonLoading(button, isLoading) {
    if (!button) return;
    
    const btnText = button.querySelector('.btn-text');
    const btnLoader = button.querySelector('.btn-loader');
    
    button.disabled = isLoading;
    
    if (btnText) {
        btnText.style.opacity = isLoading ? '0.7' : '1';
    }
    
    if (btnLoader) {
        btnLoader.classList.toggle('hidden', !isLoading);
    }
}

function showFormError(message) {
    elements.formErrorMessage.textContent = message;
    elements.formError.classList.remove('hidden');
    elements.formError.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function hideFormError() {
    elements.formError.classList.add('hidden');
}

// Add this new function for managing story display
function updateStoryDisplay(text, shouldShow = true) {
    clearTimeout(storyDisplayTimeout);
    
    if (shouldShow && text) {
        // First, make sure the container is visible
        elements.storyOutput.style.display = 'block';
        elements.storyOutput.classList.remove('hidden');
        
        // Reset animation classes
        elements.storyText.classList.remove('no-animation');
        void elements.storyText.offsetWidth; // Force reflow
        
        // Update content
        elements.storyText.textContent = text;
        
        // Add animation class
        elements.storyText.classList.add('fade-in');
        
        // Scroll after a short delay
        storyDisplayTimeout = setTimeout(() => {
            elements.storyOutput.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
    } else {
        elements.storyText.textContent = '';
        elements.storyOutput.classList.add('hidden');
        elements.storyOutput.style.display = 'none';
    }
}

// Generate story with enhanced error handling and validation
async function generateStory(preferences) {
    if (isGeneratingStory) {
        showToast('Story generation in progress...', 'info');
        return;
    }

    if (!selectedGameId) {
        showFormError('Please select a game first');
        return;
    }

    if (!preferences.focus || preferences.focus.length === 0) {
        showFormError('Please select at least one focus area');
        return;
    }
    
    isGeneratingStory = true;
    hideFormError();
    setButtonLoading(elements.generateStoryBtn, true);
    showLoading();

    try {
        const requestData = {
            game_id: String(selectedGameId),
            preferences: {
                style: preferences.style || 'dramatic',
                focus_areas: preferences.focus,
                story_length: preferences.length || 'medium',
                include_player_stats: true,
                highlight_key_moments: true,
                tone: preferences.style
            }
        };

        console.log('Sending request:', requestData);

        const response = await fetch(`${API_BASE_URL}${ENDPOINTS.generateStory}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        const data = await response.json();
        console.log('Received response:', data);
        
        if (!response.ok) {
            throw new Error(data.detail || data.message || 'Failed to generate story');
        }

        // Process the response
        currentStoryText = typeof data === 'string' ? data : 
                         data.story ? data.story :
                         data.content ? data.content :
                         data.text ? data.text : '';
        
        if (!currentStoryText) {
            throw new Error('No story content received');
        }

        // Clear any existing content first
        elements.storyText.textContent = '';
        elements.audioPlayer.classList.add('hidden');
        
        // Update the display with a slight delay to ensure proper animation
        setTimeout(() => {
            updateStoryDisplay(currentStoryText, true);
            showToast('Story generated successfully', 'success');
        }, 100);

    } catch (error) {
        console.error('Failed to generate story:', error);
        showFormError(error.message || 'Failed to generate story. Please try again.');
        updateStoryDisplay('', false);
    } finally {
        isGeneratingStory = false;
        setButtonLoading(elements.generateStoryBtn, false);
        hideLoading();
    }
}

// Generate audio with enhanced error handling
async function generateAudio() {
    const generateBtn = elements.generateAudioBtn;
    
    if (!currentStoryText) {
        showToast('Please generate a story first', 'error');
        return;
    }
    
    const languageCode = elements.languageSelect.value;
    const voice = elements.voiceSelect.value;
    const speed = elements.speedRange.value;
    const pitch = elements.pitchRange.value;
    
    if (!voice) {
        showToast('Please select a voice', 'error');
        return;
    }
    
    try {
        setButtonLoading(generateBtn, true);
        showLoading();
        
        const response = await fetch(`${API_BASE_URL}${ENDPOINTS.generateAudio}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: currentStoryText,
                voice: voice,
                language_code: languageCode,
                speaking_rate: parseFloat(speed),
                pitch: parseFloat(pitch)
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to generate audio');
        }
        
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        
        elements.storyAudio.src = audioUrl;
        elements.downloadLink.href = audioUrl;
        elements.downloadLink.classList.remove('hidden');
        elements.shareAudioBtn.classList.remove('hidden');
        elements.audioPlayer.classList.remove('hidden');
        
        showToast('Audio generated successfully', 'success');
    } catch (error) {
        console.error('Error generating audio:', error);
        showToast('Failed to generate audio', 'error');
    } finally {
        setButtonLoading(generateBtn, false);
        hideLoading();
    }
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
        
        // Get and validate focus areas
        const focus = Array.from(formData.getAll('focus'));
        if (focus.length === 0) {
            showFormError('Please select at least one focus area');
            return;
        }

        // Get other preferences
        const style = formData.get('style');
        const length = formData.get('length');

        // Validate all required fields
        if (!style || !length) {
            showFormError('Please fill in all required fields');
            return;
        }

        // Create preferences object
        const preferences = {
            style: style,
            focus: focus,
            length: length
        };

        console.log('Form preferences:', preferences);
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

    // Add language selection handler
    elements.languageSelect.addEventListener('change', (e) => {
        updateVoiceOptions(e.target.value);
    });
}

// Loading overlay
function showLoading() {
    elements.loadingOverlay.classList.remove('hidden');
}

function hideLoading() {
    elements.loadingOverlay.classList.add('hidden');
}

// Add cleanup on page unload
window.addEventListener('beforeunload', () => {
    clearTimeout(storyDisplayTimeout);
});

// Add these new functions
async function loadVoices(languageCode) {
    try {
        const response = await fetch(`${API_BASE_URL}${ENDPOINTS.voices}?language_code=${languageCode}`);
        if (!response.ok) {
            throw new Error('Failed to load voices');
        }
        const data = await response.json();
        return data.voices;
    } catch (error) {
        console.error('Error loading voices:', error);
        showToast('Failed to load voices', 'error');
        return [];
    }
}

async function updateVoiceOptions(languageCode) {
    const voiceSelect = elements.voiceSelect;
    voiceSelect.innerHTML = '<option value="">Loading voices...</option>';
    
    const voices = await loadVoices(languageCode);
    voiceSelect.innerHTML = '';
    
    if (voices.length === 0) {
        voiceSelect.innerHTML = '<option value="">No voices available</option>';
        return;
    }
    
    voices.forEach(voice => {
        const option = document.createElement('option');
        option.value = voice.name;
        // Format the display name to be more user-friendly
        const gender = voice.gender.toLowerCase();
        const voiceType = voice.name.includes('Neural') ? 'Neural' : 'Standard';
        option.textContent = `${gender} (${voiceType})`;
        voiceSelect.appendChild(option);
    });
    
    // Select the first voice by default
    if (voiceSelect.options.length > 0) {
        voiceSelect.selectedIndex = 0;
    }
}

// Initialize the app
document.addEventListener('DOMContentLoaded', init); 