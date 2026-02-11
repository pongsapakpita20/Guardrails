from typing import List, Dict
from .base import BaseGuardEngine, SwitchInfo, GuardResult

class NemoGuardEngine(BaseGuardEngine):
    def get_switches(self) -> List[SwitchInfo]:
        # NVIDIA NeMo เน้นเรื่อง Topic กับ Jailbreak เป็นหลัก
        return [
            SwitchInfo(key="jailbreak", label="Anti-Jailbreak (NeMo)", default=True),
            SwitchInfo(key="topical", label="Topical Control (Colang)", default=True),
            SwitchInfo(key="input_check", label="Input Validation", default=True),
        ]

    async def process(self, message: str, config: Dict[str, bool]) -> GuardResult:
        # Mock Logic ของ NeMo
        if config.get("jailbreak") and "ignore previous" in message.lower():
            return GuardResult(safe=False, violation="Jailbreak", reason="NeMo blocked jailbreak attempt")
            
        return GuardResult(safe=True)