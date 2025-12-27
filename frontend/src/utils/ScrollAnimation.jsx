import { useState, useEffect } from 'react'

/**
 * Custom hook for scroll-triggered animations using Intersection Observer
 * @param {Object} options - Intersection Observer options
 * @returns {Array} - [ref, isVisible]
 */
export function useScrollAnimation(options = {}) {
    const [isVisible, setIsVisible] = useState(false)
    const [ref, setRef] = useState(null)

    useEffect(() => {
        if (!ref) return

        const observer = new IntersectionObserver(([entry]) => {
            if (entry.isIntersecting) {
                setIsVisible(true)
                // Once visible, stop observing (animation runs once)
                observer.unobserve(entry.target)
            }
        }, {
            threshold: 0.1,
            ...options
        })

        observer.observe(ref)

        return () => {
            if (ref) {
                observer.unobserve(ref)
            }
        }
    }, [ref, options])

    return [setRef, isVisible]
}
