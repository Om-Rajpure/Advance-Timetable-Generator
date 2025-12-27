import { useScrollAnimation } from '../utils/ScrollAnimation'
import './FeaturesSection.css'

function FeaturesSection() {
    const [ref1, isVisible1] = useScrollAnimation()
    const [ref2, isVisible2] = useScrollAnimation()
    const [ref3, isVisible3] = useScrollAnimation()
    const [ref4, isVisible4] = useScrollAnimation()

    const features = [
        {
            icon: '📁',
            title: 'Easy CSV / Excel Upload',
            description: 'Simply upload your teacher, subject, and resource data in bulk. No manual entry needed.',
            color: '#3B4FDF'
        },
        {
            icon: '✏️',
            title: 'Editable with Auto-Fix',
            description: 'Edit any slot with real-time validation. Conflicts are detected instantly with suggested fixes.',
            color: '#10B981'
        },
        {
            icon: '🧠',
            title: 'Smart Constraint Engine',
            description: 'Enforces all academic rules automatically—no teacher clashes, no lab conflicts, balanced workload.',
            color: '#8B5CF6'
        },
        {
            icon: '📊',
            title: 'Teacher & Lab Analytics',
            description: 'Visual insights into workload distribution, lab utilization, and free time slots.',
            color: '#F59E0B'
        }
    ]

    const refs = [ref1, ref2, ref3, ref4]
    const visibilities = [isVisible1, isVisible2, isVisible3, isVisible4]

    return (
        <section id="features" className="features-section section">
            <div className="container">
                <div className="section-header text-center">
                    <span className="section-tag features-tag">Key Features</span>
                    <h2 className="section-title">
                        🚀 Powerful Features That Set Us Apart
                    </h2>
                    <p className="section-description">
                        Everything you need to create perfect timetables, all in one place
                    </p>
                </div>

                <div className="features-grid">
                    {features.map((feature, index) => (
                        <div
                            key={index}
                            ref={refs[index]}
                            className={`feature-card ${visibilities[index] ? 'visible' : ''}`}
                        >
                            <div className="feature-icon-wrapper" style={{ background: `${feature.color}15` }}>
                                <div className="feature-icon" style={{ color: feature.color }}>
                                    {feature.icon}
                                </div>
                            </div>
                            <h3 className="feature-title">{feature.title}</h3>
                            <p className="feature-description">{feature.description}</p>
                            <div className="feature-glow" style={{ background: `${feature.color}20` }}></div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    )
}

export default FeaturesSection
