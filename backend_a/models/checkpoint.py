"""Load the same CPU model for the API and frozen research runs."""

from pathlib import Path


def load_model(path, revision=None):
    if not Path(path).is_file():
        raise FileNotFoundError("Model checkpoint is unavailable. Install best_model.pt before running predictions.")
    import torch
    from models.fusion import FusionModel, RoryModel
    from models.text_encoder import MODEL_REVISION, TextEncoder
    from models.vitals_mlp import VitalsMLP

    model = RoryModel(VitalsMLP(hidden_dim=64, out_dim=128, dropout=0.3),
                      TextEncoder(out_dim=128, dropout=0.3, device="cpu", revision=revision or MODEL_REVISION),
                      FusionModel(vitals_dim=128, text_dim=128, hidden_dim=256, dropout=0.3))
    model.load_state_dict(torch.load(path, map_location="cpu", weights_only=True, mmap=True))
    model.eval()
    return model
