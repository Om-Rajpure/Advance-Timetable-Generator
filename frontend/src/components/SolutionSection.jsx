import { useScrollAnimation } from '../utils/ScrollAnimation'
import './SolutionSection.css'

function SolutionSection() {
    const [ref1, isVisible1] = useScrollAnimation()
    const [ref2, isVisible2] = useScrollAnimation()
    const [ref3, isVisible3] = useScrollAnimation()
    const [ref4, isVisible4] = useScrollAnimation()
    const [ref5, isVisible5] = useScrollAnimation()

    const solutions = [
        {
            icon: '🌳',
            title: 'Branch-Level Scheduling',
            description: 'Considers all years, divisions, and resources together for optimal scheduling'
        },
        {
            icon: '🔍',
            title: 'Automatic Clash Detection',
            description: 'Instantly identifies and prevents teacher, room, and lab conflicts'
        },
        {
            icon: '🎯',
            title: 'Smart Batch Handling',
            description: 'Intelligently schedules all practical batches simultaneously across labs'
        },
        {
            icon: '📊',
            title: 'Easy Input & Editing',
            description: 'Upload CSV files or edit directly with real-time validation'
        },
        {
            icon: '✅',
            title: 'Real-Time Validation',
            description: 'Every change is validated instantly with auto-fix suggestions'
        }
    ]

    const refs = [ref1, ref2, ref3, ref4, ref5]
    const visibilities = [isVisible1, isVisible2, isVisible3, isVisible4, isVisible5]

    return (
        <section id="how-it-works" className="solution-section section">
            <div className="container">
                <div className="section-header text-center">
                    <span className="section-tag success-tag">Our Approach</span>
                    <h2 className="section-title">
                        ✅ Our Smart Solution
                    </h2>
                    <p className="section-description">
                        Intelligent automation that handles complexity so you don't have to
                    </p>
                </div>

                <div className="solution-grid">
                    {solutions.map((solution, index) => (
                        <div
                            key={index}
                            ref={refs[index]}
                            className={`solution-card ${visibilities[index] ? 'visible' : ''}`}
                        >
                            <div className="solution-icon">{solution.icon}</div>
                            <h3 className="solution-title">{solution.title}</h3>
                            <p className="solution-description">{solution.description}</p>
                            <div className="solution-check">✓</div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    )
}

export default SolutionSection
