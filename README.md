# Statsaga (MLB Storyteller)

A modern, AI-powered baseball storytelling platform that transforms MLB game data into engaging narratives using Google's Gemini AI.

![Statsaga Logo](frontend/static/images/favicon.ico)
live demo: https://aathifpm.github.io/MLB_GCP/

## 🌟 Features

### Core Features
- **Dynamic Story Generation**: AI-powered narratives of MLB games using Gemini
- **Interactive Quizzes**: Auto-generated game-specific questions and trivia
- **Personalization**: Custom stories based on favorite teams and players
- **Real-time Data**: Live integration with MLB Stats API
- **Multiple Narrative Styles**: Choose from dramatic, analytical, or casual storytelling

### Interactive Quiz Experience
- **Engaging Game-Specific Questions**: Each quiz is uniquely generated based on the selected game
- **Dynamic Loading Experience**: 
  - Animated baseball spinner during quiz generation
  - Rotating baseball facts to keep users engaged while waiting
  - Smooth transitions and loading states
- **Interactive UI Elements**:
  - Real-time score tracking with animated display
  - Immediate feedback on answer selection
  - Visual cues for correct/incorrect answers
  - Detailed explanations for each answer
- **Responsive Design**:
  - Beautiful gradient effects and animations
  - Mobile-friendly interface
  - Smooth animations and transitions
  - Progress indicators and visual feedback

### User Experience
- Modern, responsive web interface
- Advanced search and filtering capabilities
- Season and game type selection
- Seamless navigation and story browsing
- Progress indicators and loading states

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 14+
- Docker and Docker Compose (optional)
- MongoDB
- Redis

### Environment Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/MLB_GCP.git
   cd MLB_GCP
   ```

2. Create and configure environment variables:
   ```bash
   cp .env.template .env
   # Edit .env with your configuration
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

#### Using Docker (Recommended)
```bash
# Start all services
docker-compose up -d

# For development with hot-reload
docker-compose -f docker-compose.test.yml up -d
```

#### Manual Setup
1. Start the backend server:
   ```bash
   python -m uvicorn mlb_storyteller.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. Access the application:
   ```
   http://localhost:8000
   ```

## 🏗 Project Structure
```
MLB_GCP/
├── frontend/                # Frontend assets and templates
│   ├── static/             # Static assets (CSS, JS, images)
│   └── templates/          # HTML templates
├── mlb_storyteller/        # Core application
│   ├── api/               # API routes and endpoints
│   ├── data/             # MLB data fetching and processing
│   ├── services/         # Core services (MLB stats, TTS)
│   ├── story_engine/     # Story generation logic
│   └── preferences/      # User preferences handling
├── docker/               # Docker configuration
└── .github/             # GitHub Actions workflows
```

## 🔧 Configuration

### Required Environment Variables
- `GEMINI_API_KEY`: Google Gemini AI API key
- `MONGODB_URI`: MongoDB connection string
- `REDIS_URL`: Redis connection string
- Other configuration variables in `.env.template`

## 📚 API Documentation

### Core Endpoints
- `GET /api/v1/games`: Fetch available games
- `POST /api/v1/story`: Generate game story
- `POST /api/v1/quiz`: Generate game quiz
- `GET /api/v1/preferences`: Get user preferences
- Full API documentation available at `/docs`

## 🛠 Technologies

### Backend
- FastAPI (Python web framework)
- Google Gemini AI (Story generation)
- MongoDB (User preferences)
- Redis (Caching)
- MLB Stats API (Game data)

### Frontend
- HTML5/CSS3 with advanced animations and transitions
- Modern JavaScript with dynamic content loading
- Interactive UI components and real-time feedback
- CSS Grid and Flexbox for responsive layouts
- Custom animations and loading states
- Font Awesome icons for visual elements
- Progressive enhancement and graceful degradation
- Mobile-first responsive design principles

### Infrastructure
- Docker & Docker Compose
- GitHub Actions (CI/CD)
- Google Cloud Platform

## 🤝 Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📝 License
This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments
- MLB Stats API for providing comprehensive baseball data
- Google Cloud & Gemini AI for powering our story generation
- The open-source community for various tools and libraries used in this project 