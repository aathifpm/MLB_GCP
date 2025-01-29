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
    formErrorMessage: document.getElementById('formError')?.querySelector('.error-message'),
    languageSelect: document.getElementById('languageSelect'),
    previewVoiceBtn: document.getElementById('previewVoiceBtn'),
    tabButtons: document.querySelectorAll('.tab-btn'),
    tabContents: document.querySelectorAll('.tab-content'),
    speedValue: document.getElementById('speedValue'),
    pitchValue: document.getElementById('pitchValue'),
    gameSearch: document.getElementById('gameSearch'),
    sliderPrev: document.querySelector('.slider-nav.prev'),
    sliderNext: document.querySelector('.slider-nav.next'),
    statusChips: document.querySelectorAll('.chip[data-filter]'),
    sortChips: document.querySelectorAll('.chip[data-sort]')
};

// State
let selectedGameId = null;
let currentStoryText = '';
let lastScrollTop = 0;
let isGeneratingStory = false;
let storyDisplayTimeout = null;

// Add game listing state
const gameState = {
    allGames: [],
    filteredGames: [],
    currentFilter: 'all',
    currentSort: 'date-asc',
    searchQuery: '',
    selectedGame: null,
    isModalOpen: false
};

// Update API configuration
const API_CONFIG = {
    BASE_URL: 'http://localhost:8000',
    ENDPOINTS: {
        GAME_FEED: '/api/games',
        GAME_CONTENT: '/api/games',
        TEAMS: '/api/teams',
        PLAYERS: '/api/players',
        HOME_RUNS: '/api/home-runs'
    }
};

// Add static assets configuration
const STATIC_ASSETS = {
    DEFAULT_TEAM_LOGO: `${API_CONFIG.BASE_URL}/static/images/default-team.png`,
    DEFAULT_PLAYER_PHOTO: `${API_CONFIG.BASE_URL}/static/images/default-player.png`
};

// Initialize the application
async function init() {
    await checkHealth();
    await loadGames();
    await updateVoiceOptions('en-US');
    setupEventListeners();
    setupScrollHandlers();
    setupRangeInputs();
    initializePreferencesForm();
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
        
        // Add minimal delay to ensure smooth transition
        await new Promise(resolve => setTimeout(resolve, 300)); // Reduced from default timing
        
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
    // Store all games
    gameState.allGames = dates.reduce((acc, date) => {
        return acc.concat(date.games.map(game => ({
            ...game,
            dateObj: new Date(game.gameDate)
        })));
    }, []);
    
    // Apply initial filters and render
    filterAndRenderGames();
}

function filterAndRenderGames() {
    // Apply filters
    gameState.filteredGames = gameState.allGames.filter(game => {
        const status = game.status.detailedState.toLowerCase();
        const matchesFilter = gameState.currentFilter === 'all' || 
            (gameState.currentFilter === 'upcoming' && (status.includes('scheduled') || status.includes('pre-game'))) ||
            (gameState.currentFilter === 'live' && (status.includes('in progress') || status.includes('delayed'))) ||
            (gameState.currentFilter === 'final' && status.includes('final'));
            
        const matchesSearch = !gameState.searchQuery || 
            game.teams.away.team.name.toLowerCase().includes(gameState.searchQuery.toLowerCase()) ||
            game.teams.home.team.name.toLowerCase().includes(gameState.searchQuery.toLowerCase());
        return matchesFilter && matchesSearch;
    });

    // Apply sorting
    gameState.filteredGames.sort((a, b) => {
        switch (gameState.currentSort) {
            case 'date-asc':
                return a.dateObj - b.dateObj;
            case 'date-desc':
                return b.dateObj - a.dateObj;
            case 'team':
                return a.teams.away.team.name.localeCompare(b.teams.away.team.name);
            default:
                return 0;
        }
    });
    
    renderGameCards();
}

function renderGameCards() {
    elements.gamesList.innerHTML = '';
    
    gameState.filteredGames.forEach(game => {
        const card = document.createElement('div');
        card.className = 'game-card';
        card.dataset.gameId = game.gamePk;
        
        // Determine game status and class
        const status = game.status.detailedState.toLowerCase();
        let statusClass = 'upcoming';
        if (status.includes('in progress') || status.includes('delayed')) {
            statusClass = 'live';
        } else if (status.includes('final')) {
            statusClass = 'final';
        }
        
        const statusDiv = document.createElement('div');
        statusDiv.className = `game-status ${statusClass}`;
        statusDiv.textContent = game.status.detailedState;
        
        const teams = document.createElement('div');
        teams.className = 'game-teams';
        teams.innerHTML = `
                <div class="team-info">
                <div class="team-name">${game.teams.away.team.name}</div>
                <div class="team-record">${game.teams.away.leagueRecord.wins}-${game.teams.away.leagueRecord.losses}</div>
                <div class="game-score">${game.teams.away.score || '-'}</div>
                </div>
                <div class="vs-divider">VS</div>
                <div class="team-info">
                <div class="team-name">${game.teams.home.team.name}</div>
                <div class="team-record">${game.teams.home.leagueRecord.wins}-${game.teams.home.leagueRecord.losses}</div>
                <div class="game-score">${game.teams.home.score || '-'}</div>
                    </div>
        `;
        
        const details = document.createElement('div');
        details.className = 'game-details';
        details.innerHTML = `
                <div class="game-info">
                <i class="fas fa-calendar"></i>
                ${new Date(game.gameDate).toLocaleDateString()}
                </div>
                <div class="game-info">
                <i class="fas fa-clock"></i>
                ${new Date(game.gameDate).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
        `;
        
        card.appendChild(statusDiv);
        card.appendChild(teams);
        card.appendChild(details);
        
        card.addEventListener('click', () => selectGame(game.gamePk, card));
        elements.gamesList.appendChild(card);
    });

    // Setup slider navigation
    setupSliderNavigation();
}

function setupSliderNavigation() {
    const slider = elements.gamesList;
    const scrollAmount = 300; // Width of one card

    elements.sliderPrev?.addEventListener('click', () => {
        slider.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
    });

    elements.sliderNext?.addEventListener('click', () => {
        slider.scrollBy({ left: scrollAmount, behavior: 'smooth' });
    });

    // Update navigation buttons visibility
    const updateNavButtons = () => {
        if (elements.sliderPrev && elements.sliderNext) {
            elements.sliderPrev.style.display = slider.scrollLeft > 0 ? 'flex' : 'none';
            elements.sliderNext.style.display = 
                slider.scrollLeft < (slider.scrollWidth - slider.clientWidth) ? 'flex' : 'none';
        }
    };

    slider.addEventListener('scroll', updateNavButtons);
    window.addEventListener('resize', updateNavButtons);
    updateNavButtons();
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
    
    // Find the selected game data
    const selectedGame = gameState.filteredGames.find(game => game.gamePk === gameId);
    if (selectedGame) {
        // Store selected game in state
        gameState.selectedGame = selectedGame;
        // Directly show story preferences
        showStoryPreferences();
    }
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
async function generateStory(event) {
    event.preventDefault();
    
    if (isGeneratingStory) {
        showToast('Story generation in progress...', 'info');
        return;
    }

    if (!gameState.selectedGame) {
        showFormError('Please select a game first');
        return;
    }

    // Get all form data
    const form = document.getElementById('preferencesForm');
    const formData = new FormData(form);
    
    // Get checked focus areas
    const focusAreas = Array.from(form.querySelectorAll('input[name="focus"]:checked')).map(cb => cb.value);
    
    if (focusAreas.length === 0) {
        showFormError('Please select at least one focus area');
        return;
    }

    // Get additional options
    const includePlayerStats = form.querySelector('input[name="include_player_stats"]').checked;
    const highlightKeyMoments = form.querySelector('input[name="highlight_key_moments"]').checked;
    
    const preferences = {
        style: formData.get('style'),
        focus: focusAreas,
        length: formData.get('length'),
        include_player_stats: includePlayerStats,
        highlight_key_moments: highlightKeyMoments
    };
    
    isGeneratingStory = true;
    hideFormError();
    setButtonLoading(elements.generateStoryBtn, true);
    showLoading();

    try {
        const requestData = {
            game_id: String(gameState.selectedGame.gamePk),
            preferences: {
                style: preferences.style || 'dramatic',
                focus_areas: preferences.focus,
                story_length: preferences.length || 'medium',
                include_player_stats: preferences.include_player_stats,
                highlight_key_moments: preferences.highlight_key_moments,
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
        await new Promise(resolve => setTimeout(resolve, 400));
        updateStoryDisplay(currentStoryText, true);
        showToast('Story generated successfully', 'success');

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

// Initialize form with default values
function initializePreferencesForm() {
    const form = document.getElementById('preferencesForm');
    
    // Set default values for dropdowns
    form.querySelector('#storyStyle').value = 'dramatic';
    form.querySelector('#storyLength').value = 'medium';
    
    // Set default checked state for checkboxes
    const defaultFocusAreas = ['key_plays', 'player_performances', 'game_flow'];
    defaultFocusAreas.forEach(area => {
        const checkbox = form.querySelector(`input[name="focus"][value="${area}"]`);
        if (checkbox) checkbox.checked = true;
    });
    
    // Set default checked state for additional options
    form.querySelector('input[name="include_player_stats"]').checked = true;
    form.querySelector('input[name="highlight_key_moments"]').checked = true;
    
    // Add form submit handler
    form.addEventListener('submit', generateStory);
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
        
        // Add minimal delay for smooth transition
        await new Promise(resolve => setTimeout(resolve, 350)); // Reduced from default timing
        
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

// Add tab switching functionality
function setupTabs() {
    elements.tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.dataset.tab;
            
            // Update active tab button
            elements.tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Show selected tab content
            elements.tabContents.forEach(content => {
                if (content.id === `${tabName}Tab`) {
                    content.classList.remove('hidden');
                } else {
                    content.classList.add('hidden');
                }
            });
        });
    });
}

// Update range input display values
function setupRangeInputs() {
    const updateRangeValue = (input, valueDisplay) => {
        const value = input.value;
        valueDisplay.textContent = input.id === 'speedRange' ? `${value}x` : value;
    };

    // Speed range
    elements.speedRange.addEventListener('input', () => {
        updateRangeValue(elements.speedRange, elements.speedValue);
    });

    // Pitch range
    elements.pitchRange.addEventListener('input', () => {
        updateRangeValue(elements.pitchRange, elements.pitchValue);
    });
}

// Add voice preview functionality
async function previewVoice() {
    const voice = elements.voiceSelect.value;
    if (!voice) {
        showToast('Please select a voice first', 'error');
        return;
    }

    const languageCode = elements.languageSelect.value;
    const previewText = getPreviewText(languageCode);
    const speed = elements.speedRange.value;
    const pitch = elements.pitchRange.value;

    try {
        setButtonLoading(elements.previewVoiceBtn, true);
        
        const response = await fetch(`${API_BASE_URL}${ENDPOINTS.generateAudio}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: previewText,
                voice: voice,
                language_code: languageCode,
                speaking_rate: parseFloat(speed),
                pitch: parseFloat(pitch)
            })
        });

        if (!response.ok) {
            throw new Error('Failed to generate preview');
        }

        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        
        const previewAudio = new Audio(audioUrl);
        await previewAudio.play();
        
        showToast('Playing voice preview', 'success');
    } catch (error) {
        console.error('Error previewing voice:', error);
        showToast('Failed to preview voice', 'error');
    } finally {
        setButtonLoading(elements.previewVoiceBtn, false);
    }
}

// Setup event listeners with enhanced interaction handling
function setupEventListeners() {
    // Season and game type change handlers
    elements.seasonSelect?.addEventListener('change', loadGames);
    elements.gameTypeSelect?.addEventListener('change', loadGames);
    
    // Game status filter handlers
    elements.statusChips?.forEach(chip => {
        chip.addEventListener('click', () => {
            elements.statusChips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            gameState.currentFilter = chip.dataset.filter;
            filterAndRenderGames();
        });
    });
    
    // Sort handlers
    elements.sortChips?.forEach(chip => {
        chip.addEventListener('click', () => {
            elements.sortChips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            gameState.currentSort = chip.dataset.sort;
            filterAndRenderGames();
        });
    });
    
    // Search handler
    elements.gameSearch?.addEventListener('input', debounce(() => {
        gameState.searchQuery = elements.gameSearch.value.trim().toLowerCase();
        filterAndRenderGames();
    }, 300));
    
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
        await generateStory(e);
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

    elements.previewVoiceBtn.addEventListener('click', previewVoice);
    
    // Setup tabs and range inputs
    setupTabs();
    setupRangeInputs();

    // Add modal close handlers
    document.querySelector('.close-modal').addEventListener('click', hideGameStatsModal);
    
    document.getElementById('gameStatsModal').addEventListener('click', (e) => {
        if (e.target.id === 'gameStatsModal') {
            hideGameStatsModal();
        }
    });
    
    // Add continue to story button in modal
    const continueBtn = document.createElement('button');
    continueBtn.className = 'btn btn-primary continue-to-story';
    continueBtn.innerHTML = '<i class="fas fa-pen"></i> Continue to Story Creation';
    continueBtn.addEventListener('click', () => {
        hideGameStatsModal();
        showStoryPreferences();
    });
    
    document.querySelector('.modal-body').appendChild(continueBtn);
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

    // Sort voices by type (Neural2 > Studio > WaveNet > Standard)
    const sortedVoices = voices.sort((a, b) => {
        const getVoiceTypeScore = (name) => {
            if (name.includes('Neural2')) return 4;
            if (name.includes('Studio')) return 3;
            if (name.includes('Wavenet')) return 2;
            return 1; // Standard
        };
        return getVoiceTypeScore(b.name) - getVoiceTypeScore(a.name);
    });

    // Group voices by type
    const voiceGroups = {
        neural2: [],
        studio: [],
        wavenet: [],
        standard: []
    };

    sortedVoices.forEach(voice => {
        const name = voice.name;
        if (name.includes('Neural2')) {
            voiceGroups.neural2.push(voice);
        } else if (name.includes('Studio')) {
            voiceGroups.studio.push(voice);
        } else if (name.includes('Wavenet')) {
            voiceGroups.wavenet.push(voice);
        } else {
            voiceGroups.standard.push(voice);
        }
    });

    // Function to format voice display name
    const formatVoiceName = (voice, type) => {
        const gender = voice.gender.toLowerCase();
        const genderLabel = gender === 'female' ? '👩 Female' : '👨 Male';
        const languageCode = voice.language_codes[0];
        let accent = '';
        
        // Add accent/region information
        if (languageCode === 'en-US') accent = 'American';
        else if (languageCode === 'en-GB') accent = 'British';
        else if (languageCode === 'en-AU') accent = 'Australian';
        else if (languageCode === 'es-ES') accent = 'Spain';
        else if (languageCode === 'es-US') accent = 'Latin American';
        else if (languageCode === 'ja-JP') accent = 'Japanese';

        let quality = '';
        switch (type) {
            case 'neural2':
                quality = '🎯 Neural2 (Best Quality)';
                break;
            case 'studio':
                quality = '🎨 Studio (Professional)';
                break;
            case 'wavenet':
                quality = '🌊 WaveNet (Enhanced)';
                break;
            default:
                quality = '📱 Standard';
        }

        return `${genderLabel} - ${accent} ${quality}`;
    };

    // Add optgroups for each voice type
    const addVoiceGroup = (voices, type, label) => {
        if (voices.length === 0) return;
        
        const optgroup = document.createElement('optgroup');
        optgroup.label = label;
        
        voices.forEach(voice => {
            const option = document.createElement('option');
            option.value = voice.name;
            option.textContent = formatVoiceName(voice, type);
            optgroup.appendChild(option);
        });
        
        voiceSelect.appendChild(optgroup);
    };

    // Add voices in order of quality
    addVoiceGroup(voiceGroups.neural2, 'neural2', '🌟 Premium Neural Voices');
    addVoiceGroup(voiceGroups.studio, 'studio', '🎭 Studio Voices');
    addVoiceGroup(voiceGroups.wavenet, 'wavenet', '🎵 Enhanced WaveNet Voices');
    addVoiceGroup(voiceGroups.standard, 'standard', '📱 Standard Voices');

    // Select the first Neural2 or Studio voice by default
    if (voiceGroups.neural2.length > 0) {
        voiceSelect.value = voiceGroups.neural2[0].name;
    } else if (voiceGroups.studio.length > 0) {
        voiceSelect.value = voiceGroups.studio[0].name;
    } else if (voiceSelect.options.length > 0) {
        voiceSelect.selectedIndex = 0;
    }
}

// Update the preview text based on language
function getPreviewText(languageCode) {
    const previews = {
        'en-US': "Hello! This is how I will narrate your baseball story.",
        'en-GB': "Hello! This is how I will narrate your baseball story.",
        'es-ES': "¡Hola! Así es como narraré tu historia de béisbol.",
        'es-US': "¡Hola! Así es como narraré tu historia de béisbol.",
        'ja-JP': "こんにちは！野球の物語をこのように語ります。"
    };
    return previews[languageCode] || previews['en-US'];
}

// Utility function for debouncing
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Update showStoryPreferences to handle the transition smoothly
function showStoryPreferences() {
    // Get the story preferences section
    const preferencesSection = document.getElementById('storyPreferences');
    
    // Show the section
    preferencesSection.classList.remove('hidden');
    
    // Scroll to the section smoothly
    preferencesSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    // Reset any previous story
    updateStoryDisplay('', false);
}

// Remove unused functions and elements
const gameStatsModal = document.getElementById('gameStatsModal');
if (gameStatsModal) {
    gameStatsModal.remove();
}

const videoPlayerModal = document.getElementById('videoPlayerModal');
if (videoPlayerModal) {
    videoPlayerModal.remove();
}

// Initialize the app
document.addEventListener('DOMContentLoaded', init); 