import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

def hidden_init(layer):
    fan_in = layer.weight.data.size()[0]
    lim = 1. / np.sqrt(fan_in)
    return (-lim, lim)


class Actor(nn.Module):
    """Actor(Policy) Model"""
    
    def __init__(self, input_dim, hidden_in_dim, hidden_out_dim, output_dim, seed):
        """Initialize parameters and build actor.
        Params
        ======
            input_dim (int):  number of dimensions for input layer
            hidden_in_dim (int): number of nodes in first hidden layer
            hidden_out_dim (int): number of nodes in second hidden layer
            output_dim (int): number of dimensions for output layer
            seed (int): random seed
        """        
        super(Actor, self).__init__()
        self.seed = torch.manual_seed(seed)
        
        self.fc1 = nn.Linear(input_dim,hidden_in_dim)
        self.fc2 = nn.Linear(hidden_in_dim,hidden_out_dim)
        self.fc3 = nn.Linear(hidden_out_dim,output_dim)
        
        self.bn = nn.BatchNorm1d(hidden_in_dim)
        self.reset_parameters()

    def reset_parameters(self):        
        """Reset weights to near zero values."""
        self.fc1.weight.data.uniform_(*hidden_init(self.fc1))
        self.fc2.weight.data.uniform_(*hidden_init(self.fc2))
        self.fc3.weight.data.uniform_(-3e-3, 3e-3)

    def forward(self, state):
        """Map state to actions"""
        if state.dim() == 1:
            state = torch.unsqueeze(state,0)
        x = F.relu(self.fc1(state))
        x = self.bn(x)
        x = F.relu(self.fc2(x))
        x = F.tanh(self.fc3(x))
        return x
    
  
class Critic(nn.Module):
    """Critic(Value) Model"""
    
    def __init__(self, input_dim, hidden_in_dim, hidden_out_dim, seed):
        """Initialize parameters and build crictic.
        Params
        ======
            input_dim (int):  number of dimensions for input layer
            hidden_in_dim (int): number of nodes in first hidden layer
            hidden_out_dim (int): number of nodes in second hidden layer
            seed (int): random seed
        """        
        super(Critic, self).__init__()
        self.seed = torch.manual_seed(seed)
        
        self.fc1 = nn.Linear(input_dim, hidden_in_dim)
        self.fc2 = nn.Linear(hidden_in_dim, hidden_out_dim)
        self.fc3 = nn.Linear(hidden_out_dim, 1)
        
        self.bn = nn.BatchNorm1d(hidden_in_dim)
        self.reset_parameters()

    def reset_parameters(self):        
        """Reset weights to near zero values."""
        self.fc1.weight.data.uniform_(*hidden_init(self.fc1))
        self.fc2.weight.data.uniform_(*hidden_init(self.fc2))
        self.fc3.weight.data.uniform_(-3e-3, 3e-3)

    def forward(self, state, action):
        """Map (state, action) pair to Q-values"""
        
        xs = torch.cat((state, action), dim=1)
        x = F.relu(self.fc1(xs))
        x = self.bn(x)
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x
 
class Actor_Critics(object):
    
    """Collection of Actor Critic for mutliple agents"""
    def __init__(self, n_agents, state_size, action_size, hidden_in_dim=256, hidden_out_dim=256, seed=0):
        """Initialize parameters and build local/target actor critic.
        Params
        ======
            n_agents (int):  numgber of agents in the system
            state_size (int): number of state dimensions for a single agent
            action_size (int): number of action dimensions for a single agent
            hidden_in_dim (int): number of nodes in first hidden layer
            hidden_out_dim (int): number of nodes in second hidden layer
            seed (int): random seed
        """
        self.actor_local = Actor(state_size, hidden_in_dim, hidden_out_dim, action_size, seed).to(device)
        self.actor_target = Actor(state_size, hidden_in_dim, hidden_out_dim, action_size, seed).to(device)
        critic_input_size = (state_size + action_size) * n_agents
        self.critic_local = Critic(critic_input_size, hidden_in_dim, hidden_out_dim, seed).to(device)
        self.critic_target = Critic(critic_input_size, hidden_in_dim, hidden_out_dim, seed).to(device)