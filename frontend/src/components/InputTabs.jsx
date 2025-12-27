import React from 'react'


function InputTabs({ activeTab, onTabChange = () => { }, tabs = [] }) {
    return (
        <div className="input-tabs">
            <div className="tabs-container">
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        className={`tab-button ${activeTab === tab.id ? 'active' : ''} ${tab.completed ? 'completed' : ''}`}
                        onClick={() => onTabChange(tab.id)}
                        type="button"
                    >
                        <span className="tab-icon">{tab.icon}</span>
                        <span className="tab-label">{tab.label}</span>
                        {tab.completed && (
                            <span className="tab-check">✓</span>
                        )}
                    </button>
                ))}
            </div>
        </div>
    )
}

export default InputTabs
