"""
Edit history - tracks edit operations for undo/redo support.
"""
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from copy import deepcopy


@dataclass
class EditOperation:
    """Represents a single edit operation."""
    operation_type: str  # "add_overlay", "remove_overlay", "move_overlay", "modify_segment"
    timestamp: datetime
    data: Dict[str, Any]
    inverse_data: Dict[str, Any]


class EditHistory:
    """Track edit history for undo/redo."""

    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.history: List[EditOperation] = []
        self.current_index: int = -1

    def add_operation(
        self,
        operation_type: str,
        data: Dict[str, Any],
        inverse_data: Dict[str, Any]
    ):
        """
        Add an edit operation.

        Args:
            operation_type: Type of operation
            data: Operation data
            inverse_data: Data needed to undo the operation
        """
        # Remove any operations after current index (redo history)
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]

        operation = EditOperation(
            operation_type=operation_type,
            timestamp=datetime.now(),
            data=deepcopy(data),
            inverse_data=deepcopy(inverse_data)
        )

        self.history.append(operation)
        self.current_index = len(self.history) - 1

        # Trim history if too long
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
            self.current_index = len(self.history) - 1

    def can_undo(self) -> bool:
        """Check if undo is available."""
        return self.current_index >= 0

    def can_redo(self) -> bool:
        """Check if redo is available."""
        return self.current_index < len(self.history) - 1

    def undo(self) -> Optional[Dict[str, Any]]:
        """
        Undo last operation.

        Returns:
            Inverse data for the operation, or None if nothing to undo
        """
        if not self.can_undo():
            return None

        operation = self.history[self.current_index]
        self.current_index -= 1

        return operation.inverse_data

    def redo(self) -> Optional[Dict[str, Any]]:
        """
        Redo next operation.

        Returns:
            Operation data, or None if nothing to redo
        """
        if not self.can_redo():
            return None

        self.current_index += 1
        operation = self.history[self.current_index]

        return operation.data

    def clear(self):
        """Clear all history."""
        self.history.clear()
        self.current_index = -1

    def get_history_summary(self) -> List[Dict]:
        """Get summary of all operations."""
        return [
            {
                "index": i,
                "type": op.operation_type,
                "timestamp": op.timestamp.isoformat()
            }
            for i, op in enumerate(self.history)
        ]
