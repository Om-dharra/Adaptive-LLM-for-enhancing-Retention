import torch
import torch.nn as nn

class DKTModel(nn.Module):
    def __init__(self, num_skills, hidden_dim=100, input_dim=100):
        super(DKTModel, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_skills = num_skills
        
        self.embedding = nn.Embedding(2 * num_skills, input_dim)
        
        self.lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        
        self.out = nn.Linear(hidden_dim, num_skills)
        self.sigmoid = nn.Sigmoid()

    def forward(self, input_seq, hidden_state=None):
        embed = self.embedding(input_seq) 
        
        lstm_out, new_hidden = self.lstm(embed, hidden_state)
        
    
        logits = self.out(lstm_out)
        preds = self.sigmoid(logits)
        
        return preds, new_hidden