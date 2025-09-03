# {
#   "Seq": [
#     { "Depends": "py-lib-genlayer-embeddings:09h0i209wrzh4xzq86f79c60x0ifs7xcjwl53ysrnw06i54ddxyi" },
#     { "Depends": "py-genlayer:1j12s63yfjpva9ik2xgnffgrs6v44y1f52jvj9w7xvdn7qckd379" }
#   ]
# }

from datetime import datetime, timezone
from genlayer import *


class SimpleTimeContract(gl.Contract):
    """
    A simple contract that demonstrates time-based function availability.
    """

    start_date: str  # ISO format datetime string
    data: str
    is_active: bool

    def __init__(self, start_datetime_iso: str):
        """
        Initialize the contract with a start date.
        If no date provided, uses current time.
        """
        self.start_date = start_datetime_iso
        self.is_active = False

    def _days_since_start(self) -> int:
        """Calculate days elapsed since start date."""
        current = datetime.now(timezone.utc)
        start = datetime.fromisoformat(self.start_date)
        print(f"Current: {current}, Start: {start}")
        delta = current - start
        print(f"Delta: {delta}")
        return delta.days

    @gl.public.write
    def activate(self):
        """
        Activate the contract.
        Only works if current date is after start date.
        """
        days = self._days_since_start()

        if days < 0:
            raise ValueError(
                f"Cannot activate before start date. Days until start: {abs(days)}"
            )

        self.is_active = True

    @gl.public.write
    def set_data(self, value: str):
        """
        Set data in the contract.
        Only works if contract is active and within 30 days of start.
        """
        if not self.is_active:
            raise ValueError("Contract must be activated first")

        days = self._days_since_start()

        if days > 30:
            raise ValueError(
                f"Function expired. Was available for 30 days after start, now at day {days}"
            )

        self.data = value

    @gl.public.view
    def get_status(self) -> dict:
        """Get current contract status."""
        days = self._days_since_start()
        current = datetime.now(timezone.utc)

        return {
            "start_date": self.start_date,
            "current_time": current.isoformat(),
            "days_since_start": days,
            "is_active": self.is_active,
            "data": self.data,
            "can_activate": days >= 0 and not self.is_active,
            "can_set_data": self.is_active and 0 <= days <= 30,
        }
