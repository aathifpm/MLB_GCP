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
    languageSelect: document.getElementById('languageSelect'),
    previewVoiceBtn: document.getElementById('previewVoiceBtn'),
    tabButtons: document.querySelectorAll('.tab-btn'),
    tabContents: document.querySelectorAll('.tab-content'),
    speedValue: document.getElementById('speedValue'),
    pitchValue: document.getElementById('pitchValue'),
    gameSearch: document.getElementById('gameSearch'),
    dateChips: document.getElementById('dateChips'),
    dateNavPrev: document.querySelector('.date-nav.prev'),
    dateNavNext: document.querySelector('.date-nav.next'),
    statusChips: document.querySelectorAll('.chip[data-filter]'),
    sortChips: document.querySelectorAll('.chip[data-sort]'),
    pageNumbers: document.getElementById('pageNumbers'),
    prevPage: document.getElementById('prevPage'),
    nextPage: document.getElementById('nextPage')
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
    currentPage: 1,
    gamesPerPage: 9,
    currentFilter: 'all',
    currentSort: 'date-asc',
    searchQuery: '',
    selectedDate: null,
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
    // Store all games
    gameState.allGames = dates.reduce((acc, date) => {
        return acc.concat(date.games.map(game => ({
            ...game,
            dateObj: new Date(game.gameDate)
        })));
    }, []);

    // Render date chips
    renderDateChips(dates);
    
    // Apply initial filters and render
    filterAndRenderGames();
}

function renderDateChips(dates) {
    elements.dateChips.innerHTML = '';
    
    dates.forEach(date => {
        const dateObj = new Date(date.date);
        const chip = document.createElement('button');
        chip.className = 'date-chip';
        chip.dataset.date = date.date;
        chip.textContent = dateObj.toLocaleDateString('en-US', { 
            weekday: 'short', 
            month: 'short', 
            day: 'numeric' 
        });
        
        if (date.date === gameState.selectedDate) {
            chip.classList.add('active');
        }
        
        chip.addEventListener('click', () => {
            document.querySelectorAll('.date-chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            gameState.selectedDate = date.date;
            filterAndRenderGames();
        });
        
        elements.dateChips.appendChild(chip);
    });
}

function filterAndRenderGames() {
    // Apply filters
    let filtered = gameState.allGames;
    
    // Date filter
    if (gameState.selectedDate) {
        filtered = filtered.filter(game => {
            const gameDate = new Date(game.gameDate).toLocaleDateString();
            const selectedDate = new Date(gameState.selectedDate).toLocaleDateString();
            return gameDate === selectedDate;
        });
    }
    
    // Status filter
    if (gameState.currentFilter !== 'all') {
        filtered = filtered.filter(game => {
            const status = game.status.detailedState.toLowerCase();
            switch (gameState.currentFilter) {
                case 'upcoming':
                    return status.includes('scheduled') || status.includes('pre-game');
                case 'live':
                    return status.includes('in progress') || status.includes('delayed');
                case 'final':
                    return status.includes('final');
                default:
                    return true;
            }
        });
    }
    
    // Search filter
    if (gameState.searchQuery) {
        const query = gameState.searchQuery.toLowerCase();
        filtered = filtered.filter(game => 
            game.teams.home.team.name.toLowerCase().includes(query) ||
            game.teams.away.team.name.toLowerCase().includes(query)
        );
    }
    
    // Sort
    filtered.sort((a, b) => {
        switch (gameState.currentSort) {
            case 'date-asc':
                return a.dateObj - b.dateObj;
            case 'date-desc':
                return b.dateObj - a.dateObj;
            case 'team':
                return a.teams.home.team.name.localeCompare(b.teams.home.team.name);
            default:
                return 0;
        }
    });
    
    gameState.filteredGames = filtered;
    renderGameCards();
    renderPagination();
}

function renderGameCards() {
    elements.gamesList.innerHTML = '';
    
    const startIndex = (gameState.currentPage - 1) * gameState.gamesPerPage;
    const endIndex = startIndex + gameState.gamesPerPage;
    const gamesToShow = gameState.filteredGames.slice(startIndex, endIndex);
    
    if (gamesToShow.length === 0) {
        elements.gamesList.innerHTML = `
            <div class="no-games">
                <i class="fas fa-search"></i>
                <p>No games found matching your criteria</p>
            </div>
        `;
        return;
    }
    
    gamesToShow.forEach(game => {
        const card = document.createElement('div');
        card.className = 'game-card';
        card.dataset.gameId = game.gamePk;
        
        const status = game.status.detailedState.toLowerCase();
        let statusClass = 'upcoming';
        if (status.includes('in progress') || status.includes('delayed')) {
            statusClass = 'live';
        } else if (status.includes('final')) {
            statusClass = 'final';
        }
        
        const homeTeam = game.teams.home.team;
        const awayTeam = game.teams.away.team;
        const gameTime = new Date(game.gameDate);
        
        card.innerHTML = `
            <div class="game-status ${statusClass}">${game.status.detailedState}</div>
            <div class="game-teams">
                <div class="team-info">
                    <div class="team-name">${awayTeam.name}</div>
                    <div class="team-record">${game.teams.away.leagueRecord?.wins || 0}-${game.teams.away.leagueRecord?.losses || 0}</div>
                </div>
                <div class="vs-divider">VS</div>
                <div class="team-info">
                    <div class="team-name">${homeTeam.name}</div>
                    <div class="team-record">${game.teams.home.leagueRecord?.wins || 0}-${game.teams.home.leagueRecord?.losses || 0}</div>
                </div>
            </div>
            <div class="game-details">
                <div class="game-info">
                    <i class="far fa-calendar"></i>
                    ${gameTime.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                </div>
                <div class="game-info">
                    <i class="far fa-clock"></i>
                    ${gameTime.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}
                </div>
                <div class="game-info">
                    <i class="fas fa-map-marker-alt"></i>
                    ${game.venue?.name || 'TBD'}
                </div>
            </div>
        `;
        
        card.addEventListener('click', () => {
            if (!gameState.isModalOpen) {
                showGameStatsModal(game);
            }
        });
        elements.gamesList.appendChild(card);
    });
}

function renderPagination() {
    const totalPages = Math.ceil(gameState.filteredGames.length / gameState.gamesPerPage);
    elements.pageNumbers.innerHTML = '';
    elements.prevPage.disabled = gameState.currentPage === 1;
    elements.nextPage.disabled = gameState.currentPage === totalPages;

    // Helper function to create page button
    const createPageButton = (pageNum, isActive = false, isEllipsis = false) => {
        const button = document.createElement('button');
        button.className = `page-number ${isActive ? 'active' : ''} ${isEllipsis ? 'ellipsis' : ''}`;
        button.textContent = isEllipsis ? '...' : pageNum;
        
        if (!isEllipsis) {
            button.addEventListener('click', () => {
                gameState.currentPage = pageNum;
                renderGameCards();
                renderPagination();
            });
        }
        
        return button;
    };

    // Always show first page
    elements.pageNumbers.appendChild(createPageButton(1, gameState.currentPage === 1));

    // Calculate range of pages to show
    let startPage = Math.max(2, gameState.currentPage - 3);
    let endPage = Math.min(totalPages - 1, gameState.currentPage + 3);

    // Add ellipsis after first page if needed
    if (startPage > 2) {
        elements.pageNumbers.appendChild(createPageButton(null, false, true));
    }

    // Add pages within range
    for (let i = startPage; i <= endPage; i++) {
        elements.pageNumbers.appendChild(createPageButton(i, gameState.currentPage === i));
    }

    // Add ellipsis before last page if needed
    if (endPage < totalPages - 1) {
        elements.pageNumbers.appendChild(createPageButton(null, false, true));
    }

    // Always show last page if there is more than one page
    if (totalPages > 1) {
        elements.pageNumbers.appendChild(createPageButton(totalPages, gameState.currentPage === totalPages));
    }
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

    elements.previewVoiceBtn.addEventListener('click', previewVoice);
    
    // Setup tabs and range inputs
    setupTabs();
    setupRangeInputs();

    // Game search
    elements.gameSearch.addEventListener('input', debounce(() => {
        gameState.searchQuery = elements.gameSearch.value;
        gameState.currentPage = 1;
        filterAndRenderGames();
    }, 300));
    
    // Status filter chips
    elements.statusChips.forEach(chip => {
        chip.addEventListener('click', () => {
            elements.statusChips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            gameState.currentFilter = chip.dataset.filter;
            gameState.currentPage = 1;
            filterAndRenderGames();
        });
    });
    
    // Sort chips
    elements.sortChips.forEach(chip => {
        chip.addEventListener('click', () => {
            elements.sortChips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            gameState.currentSort = chip.dataset.sort;
            filterAndRenderGames();
        });
    });
    
    // Date navigation
    elements.dateNavPrev.addEventListener('click', () => {
        const chips = Array.from(elements.dateChips.children);
        const activeIndex = chips.findIndex(chip => chip.classList.contains('active'));
        if (activeIndex > 0) {
            chips[activeIndex - 1].click();
            chips[activeIndex - 1].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    });
    
    elements.dateNavNext.addEventListener('click', () => {
        const chips = Array.from(elements.dateChips.children);
        const activeIndex = chips.findIndex(chip => chip.classList.contains('active'));
        if (activeIndex < chips.length - 1) {
            chips[activeIndex + 1].click();
            chips[activeIndex + 1].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    });
    
    // Pagination
    elements.prevPage.addEventListener('click', () => {
        if (gameState.currentPage > 1) {
            gameState.currentPage--;
            filterAndRenderGames();
        }
    });
    
    elements.nextPage.addEventListener('click', () => {
        const totalPages = Math.ceil(gameState.filteredGames.length / gameState.gamesPerPage);
        if (gameState.currentPage < totalPages) {
            gameState.currentPage++;
            filterAndRenderGames();
        }
    });

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

// Add modal handling functions
function showStoryPreferences() {
    // Get the story preferences section
    const preferencesSection = document.getElementById('storyPreferences');
    
    // Show the section
    preferencesSection.classList.remove('hidden');
    
    // Scroll to the section smoothly
    preferencesSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    // Update UI state
    selectedGameId = gameState.selectedGame.gamePk;
    
    // Reset any previous story
    updateStoryDisplay('', false);
}

async function showGameStatsModal(game) {
    try {
        showLoadingOverlay();
        
        // Store selected game in state
        gameState.selectedGame = game;
        
        // Fetch game data and highlights
        const [gameData, highlights, homeRuns] = await Promise.all([
            fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.GAME_FEED}/${game.gamePk}/feed`).then(res => res.json()),
            fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.GAME_FEED}/${game.gamePk}/highlights`).then(res => res.json()),
            fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.HOME_RUNS}/${new Date(game.gameDate).getFullYear()}`).then(res => res.json())
        ]);
        
        // Filter home runs for this game
        const gameHomeRuns = homeRuns.filter(hr => hr.play_id.toString() === game.gamePk.toString());
        
        // Update modal with all data
        updateGameStatsModal(gameData, highlights, gameHomeRuns);
        
        // Show modal
        const modal = document.getElementById('gameStatsModal');
        modal.classList.remove('hidden');
        modal.classList.add('show');
        document.body.classList.add('modal-open');
        gameState.isModalOpen = true;
        
    } catch (error) {
        console.error('Error showing game stats:', error);
        showToast('Failed to load game statistics', 'error');
    } finally {
        hideLoadingOverlay();
    }
}

function hideGameStatsModal() {
    const modal = document.getElementById('gameStatsModal');
    modal.classList.remove('show');
    setTimeout(() => {
        modal.classList.add('hidden');
        document.body.classList.remove('modal-open');
        gameState.isModalOpen = false;
    }, 300);
}

function updateGameStatsModal(gameData, highlights, homeRuns = []) {
    const modal = document.getElementById('gameStatsModal');
    if (!modal) return;
    
    // Get teams data
    const teams = gameData.gameData?.teams || {};
    const homeTeam = teams.home || {};
    const awayTeam = teams.away || {};
    
    // Get linescore for current game state
    const linescore = gameData.liveData?.linescore || {};
    const homeScore = linescore.teams?.home?.runs || 0;
    const awayScore = linescore.teams?.away?.runs || 0;
    
    // Get boxscore for detailed stats
    const boxscore = gameData.liveData?.boxscore?.teams || {};
    const homeStats = boxscore.home?.teamStats?.batting || {};
    const awayStats = boxscore.away?.teamStats?.batting || {};
    
    // Get game info
    const status = gameData.gameData?.status?.detailedState || 'Scheduled';
    const venue = gameData.gameData?.venue?.name || 'TBD';
    const gameDate = gameData.gameData?.datetime?.dateTime || new Date().toISOString();
    
    modal.querySelector('.game-summary').innerHTML = `
        <div class="team-matchup">
            <div class="team home">
                <img src="https://www.mlbstatic.com/team-logos/${homeTeam.id}.svg" 
                     alt="${homeTeam.name} logo" 
                     class="team-logo"
                     onerror="this.src='${STATIC_ASSETS.DEFAULT_TEAM_LOGO}'">
                <h3>${homeTeam.name || 'Home Team'}</h3>
                <p class="score">${homeScore}</p>
            </div>
            <div class="vs">VS</div>
            <div class="team away">
                <img src="https://www.mlbstatic.com/team-logos/${awayTeam.id}.svg" 
                     alt="${awayTeam.name} logo" 
                     class="team-logo"
                     onerror="this.src='${STATIC_ASSETS.DEFAULT_TEAM_LOGO}'">
                <h3>${awayTeam.name || 'Away Team'}</h3>
                <p class="score">${awayScore}</p>
            </div>
        </div>
        <div class="game-info">
            <p><i class="fas fa-calendar"></i> ${new Date(gameDate).toLocaleDateString()}</p>
            <p><i class="fas fa-map-marker-alt"></i> ${venue}</p>
            <p><i class="fas fa-clock"></i> ${status}</p>
        </div>
    `;
    
    // Update highlights section
    const highlightsContainer = modal.querySelector('.highlights-section');
    if (highlights && highlights.length > 0) {
        highlightsContainer.innerHTML = `
            <h3><i class="fas fa-play-circle"></i> Game Highlights</h3>
            <div class="highlights-grid">
                ${highlights.map(highlight => {
                    // Get the best quality video URL
                    const videoUrl = highlight.playbacks?.find(p => p.name === 'mp4Avc')?.url || '';
                    return `
                        <div class="highlight-card">
                            <div class="highlight-video" data-video-url="${videoUrl}">
                                <img src="${highlight.thumbnail || ''}" alt="${highlight.title}">
                                <div class="play-button">
                                    <i class="fas fa-play"></i>
                                </div>
                                ${highlight.duration ? `<span class="duration">${highlight.duration}</span>` : ''}
                            </div>
                            <div class="highlight-info">
                                <h4>${highlight.title}</h4>
                                <p>${highlight.description || ''}</p>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;

        // Add click handlers for video playback
        highlightsContainer.querySelectorAll('.highlight-video').forEach(video => {
            video.addEventListener('click', () => {
                const videoUrl = video.dataset.videoUrl;
                if (videoUrl) {
                    showVideoPlayer(videoUrl);
                }
            });
        });
    } else {
        highlightsContainer.innerHTML = '<p>No highlights available</p>';
    }
    
    // Update home runs section
    const homeRunsContainer = modal.querySelector('.home-runs-section');
    if (homeRuns && homeRuns.length > 0) {
        homeRunsContainer.innerHTML = `
            <h3><i class="fas fa-baseball-ball"></i> Home Runs</h3>
            <div class="home-runs-grid">
                ${homeRuns.map(hr => `
                    <div class="home-run-card">
                        <div class="hr-details">
                            <h4>${hr.title || 'Home Run'}</h4>
                            <div class="hr-stats">
                                ${hr.ExitVelocity ? `<span><i class="fas fa-bolt"></i> Exit Velocity: ${hr.ExitVelocity} mph</span>` : ''}
                                ${hr.LaunchAngle ? `<span><i class="fas fa-angle-up"></i> Launch Angle: ${hr.LaunchAngle}°</span>` : ''}
                                ${hr.HitDistance ? `<span><i class="fas fa-ruler-horizontal"></i> Distance: ${hr.HitDistance} ft</span>` : ''}
                            </div>
                        </div>
                        ${hr.video ? `
                            <div class="hr-video">
                                <button class="btn btn-primary" onclick="showVideoPlayer('${hr.video}')">
                                    <i class="fas fa-play"></i> Watch Video
                                </button>
                            </div>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
        `;
    } else {
        homeRunsContainer.innerHTML = '<p>No home runs in this game</p>';
    }
    
    // Get batting stats
    const homeBatting = boxscore.home?.teamStats?.batting || {};
    const awayBatting = boxscore.away?.teamStats?.batting || {};
    
    // Update game stats section with detailed batting stats
    const statsContainer = modal.querySelector('.game-stats-section');
    statsContainer.innerHTML = `
        <h3><i class="fas fa-chart-bar"></i> Team Statistics</h3>
        <div class="stats-grid">
            <div class="stat-column">
                <h4>${homeTeam.name || 'Home Team'}</h4>
                <div class="stat-row">
                    <span>Hits</span>
                    <span>${homeBatting.hits || 0}</span>
                </div>
                <div class="stat-row">
                    <span>Runs</span>
                    <span>${homeScore}</span>
                </div>
                <div class="stat-row">
                    <span>Home Runs</span>
                    <span>${homeBatting.homeRuns || 0}</span>
                </div>
                <div class="stat-row">
                    <span>Batting Avg</span>
                    <span>${homeBatting.avg || '.000'}</span>
                </div>
                <div class="stat-row">
                    <span>RBI</span>
                    <span>${homeBatting.rbi || 0}</span>
                </div>
                <div class="stat-row">
                    <span>Strikeouts</span>
                    <span>${homeBatting.strikeOuts || 0}</span>
                </div>
            </div>
            <div class="stat-column">
                <h4>${awayTeam.name || 'Away Team'}</h4>
                <div class="stat-row">
                    <span>Hits</span>
                    <span>${awayBatting.hits || 0}</span>
                </div>
                <div class="stat-row">
                    <span>Runs</span>
                    <span>${awayScore}</span>
                </div>
                <div class="stat-row">
                    <span>Home Runs</span>
                    <span>${awayBatting.homeRuns || 0}</span>
                </div>
                <div class="stat-row">
                    <span>Batting Avg</span>
                    <span>${awayBatting.avg || '.000'}</span>
                </div>
                <div class="stat-row">
                    <span>RBI</span>
                    <span>${awayBatting.rbi || 0}</span>
                </div>
                <div class="stat-row">
                    <span>Strikeouts</span>
                    <span>${awayBatting.strikeOuts || 0}</span>
                </div>
            </div>
        </div>
    `;
}

function getOrdinalSuffix(num) {
    const j = num % 10;
    const k = num % 100;
    if (j == 1 && k != 11) return "st";
    if (j == 2 && k != 12) return "nd";
    if (j == 3 && k != 13) return "rd";
    return "th";
}

// Add these loading overlay functions
function showLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    overlay.classList.remove('hidden');
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    overlay.classList.add('hidden');
}

// Add video player modal to the DOM
document.body.insertAdjacentHTML('beforeend', `
    <div class="video-player-modal" id="videoPlayerModal">
        <div class="video-container">
            <video id="highlightVideo" controls></video>
            <button class="close-video" onclick="hideVideoPlayer()">
                <i class="fas fa-times"></i>
            </button>
        </div>
    </div>
`);

function showVideoPlayer(videoUrl) {
    const modal = document.getElementById('videoPlayerModal');
    const video = document.getElementById('highlightVideo');
    
    // Set video source and load it
    video.src = videoUrl;
    video.load();
    
    // Show modal
    modal.classList.add('show');
    
    // Play video
    video.play().catch(e => console.log('Auto-play prevented:', e));
    
    // Add event listener to pause video when modal is closed
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            hideVideoPlayer();
        }
    });
}

function hideVideoPlayer() {
    const modal = document.getElementById('videoPlayerModal');
    const video = document.getElementById('highlightVideo');
    
    // Pause and reset video
    video.pause();
    video.currentTime = 0;
    
    // Hide modal
    modal.classList.remove('show');
}

// Initialize the app
document.addEventListener('DOMContentLoaded', init); 