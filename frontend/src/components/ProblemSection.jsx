import { useScrollAnimation } from '../utils/ScrollAnimation'
import './ProblemSection.css'

function ProblemSection() {
    const [ref1, isVisible1] = useScrollAnimation()
    const [ref2, isVisible2] = useScrollAnimation()
    const [ref3, isVisible3] = useScrollAnimation()
    const [ref4, isVisible4] = useScrollAnimation()
    const [ref5, isVisible5] = useScrollAnimation()

    const problems = [
        {
            icon: '👥',
            title: 'Teacher Clashes',
            description: 'One teacher cannot be in two places at once, causing scheduling conflicts'
        },
        {
            icon: '🔬',
            title: 'Shared Lab Conflicts',
            description: 'Labs are shared across years, making practical scheduling extremely difficult'
        },
        {
            icon: '⚖️',
            title: 'Uneven Distribution',
            description: 'Lectures are not evenly distributed, causing workload imbalance'
        },
        {
            icon: '⏱️',
            title: 'Time-Consuming',
            description: 'Manual timetable creation takes days or weeks of meticulous planning'
        },
        {
            icon: '❌',
            title: 'Hard to Fix',
            description: 'A single change can break the entire timetable, requiring complete redo'
        }
    ]

    const refs = [ref1, ref2, ref3, ref4, ref5]
    const visibilities = [isVisible1, isVisible2, isVisible3, isVisible4, isVisible5]

    return (
        <section className="problem-section section">
            <div className="container">
                <div className="section-header text-center">
                    <span className="section-tag">The Challenge</span>
                    <h2 className="section-title">
                        ❌ Problems with Manual Timetable Creation
                    </h2>
                    <p className="section-description">
                        Creating college timetables manually is a nightmare of overlapping constraints
                    </p>
                </div>

                <div className="problem-grid">
                    {problems.map((problem, index) => (
                        <div
                            key={index}
                            ref={refs[index]}
                            className={`problem-card ${visibilities[index] ? 'visible' : ''}`}
                        >
                            <div className="problem-icon error-icon">{problem.icon}</div>
                            <h3 className="problem-title">{problem.title}</h3>
                            <p className="problem-description">{problem.description}</p>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    )
}

export default ProblemSection
