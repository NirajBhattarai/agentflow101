"""
Pool Calculator Client Service

Calls the Pool Calculator Agent to get optimal swap allocations using LLM reasoning.
"""

import json
from typing import Dict, Optional
from agents.pool_calculator.agent import PoolCalculatorAgent


async def get_optimal_allocations_from_pool_calculator(
    liquidity_data: Dict,
    total_amount: float,
    token_in: str,
    token_out: str,
    session_id: str = "swap_router_session",
) -> Optional[Dict]:
    """
    Call Pool Calculator Agent to get optimal swap allocations across chains.
    
    Args:
        liquidity_data: Liquidity data from multichain_liquidity agent
        total_amount: Total amount to swap
        token_in: Input token symbol
        token_out: Output token symbol
        session_id: Session ID
    
    Returns:
        Dictionary with recommended allocations, or None if failed
    """
    try:
        agent = PoolCalculatorAgent()
        
        # Build query for pool calculator
        query = f"""
Analyze pools and recommend optimal swap allocation for swapping {total_amount:,.0f} {token_in} to {token_out}.

Liquidity data from chains:
{json.dumps(liquidity_data, indent=2)}

Please:
1. Analyze pools from each chain
2. Test different allocation scenarios (e.g., 50/30/20, 60/25/15)
3. Consider price impact, liquidity depth, and gas costs
4. Return JSON with recommended_allocations in format:
{{
  "recommended_allocations": {{
    "ethereum": <amount>,
    "polygon": <amount>,
    "hedera": <amount>
  }},
  "total_output": <total_eth_received>,
  "average_price_impact": <impact_percent>,
  "reasoning": "<explanation>"
}}
"""
        
        response = await agent.invoke(query, session_id)
        
        # Try to extract JSON from response
        # The LLM might return JSON wrapped in markdown or text
        response_text = response.strip()
        
        # Try to find JSON in the response
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            try:
                result = json.loads(json_str)
                return result
            except json.JSONDecodeError:
                pass
        
        # If no JSON found, return None
        print(f"⚠️  Pool Calculator did not return valid JSON: {response[:200]}")
        return None
        
    except Exception as e:
        print(f"❌ Error calling Pool Calculator Agent: {e}")
        import traceback
        traceback.print_exc()
        return None

