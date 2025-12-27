import { useNavigate } from 'react-router-dom'
import TimetableIllustration from './TimetableIllustration'
import './Hero.css'

function Hero() {
    const navigate = useNavigate()

    const handleGenerateTimetable = () => {
        navigate('/login')
    }

    const handleUploadTimetable = () => {
        navigate('/login')
    }

    return (
        <section id="home" className="hero-section">
            <div className="container hero-container">
                <div className="hero-content">
                    <h1 className="hero-title slide-in-left">
                        Smart Branch-Level<br />
                        <span className="gradient-text">Timetable Generator</span>
                    </h1>

                    <p className="hero-subtitle slide-in-left" style={{ animationDelay: '0.2s' }}>
                        Automatically generate, edit, and optimize college timetables without clashes.
                    </p>

                    <div className="hero-description slide-in-left" style={{ animationDelay: '0.3s' }}>
                        <p>
                            Managing teachers, labs, divisions, and academic rules manually is complex and error-prone.
                            <strong> Our system solves this</strong> by generating a clash-free, editable timetable for the entire branch.
                        </p>
                    </div>

                    <div className="hero-buttons slide-in-left" style={{ animationDelay: '0.4s' }}>
                        <button
                            className="btn btn-gradient btn-lg btn-pulse"
                            onClick={handleGenerateTimetable}
                        >
                            🚀 Generate Timetable
                        </button>
                        <button
                            className="btn btn-outline btn-lg"
                            onClick={handleUploadTimetable}
                        >
                            📤 Upload Timetable
                        </button>
                    </div>

                    <p className="hero-auth-link slide-in-left" style={{ animationDelay: '0.5s' }}>
                        Already have an account? <a href="/login">Login here</a>
                    </p>
                </div>

                <div className="hero-illustration slide-in-right">
                    <TimetableIllustration />
                </div>
            </div>
        </section>
    )
}

export default Hero
