# ======== score_manager.py ========
import os
import json
from pathlib import Path
from typing import Dict, Any

class ScoreManager:
    def __init__(self, base_path: str = "user_scores"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
    
    def _get_user_file(self, user_id: int) -> Path:
        """Obtiene la ruta del archivo de puntuación para un usuario"""
        return self.base_path / f"{user_id}.json"
    
    def get_scores(self, user_id: int) -> Dict[str, int]:
        """Obtiene las puntuaciones de un usuario"""
        user_file = self._get_user_file(user_id)
        if not user_file.exists():
            return {"correct": 0, "incorrect": 0, "total": 0}
        
        with open(user_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def update_score(self, user_id: int, is_correct: bool):
        """Actualiza la puntuación de un usuario"""
        scores = self.get_scores(user_id)
        
        if is_correct:
            scores["correct"] = scores.get("correct", 0) + 1
        else:
            scores["incorrect"] = scores.get("incorrect", 0) + 1
        
        scores["total"] = scores["correct"] + scores["incorrect"]
        scores["average"] = (scores["correct"] / scores["total"]) * 100 if scores["total"] > 0 else 0
        
        with open(self._get_user_file(user_id), 'w', encoding='utf-8') as f:
            json.dump(scores, f, indent=2)
    
    def reset_scores(self, user_id: int):
        """Reinicia las puntuaciones de un usuario"""
        with open(self._get_user_file(user_id), 'w', encoding='utf-8') as f:
            json.dump({"correct": 0, "incorrect": 0, "total": 0, "average": 0}, f, indent=2)