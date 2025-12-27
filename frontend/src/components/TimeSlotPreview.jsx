import React from 'react'
import '../styles/formComponents.css'

function TimeSlotPreview({ startTime, endTime, lectureDuration, recessStart, recessDuration }) {
    // Convert time strings to minutes from midnight
    const timeToMinutes = (timeStr) => {
        const [time, period] = timeStr.split(' ')
        let [hours, minutes] = time.split(':').map(Number)
        if (period === 'PM' && hours !== 12) hours += 12
        if (period === 'AM' && hours === 12) hours = 0
        return hours * 60 + minutes
    }

    const startMinutes = timeToMinutes(startTime)
    const endMinutes = timeToMinutes(endTime)
    const totalMinutes = endMinutes - startMinutes
    const recessMinutes = recessStart ? timeToMinutes(recessStart) - startMinutes : null

    // Calculate slots
    let slots = []
    let currentTime = startMinutes

    while (currentTime < endMinutes) {
        const isRecess = recessMinutes !== null &&
            currentTime >= recessMinutes &&
            currentTime < (recessMinutes + recessDuration)

        if (isRecess && currentTime === recessMinutes) {
            slots.push({
                type: 'recess',
                duration: recessDuration,
                start: currentTime
            })
            currentTime += recessDuration
        } else if (!isRecess) {
            slots.push({
                type: 'lecture',
                duration: lectureDuration,
                start: currentTime
            })
            currentTime += lectureDuration
        }
    }

    // Format minutes back to time
    const minutesToTime = (mins) => {
        const totalMins = startMinutes + mins
        let hours = Math.floor(totalMins / 60)
        const minutes = totalMins % 60
        const period = hours >= 12 ? 'PM' : 'AM'
        if (hours > 12) hours -= 12
        if (hours === 0) hours = 12
        return `${hours}:${minutes.toString().padStart(2, '0')} ${period}`
    }

    const lectureCount = slots.filter(s => s.type === 'lecture').length

    return (
        <div className="timeslot-preview">
            <div className="timeslot-summary">
                <strong>{lectureCount} lecture slots</strong> per day
                {recessDuration > 0 && <span> (+ {recessDuration} min recess)</span>}
            </div>
            <div className="timeslot-timeline">
                {slots.map((slot, index) => (
                    <div
                        key={index}
                        className={`timeslot-block ${slot.type}`}
                        style={{ flex: slot.duration }}
                    >
                        <div className="slot-label">
                            {slot.type === 'recess' ? '☕ Recess' : `Slot ${slots.filter((s, i) => i < index && s.type === 'lecture').length + 1}`}
                        </div>
                        <div className="slot-time">
                            {minutesToTime(slot.start - startMinutes)}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}

export default TimeSlotPreview
