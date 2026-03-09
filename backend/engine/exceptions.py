class InfeasibleScheduleError(Exception):
    """Raised when the scheduler strictly fails to find a valid timetable."""
    def __init__(self, message, reasons=None):
        super().__init__(message)
        self.reasons = reasons or []
