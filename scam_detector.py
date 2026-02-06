import torch
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification

# Path to your extracted model folder
MODEL_PATH = "./distilbert"

# Load tokenizer and model ONCE
tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_PATH)
model = DistilBertForSequenceClassification.from_pretrained(MODEL_PATH)
model.eval()

def is_scam_message(message, threshold=0.7):
    """
    Returns:
        (is_scam: bool, confidence: float)
    """

    inputs = tokenizer(
        message,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=512
    )

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=1)

    scam_prob = probs[0][1].item()   # label 1 = scam
    return scam_prob >= threshold, scam_prob
