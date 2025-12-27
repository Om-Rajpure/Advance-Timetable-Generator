import Navbar from '../components/Navbar'
import Hero from '../components/Hero'
import ProblemSection from '../components/ProblemSection'
import SolutionSection from '../components/SolutionSection'
import FeaturesSection from '../components/FeaturesSection'
import CTASection from '../components/CTASection'
import Footer from '../components/Footer'

function LandingPage() {
    return (
        <div className="landing-page">
            <Navbar />
            <Hero />
            <ProblemSection />
            <SolutionSection />
            <FeaturesSection />
            <CTASection />
            <Footer />
        </div>
    )
}

export default LandingPage
