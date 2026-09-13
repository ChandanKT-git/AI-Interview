# AI Interview Coach

AI Interview Coach is a full-stack, AI-driven platform designed to conduct highly realistic technical interviews. By leveraging advanced language models, the application dynamically generates role-specific questions, evaluates candidate responses in real-time, and provides detailed, actionable feedback.

## Live Demo

- **Application**: https://ai-interview-weld-pi.vercel.app/
- **Backend API**: https://ai-interview-backend-sige.onrender.com/

## Core Features

- **Dynamic Question Generation**: Automatically tailors interview questions based on the selected role, target company, and experience level.
- **Real-Time AI Evaluation**: Analyzes candidate answers using Groq-powered LLMs to grade performance across technical accuracy, communication, and problem-solving skills.
- **Dual User Roles**: 
  - **Candidates**: Can take practice interviews, track progress, and review comprehensive performance reports.
  - **Recruiters**: Can design, curate, and publish custom "Interview Packs" for specific job requisitions.
- **Resume Integration**: Parses candidate resumes to generate personalized, experience-driven questions.
- **Voice-to-Text Support**: Integrates Web Speech API for seamless audio dictation during the interview process.
- **Graceful Degradation**: Features a fully functional heuristic question bank and rule-based evaluator that seamlessly activates if the AI API is unavailable.

## Tech Stack

### Frontend
- **Framework**: React.js
- **Styling**: Tailwind CSS
- **Animations**: Framer Motion
- **Data Visualization**: Recharts
- **Routing**: React Router

### Backend
- **Framework**: FastAPI (Python)
- **Database**: MongoDB (via AsyncIOMotorClient)
- **AI Integration**: Groq API (OpenAI-compatible endpoints)
- **Authentication**: JWT-style opaque session tokens

## Local Development Setup

### Prerequisites
- Node.js (v16 or higher)
- Python (3.9 or higher)
- MongoDB instance (Local or Atlas)

### 1. Backend Setup

Navigate to the backend directory and set up the Python environment:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the `backend` directory:
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=interview_coach
GROQ_API_KEY=your_groq_api_key_here
```

Start the FastAPI server:
```bash
uvicorn server:app --reload --port 8001
```

### 2. Frontend Setup

Navigate to the frontend directory and install dependencies:

```bash
cd frontend
npm install
```

Create a `.env` file in the `frontend` directory:
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

Start the React development server:
```bash
npm start
```

## Architecture & Security

- **Authentication**: Implements secure session tokens stored in the database.
- **CORS Handling**: Backend is configured to accept cross-origin requests from specified frontend domains.
- **Stateless API**: The FastAPI backend remains entirely stateless, relying on the MongoDB session collection to verify authenticated requests.

## License

This project is licensed under the MIT License.
