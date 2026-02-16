"""
Guardrails AI — Competitor Mention Guard
Comprehensive list of Thai transport competitors.
"""
from typing import Tuple, List

class CompetitorGuard:
    def __init__(self):
        self.competitors = [
            # สายการบิน
            "AirAsia", "แอร์เอเชีย",
            "Nok Air", "นกแอร์",
            "Thai Lion Air", "ไทยไลอ้อนแอร์",
            "VietJet", "เวียตเจ็ท",
            "Bangkok Airways", "บางกอกแอร์เวย์ส",
            "Thai Airways", "การบินไทย",
            "Thai Smile", "ไทยสมายล์",

            # รถทัวร์ / รถบัส
            "Nakhonchai Air", "นครชัยแอร์",
            "Sombat Tour", "สมบัติทัวร์",
            "บุษราคัมทัวร์", "ศรีสุพรรณ", "เชิดชัยทัวร์",
            "บขส", "รถโดยสาร บขส",

            # Ride-hailing
            "Grab", "แกร็บ",
            "Bolt", "โบลท์",
            "InDriver",
            "Uber", "อูเบอร์",

            # อื่นๆ
            "12Go", "Traveloka", "Agoda",
        ]

    def check(self, text: str) -> Tuple[bool, str]:
        lower_text = text.lower()
        found: List[str] = [c for c in self.competitors if c.lower() in lower_text]
        if found:
            return False, f"Competitor mentioned: {', '.join(found[:3])}"
        return True, "Clean"

competitor_guard = CompetitorGuard()
