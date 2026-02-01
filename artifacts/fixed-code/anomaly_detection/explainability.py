class AnomalyScoreModel(nn.Module):
    def __init__(self, model):
        super().__init__()
        self.model = model

    def forward(self, x):
        _, anomaly_score, _ = self.model(x)
        return anomaly_score