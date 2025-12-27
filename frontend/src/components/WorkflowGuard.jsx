import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDashboardState } from '../hooks/useDashboardState'

/**
 * WorkflowGuard Component
 * Protects routes by ensuring required workflow steps are completed
 * Redirects to dashboard with a message if requirements are not met
 */
function WorkflowGuard({ children, requiredStep }) {
    const navigate = useNavigate()
    const { getWorkflowStatus } = useDashboardState()
    const workflowStatus = getWorkflowStatus()

    useEffect(() => {
        let shouldRedirect = false
        let message = ''

        switch (requiredStep) {
            case 'branchSetup':
                if (!workflowStatus.canAccessSmartInput) {
                    shouldRedirect = true
                    message = 'Please complete Branch Setup first'
                }
                break

            case 'smartInput':
                if (!workflowStatus.canAccessGenerate) {
                    shouldRedirect = true
                    message = workflowStatus.branchSetupCompleted
                        ? 'Please complete Smart Input first'
                        : 'Please complete Branch Setup and Smart Input first'
                }
                break

            default:
                break
        }

        if (shouldRedirect) {
            // Show toast message (could be replaced with a toast library)
            const toast = document.createElement('div')
            toast.className = 'workflow-guard-toast'
            toast.textContent = message
            toast.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: linear-gradient(135deg, #ef4444, #dc2626);
                color: white;
                padding: 16px 24px;
                border-radius: 12px;
                box-shadow: 0 8px 24px rgba(239, 68, 68, 0.3);
                z-index: 10000;
                font-weight: 600;
                animation: slideInRight 0.3s ease-out;
            `
            document.body.appendChild(toast)

            setTimeout(() => {
                toast.style.animation = 'slideOutRight 0.3s ease-out'
                setTimeout(() => toast.remove(), 300)
            }, 3000)

            // Add animations if not already present
            if (!document.getElementById('workflow-guard-styles')) {
                const style = document.createElement('style')
                style.id = 'workflow-guard-styles'
                style.textContent = `
                    @keyframes slideInRight {
                        from {
                            transform: translateX(400px);
                            opacity: 0;
                        }
                        to {
                            transform: translateX(0);
                            opacity: 1;
                        }
                    }
                    @keyframes slideOutRight {
                        from {
                            transform: translateX(0);
                            opacity: 1;
                        }
                        to {
                            transform: translateX(400px);
                            opacity: 0;
                        }
                    }
                `
                document.head.appendChild(style)
            }

            navigate('/dashboard', { replace: true })
        }
    }, [requiredStep, workflowStatus, navigate])

    return children
}

export default WorkflowGuard
