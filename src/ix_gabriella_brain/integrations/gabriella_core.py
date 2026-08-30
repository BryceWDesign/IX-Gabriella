from __future__ import annotations

from dataclasses import dataclass

from ix_gabriella_brain.brain import GabriellaBrain


@dataclass
class GabriellaBrainAdapter:
    """Small integration boundary for the IX-Gabriella v0.2 local assistant shell."""

    brain: GabriellaBrain

    def handle_user_text(self, text: str, *, user_id: str = "local-user", session_id: str = "local-session") -> dict[str, object]:
        packet = self.brain.think(text, user_id=user_id, channel="gabriella_gui", session_id=session_id)
        return {
            "packet_id": packet.packet_id,
            "message": packet.decision.user_message,
            "route": packet.route.route.value,
            "status": packet.decision.status.value,
            "requires_approval": packet.decision.needs_user_input,
            "receipt_hash": packet.receipt_hash,
            "brain_packet": packet.to_dict(),
        }
