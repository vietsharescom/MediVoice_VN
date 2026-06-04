# src/models/_phobert_crf.py
# PhoBERT-base-v2 + CRF model architecture — used by training + inference
# FID: MV-FID-018
# Version: v1.0

import torch
import torch.nn as nn


class PhoBERTCRFModel(nn.Module):
    """
    PhoBERT-base-v2 encoder + linear projection + CRF decoder.

    Training: torchcrf.CRF.forward() returns negative log-likelihood loss.
    Inference: torchcrf.CRF.decode() returns Viterbi best path.
    """

    def __init__(self, num_labels: int, dropout: float = 0.1):
        super().__init__()
        try:
            from transformers import AutoModel
            self.bert = AutoModel.from_pretrained("vinai/phobert-base-v2")
        except Exception:
            # Offline fallback: bare config (weights loaded separately)
            from transformers import RobertaConfig, RobertaModel
            config = RobertaConfig(
                vocab_size=64001,
                hidden_size=768,
                num_hidden_layers=12,
                num_attention_heads=12,
            )
            self.bert = RobertaModel(config)

        self.dropout = nn.Dropout(dropout)
        self.linear = nn.Linear(768, num_labels)

        try:
            from torchcrf import CRF
            self.crf = CRF(num_labels, batch_first=True)
            self._has_crf = True
        except ImportError:
            self.crf = None
            self._has_crf = False

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        labels: torch.Tensor = None,
    ):
        """
        Training:   pass labels → returns CRF NLL loss (scalar).
        Inference:  labels=None → returns Viterbi tag sequence (List[List[int]]).
        """
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        sequence_output = self.dropout(outputs.last_hidden_state)
        emissions = self.linear(sequence_output)

        if self._has_crf:
            mask = attention_mask.bool()
            if labels is not None:
                loss = -self.crf(emissions, labels, mask=mask, reduction="mean")
                return loss
            else:
                return self.crf.decode(emissions, mask=mask)
        else:
            # Fallback: argmax (no CRF)
            if labels is not None:
                loss_fn = nn.CrossEntropyLoss(ignore_index=-100)
                loss = loss_fn(
                    emissions.view(-1, emissions.size(-1)),
                    labels.view(-1),
                )
                return loss
            else:
                return emissions.argmax(dim=-1).tolist()
