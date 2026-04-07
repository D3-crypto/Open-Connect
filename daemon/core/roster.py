import json
import os

class RosterManager:
    def __init__(self, storage_path="trusted_roster.json"):
        self.storage_path = storage_path
        self.roster = self._load_roster()

    def _load_roster(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        return {"ecosystem_id": None, "peers": {}}

    def save_roster(self):
        with open(self.storage_path, 'w') as f:
            json.dump(self.roster, f, indent=2)

    def is_peer_trusted(self, public_key_b64):
        """
        THIS IS THE CORE SECURITY GATE. 
        If a device is not in this local list, its packets are instantly dropped.
        """
        return public_key_b64 in self.roster.get("peers", {})
