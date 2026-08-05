import React, { useState } from 'react';
import './ResourceAnalysisModal.css';

export default function ResourceAnalysisModal({ analysisData, reportText, onClose, onEditData }) {
  const [copied, setCopied] = useState(false);

  if (!analysisData && !reportText) return null;

  // Extract structured values or fall back to parsing text
  const division = analysisData?.division || "Division Analysis";
  const reason = analysisData?.reasonForFailure || {};
  const teacherReqs = analysisData?.teacherRequirements || [];
  const labReqs = analysisData?.labRequirements || [];
  const roomReqs = analysisData?.classroomRequirements || [];
  const bottlenecks = analysisData?.constraintBottlenecks || [];
  const fixes = analysisData?.suggestedFixes || [];
  const summary = analysisData?.resourceSummary || {
    teachers: ["None"],
    labs: ["None"],
    classrooms: ["None"],
    other: ["None"]
  };

  const handleCopyReport = () => {
    const textToCopy = reportText || JSON.stringify(analysisData, null, 2);
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="ram-overlay">
      <div className="ram-modal">
        {/* Header */}
        <div className="ram-header">
          <div className="ram-title-group">
            <div className="ram-icon-badge">⚡</div>
            <div>
              <h2 className="ram-title">Constraint Resource Analysis</h2>
              <p className="ram-subtitle">Bottleneck diagnosis & minimum additional resource requirements</p>
            </div>
          </div>
          <button className="ram-close-btn" onClick={onClose} title="Close Modal">✕</button>
        </div>

        {/* Body */}
        <div className="ram-body">
          {/* Reason Card */}
          <div className="ram-reason-card">
            <span className="ram-div-badge">Division: {division}</span>
            <div className="ram-reason-details">
              <div className="ram-reason-pill">
                <span>⚠️</span>
                <span>Theory lectures remaining: <strong>{reason.theoryRemaining ?? 0}</strong></span>
              </div>
              <div className="ram-reason-pill">
                <span>🧪</span>
                <span>Practicals remaining: <strong>{reason.practicalsRemaining ?? 0}</strong></span>
              </div>
            </div>
          </div>

          {/* Detailed Requirements Grid */}
          <div className="ram-grid">
            {/* Teacher Requirements */}
            <div className="ram-card">
              <h3 className="ram-card-title">👨‍🏫 Teacher Requirements</h3>
              <ul className="ram-list">
                {teacherReqs.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>

            {/* Lab Requirements */}
            <div className="ram-card">
              <h3 className="ram-card-title">🔬 Lab Requirements</h3>
              <ul className="ram-list">
                {labReqs.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>

            {/* Classroom Requirements */}
            <div className="ram-card">
              <h3 className="ram-card-title">🏫 Classroom Requirements</h3>
              <ul className="ram-list">
                {roomReqs.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>

            {/* Constraint Bottlenecks */}
            <div className="ram-card">
              <h3 className="ram-card-title">⚡ Constraint Bottlenecks</h3>
              <ul className="ram-list">
                {bottlenecks.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>

            {/* Actionable Suggested Fixes */}
            <div className="ram-card ram-fixes-card">
              <h3 className="ram-card-title">💡 Actionable Suggested Fixes</h3>
              <div className="ram-list">
                {fixes.map((fix, idx) => (
                  <div className="ram-fix-item" key={idx}>
                    <span>{fix}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Resource Summary Card */}
          <div className="ram-summary-box">
            <div className="ram-summary-header">
              <span>📋</span> Minimum Additional Resources Needed
            </div>
            <div className="ram-summary-grid">
              <div className="ram-summary-col">
                <div className="ram-summary-col-label">Teachers</div>
                {(summary.teachers || ["None"]).map((t, i) => (
                  <span className="ram-summary-tag" key={i}>{t}</span>
                ))}
              </div>

              <div className="ram-summary-col">
                <div className="ram-summary-col-label">Labs</div>
                {(summary.labs || ["None"]).map((l, i) => (
                  <span className="ram-summary-tag" key={i}>{l}</span>
                ))}
              </div>

              <div className="ram-summary-col">
                <div className="ram-summary-col-label">Classrooms</div>
                {(summary.classrooms || ["None"]).map((c, i) => (
                  <span className="ram-summary-tag" key={i}>{c}</span>
                ))}
              </div>

              <div className="ram-summary-col">
                <div className="ram-summary-col-label">Other</div>
                {(summary.other || ["None"]).map((o, i) => (
                  <span className="ram-summary-tag" key={i}>{o}</span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="ram-footer">
          <button className="ram-btn ram-btn-secondary" onClick={handleCopyReport}>
            {copied ? "✓ Copied to Clipboard!" : "📋 Copy Full Report"}
          </button>
          {onEditData && (
            <button className="ram-btn ram-btn-secondary" onClick={onEditData}>
              ✏️ Adjust Inputs / Resources
            </button>
          )}
          <button className="ram-btn ram-btn-primary" onClick={onClose}>
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
