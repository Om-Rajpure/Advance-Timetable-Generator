class ConstraintLogger:
    """
    Tracks and explains why scheduling failed for specific sessions.
    separating Hard vs Soft constraint violations.
    """
    def __init__(self):
        # Structure: { "SubjectName": { "ContextID (e.g. BE-A-Batch1)": [Failures] } }
        self.logs = {} 
        self.unscheduled_items = [] # List of {subject, division, reason}

    def log_failure(self, subject, context_id, constraint_type, reason, details=None):
        """
        Log a specific constraint failure.
        constraint_type: "HARD" or "SOFT"
        reason: e.g. "Recess Conflict", "Teacher Unavailable"
        details: e.g. {"day": "Monday", "window": [3, 4]}
        """
        if subject not in self.logs:
            self.logs[subject] = {}
        if context_id not in self.logs[subject]:
            self.logs[subject][context_id] = []
            
        entry = {
            "type": constraint_type,
            "reason": reason,
            "details": details or {}
        }
        self.logs[subject][context_id].append(entry)

    def log_unscheduled(self, subject, context_id, summary_reason):
        """Mark an item as totally unscheduled"""
        self.unscheduled_items.append({
            "subject": subject,
            "context": context_id,
            "summary": summary_reason
        })

    def get_report(self):
        lines = ["=== CONSTRAINT VIOLATION REPORT ==="]
        
        if not self.unscheduled_items:
            lines.append("No completely unscheduled items.")
        else:
            for item in self.unscheduled_items:
                lines.append(f"\n[UNSCHEDULED] {item['subject']} ({item['context']})")
                lines.append(f"Reason: {item['summary']}")
                
                # Dig into detailed logs if available
                if item['subject'] in self.logs and item['context'] in self.logs[item['subject']]:
                    failures = self.logs[item['subject']][item['context']]
                    # Group by reason
                    counts = {}
                    for f in failures:
                        r = f['reason']
                        counts[r] = counts.get(r, 0) + 1
                    
                    lines.append("Detailed Constraint Blocks:")
                    for r, count in counts.items():
                        lines.append(f"  - {r}: {count} times")
        
        return "\n".join(lines)
