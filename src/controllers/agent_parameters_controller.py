from fastapi import APIRouter, HTTPException
from models.schemas import AgentParameter
from typing import List

router = APIRouter(prefix="/api/v1/agent-parameters", tags=["agent-parameters"])

# In-memory storage for demonstration purposes (replace with database integration)
agent_parameters_db = []

@router.post("/save", response_model=AgentParameter)
def save_agent_parameters(agent_parameters: AgentParameter):
    """Save or update agent parameters."""
    # Check if the agent already exists
    for record in agent_parameters_db:
        if record.agent_name == agent_parameters.agent_name:
            # Update existing record
            record.parameter1 = agent_parameters.parameter1
            record.parameter2 = agent_parameters.parameter2
            record.parameter3 = agent_parameters.parameter3
            record.parameter4 = agent_parameters.parameter4
            return record

    # Add new record
    agent_parameters_db.append(agent_parameters)
    return agent_parameters

@router.get("/fetch", response_model=List[AgentParameter])
def fetch_agent_parameters():
    """Fetch all agent parameters."""
    return agent_parameters_db
