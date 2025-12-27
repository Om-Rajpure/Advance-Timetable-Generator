function TimetableIllustration() {
    return (
        <svg
            viewBox="0 0 500 400"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className="illustration-svg"
        >
            {/* Background Grid */}
            <rect x="50" y="50" width="400" height="300" rx="20" fill="url(#gridGradient)" />

            {/* Grid Lines */}
            <g opacity="0.3">
                <line x1="50" y1="100" x2="450" y2="100" stroke="#3B4FDF" strokeWidth="2" />
                <line x1="50" y1="150" x2="450" y2="150" stroke="#3B4FDF" strokeWidth="2" />
                <line x1="50" y1="200" x2="450" y2="200" stroke="#3B4FDF" strokeWidth="2" />
                <line x1="50" y1="250" x2="450" y2="250" stroke="#3B4FDF" strokeWidth="2" />
                <line x1="50" y1="300" x2="450" y2="300" stroke="#3B4FDF" strokeWidth="2" />

                <line x1="130" y1="50" x2="130" y2="350" stroke="#3B4FDF" strokeWidth="2" />
                <line x1="210" y1="50" x2="210" y2="350" stroke="#3B4FDF" strokeWidth="2" />
                <line x1="290" y1="50" x2="290" y2="350" stroke="#3B4FDF" strokeWidth="2" />
                <line x1="370" y1="50" x2="370" y2="350" stroke="#3B4FDF" strokeWidth="2" />
            </g>

            {/* Animated Cells */}
            <rect x="60" y="110" width="60" height="35" rx="8" fill="#10B981" opacity="0.8">
                <animate attributeName="opacity" values="0.6;1;0.6" dur="2s" repeatCount="indefinite" />
            </rect>
            <rect x="140" y="160" width="60" height="35" rx="8" fill="#3B4FDF" opacity="0.8">
                <animate attributeName="opacity" values="0.6;1;0.6" dur="2.5s" repeatCount="indefinite" />
            </rect>
            <rect x="220" y="210" width="60" height="35" rx="8" fill="#10B981" opacity="0.8">
                <animate attributeName="opacity" values="0.6;1;0.6" dur="3s" repeatCount="indefinite" />
            </rect>
            <rect x="300" y="110" width="60" height="35" rx="8" fill="#3B4FDF" opacity="0.8">
                <animate attributeName="opacity" values="0.6;1;0.6" dur="2.2s" repeatCount="indefinite" />
            </rect>

            {/* AI Brain Icon */}
            <circle cx="420" cy="80" r="40" fill="url(#brainGradient)">
                <animate attributeName="r" values="38;42;38" dur="3s" repeatCount="indefinite" />
            </circle>

            {/* Brain Connections */}
            <path d="M 410 75 Q 400 70 395 65" stroke="#fff" strokeWidth="3" strokeLinecap="round" opacity="0.8" />
            <path d="M 430 75 Q 440 70 445 65" stroke="#fff" strokeWidth="3" strokeLinecap="round" opacity="0.8" />
            <circle cx="410" cy="75" r="3" fill="#fff" />
            <circle cx="430" cy="75" r="3" fill="#fff" />
            <circle cx="420" cy="90" r="3" fill="#fff" />

            {/* Connection Lines */}
            <path d="M 380 80 L 360 110" stroke="#10B981" strokeWidth="2" strokeDasharray="5,5" opacity="0.6">
                <animate attributeName="stroke-dashoffset" from="0" to="10" dur="1s" repeatCount="indefinite" />
            </path>
            <path d="M 385 100 L 300 140" stroke="#3B4FDF" strokeWidth="2" strokeDasharray="5,5" opacity="0.6">
                <animate attributeName="stroke-dashoffset" from="0" to="10" dur="1.2s" repeatCount="indefinite" />
            </path>

            {/* Gradients */}
            <defs>
                <linearGradient id="gridGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#F0F4FF" />
                    <stop offset="100%" stopColor="#E0E7FF" />
                </linearGradient>
                <linearGradient id="brainGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#3B4FDF" />
                    <stop offset="100%" stopColor="#10B981" />
                </linearGradient>
            </defs>
        </svg>
    )
}

export default TimetableIllustration
