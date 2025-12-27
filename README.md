# Advanced Timetable Generator

A modern, intelligent branch-level timetable generation system for colleges.

## Features

- 🌳 **Branch-Level Scheduling**: Considers all years, divisions, and resources together
- 🔍 **Automatic Clash Detection**: Prevents teacher, room, and lab conflicts
- 📊 **Easy CSV Upload**: Bulk import of teachers, subjects, and resources
- ✏️ **Editable Timetables**: Real-time validation with auto-fix suggestions
- 🧠 **Smart Constraint Engine**: Enforces all academic rules automatically

## Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: React + Vite
- **Styling**: Vanilla CSS with modern design system

## Getting Started

### Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run Flask server
python app.py
```

Server runs on `http://localhost:5000`

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend runs on `http://localhost:3000`

### Building for Production

```bash
cd frontend
npm run build
```

This builds the React app to `../static/` folder which Flask will serve.

## Project Structure

```
Adv Timetable Gen/
├── app.py                 # Flask backend
├── requirements.txt       # Python dependencies
├── static/               # Built React app (auto-generated)
└── frontend/
    ├── src/
    │   ├── components/   # Reusable components
    │   ├── pages/        # Page components
    │   ├── utils/        # Utility functions
    │   └── index.css     # Design system
    ├── package.json
    └── vite.config.js
```

## License

Built for educational purposes.
