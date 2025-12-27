import { useNavigate } from 'react-router-dom'
import './CTASection.css'

function CTASection() {
    const navigate = useNavigate()

    return (
        <section className="cta-section section">
            <div className="container">
                <div className="cta-content">
                    <h2 className="cta-title">
                        Ready to create a clash-free timetable in minutes?
                    </h2>
                    <p className="cta-description">
                        Join colleges that have transformed their scheduling process with intelligent automation
                    </p>
                    <div className="cta-buttons">
                        <button
                            className="btn btn-gradient btn-lg btn-pulse"
                            onClick={() => navigate('/signup')}
                        >
                            🚀 Get Started Free
                        </button>
                        <button
                            className="btn btn-outline-white btn-lg"
                            onClick={() => navigate('/login')}
                        >
                            📤 Upload Your Timetable
                        </button>
                    </div>
                    <p className="cta-subtext">
                        No credit card required • 5-minute setup • Instant results
                    </p>
                </div>
            </div>
        </section>
    )
}

export default CTASection
