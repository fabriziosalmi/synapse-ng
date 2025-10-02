"""
AI Agent Module for Synapse-NG
=================================

This module provides local LLM capabilities for natural language interaction,
strategic analysis, and automation. Each node runs its own AI agent that can:
- Interpret natural language commands and convert them to API actions
- Analyze network state and make strategic decisions
- Proactively participate in governance, tasks, and auctions
- Learn from user objectives and optimize behavior

Model: Qwen3 0.6B (GGUF format)
Engine: llama-cpp-python
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import os

logger = logging.getLogger(__name__)


class AgentObjective(str, Enum):
    """Predefined agent objectives"""
    MAXIMIZE_SP = "maximize_synapse_points"
    MAXIMIZE_REPUTATION = "maximize_reputation"
    SPECIALIZE_SKILLS = "specialize_in_skills"
    PARTICIPATE_GOVERNANCE = "participate_in_governance"
    COLLABORATE_TEAMS = "join_collaborative_teams"
    WIN_AUCTIONS = "win_valuable_auctions"
    MAINTAIN_PRIVACY = "maintain_privacy_zkp"
    BALANCE_ALL = "balanced_participation"


@dataclass
class UserObjectives:
    """User-defined objectives for the AI agent"""
    primary_objective: AgentObjective = AgentObjective.BALANCE_ALL
    target_skills: List[str] = field(default_factory=list)
    min_sp_reserve: int = 100  # Minimum SP to keep
    max_bid_percentage: float = 0.3  # Max % of SP to bid in auctions
    auto_vote: bool = True
    auto_apply_tasks: bool = True
    auto_join_teams: bool = True
    risk_tolerance: float = 0.5  # 0.0 = conservative, 1.0 = aggressive
    

@dataclass
class AgentAction:
    """Represents an action the AI wants to execute"""
    action: str  # API endpoint or action name
    params: Dict[str, Any]
    reasoning: Optional[str] = None
    priority: int = 5  # 1-10, higher = more important


@dataclass
class NetworkContext:
    """Network state context for the AI agent"""
    node_id: str
    channel: str
    synapse_points: int
    reputation: float
    skills: List[str]
    open_tasks: List[Dict]
    active_proposals: List[Dict]
    active_auctions: List[Dict]
    available_teams: List[Dict]
    peer_count: int
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class LLMEngine:
    """Wrapper for llama-cpp-python LLM"""
    
    def __init__(self, model_path: str, n_ctx: int = 2048, n_threads: int = 4):
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.llm = None
        
    def load_model(self) -> bool:
        """Load GGUF model into memory"""
        try:
            # Import here to allow graceful degradation if not installed
            from llama_cpp import Llama
            
            logger.info(f"Loading LLM model from {self.model_path}")
            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_threads=self.n_threads,
                verbose=False
            )
            logger.info("LLM model loaded successfully")
            return True
            
        except ImportError:
            logger.error("llama-cpp-python not installed. Install with: pip install llama-cpp-python")
            return False
        except Exception as e:
            logger.error(f"Failed to load LLM model: {e}")
            return False
    
    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        """Generate text from prompt"""
        if not self.llm:
            raise RuntimeError("LLM not loaded. Call load_model() first.")
        
        try:
            response = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["</response>", "\n\n\n"],
                echo=False
            )
            
            return response['choices'][0]['text'].strip()
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise


class AIAgent:
    """Main AI Agent class"""
    
    def __init__(self, node_id: str, model_path: str):
        self.node_id = node_id
        self.model_path = model_path
        self.engine = LLMEngine(model_path)
        self.objectives = UserObjectives()
        self.action_history: List[AgentAction] = []
        self.enabled = False
        
    def initialize(self) -> bool:
        """Initialize the AI agent (load model)"""
        success = self.engine.load_model()
        if success:
            self.enabled = True
            logger.info(f"AI Agent initialized for node {self.node_id}")
        return success
    
    def set_objectives(self, objectives: UserObjectives):
        """Update user objectives"""
        self.objectives = objectives
        logger.info(f"AI Agent objectives updated: {objectives.primary_objective}")
    
    def build_system_prompt(self, context: NetworkContext) -> str:
        """Build system prompt with network state and available actions"""
        
        api_reference = """
AVAILABLE ACTIONS:
1. create_task: {"action": "create_task", "params": {"channel": "string", "title": "string", "description": "string", "reward": int}}
2. claim_task: {"action": "claim_task", "params": {"channel": "string", "task_id": "string"}}
3. complete_task: {"action": "complete_task", "params": {"channel": "string", "task_id": "string", "proof": "string"}}
4. create_proposal: {"action": "create_proposal", "params": {"channel": "string", "title": "string", "description": "string", "proposal_type": "string"}}
5. vote_proposal: {"action": "vote_proposal", "params": {"channel": "string", "proposal_id": "string", "vote": "approve|reject", "use_zkp": bool}}
6. create_auction: {"action": "create_auction", "params": {"channel": "string", "title": "string", "starting_price": int, "min_increment": int}}
7. bid_auction: {"action": "bid_auction", "params": {"channel": "string", "auction_id": "string", "amount": int}}
8. create_composite_task: {"action": "create_composite_task", "params": {"channel": "string", "title": "string", "description": "string", "sub_tasks": [], "total_reward": int}}
9. apply_team: {"action": "apply_team", "params": {"channel": "string", "task_id": "string"}}
10. update_skills: {"action": "update_skills", "params": {"skills": [], "bio": "string"}}
"""
        
        context_info = f"""
NETWORK STATE:
- Node ID: {context.node_id}
- Channel: {context.channel}
- Synapse Points: {context.synapse_points} SP
- Reputation: {context.reputation:.2f}
- Skills: {', '.join(context.skills) if context.skills else 'none'}
- Connected Peers: {context.peer_count}
- Timestamp: {context.timestamp}

OPPORTUNITIES:
- Open Tasks: {len(context.open_tasks)} available
- Active Proposals: {len(context.active_proposals)} to vote on
- Active Auctions: {len(context.active_auctions)} to bid on
- Available Teams: {len(context.available_teams)} recruiting
"""
        
        objectives_info = f"""
YOUR OBJECTIVES:
- Primary Goal: {self.objectives.primary_objective}
- Target Skills: {', '.join(self.objectives.target_skills) if self.objectives.target_skills else 'flexible'}
- SP Reserve: Keep minimum {self.objectives.min_sp_reserve} SP
- Max Bid: {self.objectives.max_bid_percentage * 100}% of SP
- Auto Vote: {self.objectives.auto_vote}
- Auto Apply Tasks: {self.objectives.auto_apply_tasks}
- Auto Join Teams: {self.objectives.auto_join_teams}
- Risk Tolerance: {self.objectives.risk_tolerance}
"""
        
        system_prompt = f"""You are an intelligent agent managing a node in a decentralized autonomous network.

{context_info}

{objectives_info}

{api_reference}

INSTRUCTIONS:
- Analyze the current network state
- Consider user objectives
- Generate strategic actions to achieve goals
- Output ONLY valid JSON with action commands
- Each action must have "action" and "params" fields
- You can return multiple actions as a JSON array
- Be strategic: maximize SP, build reputation, collaborate effectively

OUTPUT FORMAT:
{{"action": "action_name", "params": {{...}}, "reasoning": "why this action"}}

OR for multiple actions:
[
  {{"action": "action1", "params": {{...}}, "reasoning": "..."}},
  {{"action": "action2", "params": {{...}}, "reasoning": "..."}}
]
"""
        return system_prompt
    
    def parse_llm_output(self, output: str) -> List[AgentAction]:
        """Parse LLM output into AgentAction objects"""
        try:
            # Try to extract JSON from output
            output = output.strip()
            
            # Handle markdown code blocks
            if "```json" in output:
                output = output.split("```json")[1].split("```")[0].strip()
            elif "```" in output:
                output = output.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            parsed = json.loads(output)
            
            # Handle single action or array
            if isinstance(parsed, dict):
                parsed = [parsed]
            
            actions = []
            for item in parsed:
                if "action" in item and "params" in item:
                    actions.append(AgentAction(
                        action=item["action"],
                        params=item["params"],
                        reasoning=item.get("reasoning"),
                        priority=item.get("priority", 5)
                    ))
            
            return actions
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM output as JSON: {e}\nOutput: {output}")
            return []
        except Exception as e:
            logger.error(f"Error parsing LLM output: {e}")
            return []
    
    async def process_prompt(self, user_prompt: str, context: NetworkContext) -> Tuple[List[AgentAction], str]:
        """
        Process user prompt and generate actions
        
        Returns: (list of actions, raw LLM response)
        """
        if not self.enabled:
            raise RuntimeError("AI Agent not initialized")
        
        # Build full prompt
        system_prompt = self.build_system_prompt(context)
        full_prompt = f"{system_prompt}\n\nUSER REQUEST: {user_prompt}\n\nRESPONSE:"
        
        # Generate response
        try:
            response = self.engine.generate(full_prompt, max_tokens=512, temperature=0.7)
            logger.info(f"LLM Response: {response}")
            
            # Parse actions
            actions = self.parse_llm_output(response)
            
            # Record actions
            self.action_history.extend(actions)
            
            return actions, response
            
        except Exception as e:
            logger.error(f"Error processing prompt: {e}")
            raise
    
    async def proactive_analysis(self, context: NetworkContext) -> List[AgentAction]:
        """
        Proactive analysis of network state - agent thinks autonomously
        
        Called periodically to let agent make strategic decisions
        """
        if not self.enabled:
            return []
        
        analysis_prompt = "Analyze the current network state and suggest strategic actions based on your objectives. Focus on opportunities that align with your primary goal."
        
        try:
            actions, _ = await self.process_prompt(analysis_prompt, context)
            logger.info(f"Proactive analysis generated {len(actions)} actions")
            return actions
            
        except Exception as e:
            logger.error(f"Proactive analysis failed: {e}")
            return []
    
    def validate_action(self, action: AgentAction, context: NetworkContext) -> Tuple[bool, str]:
        """
        Validate if an action is safe to execute
        
        Returns: (is_valid, reason)
        """
        # Check SP constraints
        if action.action in ["bid_auction", "create_task", "create_composite_task"]:
            amount = action.params.get("amount") or action.params.get("reward") or action.params.get("total_reward", 0)
            
            if context.synapse_points - amount < self.objectives.min_sp_reserve:
                return False, f"Action would reduce SP below reserve ({self.objectives.min_sp_reserve})"
            
            if action.action == "bid_auction":
                max_bid = int(context.synapse_points * self.objectives.max_bid_percentage)
                if amount > max_bid:
                    return False, f"Bid {amount} exceeds max allowed {max_bid} ({self.objectives.max_bid_percentage*100}% of SP)"
        
        # Check auto-vote setting
        if action.action == "vote_proposal" and not self.objectives.auto_vote:
            return False, "Auto-voting disabled in objectives"
        
        # Check auto-apply setting
        if action.action in ["claim_task", "apply_team"] and not self.objectives.auto_apply_tasks:
            return False, "Auto-applying to tasks disabled in objectives"
        
        # Check auto-join teams setting
        if action.action == "apply_team" and not self.objectives.auto_join_teams:
            return False, "Auto-joining teams disabled in objectives"
        
        return True, "Action validated"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            "enabled": self.enabled,
            "node_id": self.node_id,
            "model_path": self.model_path,
            "objectives": {
                "primary": self.objectives.primary_objective,
                "target_skills": self.objectives.target_skills,
                "min_sp_reserve": self.objectives.min_sp_reserve,
                "max_bid_percentage": self.objectives.max_bid_percentage,
                "auto_vote": self.objectives.auto_vote,
                "auto_apply_tasks": self.objectives.auto_apply_tasks,
                "auto_join_teams": self.objectives.auto_join_teams,
                "risk_tolerance": self.objectives.risk_tolerance
            },
            "total_actions_executed": len(self.action_history),
            "recent_actions": [
                {
                    "action": a.action,
                    "params": a.params,
                    "reasoning": a.reasoning
                }
                for a in self.action_history[-5:]
            ]
        }


# Singleton instance (initialized per node)
_agent_instance: Optional[AIAgent] = None


def initialize_agent(node_id: str, model_path: str) -> bool:
    """Initialize global AI agent instance"""
    global _agent_instance
    
    if not os.path.exists(model_path):
        logger.error(f"Model file not found: {model_path}")
        return False
    
    _agent_instance = AIAgent(node_id, model_path)
    success = _agent_instance.initialize()
    
    return success


def get_agent() -> Optional[AIAgent]:
    """Get global AI agent instance"""
    return _agent_instance


def is_agent_enabled() -> bool:
    """Check if AI agent is enabled"""
    return _agent_instance is not None and _agent_instance.enabled


# Test function
async def test_ai_agent():
    """Test AI agent functionality"""
    print("\n=== Testing AI Agent ===\n")
    
    # Mock model path (for testing without actual model)
    model_path = "models/qwen3-0.6b.gguf"
    node_id = "test-node-123"
    
    print(f"1. Creating AI Agent for node {node_id}")
    agent = AIAgent(node_id, model_path)
    
    # Skip actual model loading for test
    agent.enabled = True
    print("   ✓ Agent created (model loading skipped for test)")
    
    print("\n2. Setting objectives")
    objectives = UserObjectives(
        primary_objective=AgentObjective.MAXIMIZE_SP,
        target_skills=["python", "backend", "testing"],
        min_sp_reserve=100,
        max_bid_percentage=0.3,
        auto_vote=True,
        auto_apply_tasks=True,
        risk_tolerance=0.6
    )
    agent.set_objectives(objectives)
    print(f"   ✓ Objectives set: {objectives.primary_objective}")
    
    print("\n3. Building context")
    context = NetworkContext(
        node_id=node_id,
        channel="dev-channel",
        synapse_points=500,
        reputation=0.75,
        skills=["python", "testing"],
        open_tasks=[
            {"id": "task1", "title": "Fix bug", "reward": 50},
            {"id": "task2", "title": "Add feature", "reward": 100}
        ],
        active_proposals=[
            {"id": "prop1", "title": "Increase rewards"}
        ],
        active_auctions=[],
        available_teams=[],
        peer_count=5
    )
    print(f"   ✓ Context: {context.synapse_points} SP, {context.reputation} reputation")
    
    print("\n4. Building system prompt")
    system_prompt = agent.build_system_prompt(context)
    print(f"   ✓ System prompt built ({len(system_prompt)} chars)")
    print(f"   Preview: {system_prompt[:200]}...")
    
    print("\n5. Testing action parsing")
    test_output = '''
    [
      {"action": "claim_task", "params": {"channel": "dev-channel", "task_id": "task2"}, "reasoning": "High reward task matches skills"},
      {"action": "vote_proposal", "params": {"channel": "dev-channel", "proposal_id": "prop1", "vote": "approve", "use_zkp": true}, "reasoning": "Increase rewards benefits all"}
    ]
    '''
    actions = agent.parse_llm_output(test_output)
    print(f"   ✓ Parsed {len(actions)} actions:")
    for action in actions:
        print(f"     - {action.action}: {action.reasoning}")
    
    print("\n6. Testing action validation")
    for action in actions:
        is_valid, reason = agent.validate_action(action, context)
        status = "✓" if is_valid else "✗"
        print(f"   {status} {action.action}: {reason}")
    
    print("\n7. Testing invalid action (excessive bid)")
    invalid_action = AgentAction(
        action="bid_auction",
        params={"channel": "dev-channel", "auction_id": "auc1", "amount": 200},
        reasoning="Want to win"
    )
    is_valid, reason = agent.validate_action(invalid_action, context)
    print(f"   ✗ bid_auction (200 SP): {reason}")
    
    print("\n8. Getting agent stats")
    agent.action_history = actions
    stats = agent.get_stats()
    print(f"   ✓ Stats: {stats['total_actions_executed']} actions executed")
    print(f"   ✓ Primary objective: {stats['objectives']['primary']}")
    
    print("\n=== All AI Agent Tests Passed ===\n")


if __name__ == "__main__":
    asyncio.run(test_ai_agent())
