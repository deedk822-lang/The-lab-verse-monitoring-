def select_model(self, task: str, budget_remaining: float = 0.0, prefer_free: bool = True, min_quality: int = 7) -> ModelSpec | None:
    if not isinstance(task, str):
        raise ValueError("Task must be a string")
    
    # ... rest of the function ...
from sqlalchemy import create_engine

class ModelSpec(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    provider = db.Column(db.String)
    cost_per_million_tokens = db.Column(db.Float)
    quality_score = db.Column(db.Integer)
    speed_score = db.Column(db.Integer)
    context_window = db.Column(db.Integer)
    specialization = db.Column(db.String)

    @classmethod
    def get_by_name(cls, name: str) -> 'ModelSpec':
        return cls.query.filter_by(name=name).first()