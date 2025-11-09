# Parallel Agents Guide for Swap Agent

Based on [Google ADK Parallel Agents Documentation](https://google.github.io/adk-docs/agents/workflow-agents/parallel-agents/#independent-execution-and-state-management)

## Overview

The `ParallelAgent` executes sub-agents **concurrently**, dramatically speeding up workflows where tasks can be performed independently. This is perfect for:

- Fetching swap quotes from multiple DEXes simultaneously
- Checking balances across multiple chains in parallel
- Getting token addresses for multiple tokens concurrently

## Key Concepts

### 1. Independent Execution
- Sub-agents run **independently** - no automatic sharing of conversation history or state
- Each sub-agent operates in its own execution branch
- Results are collected after all agents complete

### 2. When to Use ParallelAgent
✅ **Use when:**
- Tasks are independent (no dependencies between them)
- Tasks are resource-intensive (API calls, blockchain queries)
- Speed is a priority
- Tasks can be performed concurrently

❌ **Don't use when:**
- Tasks depend on each other's results
- Shared state is required during execution
- Sequential processing is necessary

## Current Swap Agent Architecture

Currently, the swap agent:
1. Extracts swap parameters (sequential)
2. Gets token addresses (sequential)
3. Fetches swap options from DEXes (sequential - could be parallel!)
4. Checks balance (sequential)
5. Executes swap (sequential)

## Potential Parallel Agent Applications

### Use Case 1: Fetching Swap Quotes from Multiple DEXes

**Current (Sequential):**
```python
# Sequential - slow
saucerswap_quote = get_swap_hedera(..., dex_name="SaucerSwap")
heliswap_quote = get_swap_hedera(..., dex_name="HeliSwap")
quickswap_quote = get_swap_polygon(..., dex_name="QuickSwap")
```

**With ParallelAgent (Concurrent):**
```python
# Note: Check actual import path in your Google ADK version
# Common paths:
# from google.adk.agents.parallel_agent import ParallelAgent
# OR
# from google.adk.agents import ParallelAgent
# OR
# from google.adk.workflow.parallel_agent import ParallelAgent

from google.adk.agents.llm_agent import LlmAgent

# Create sub-agents for each DEX
saucerswap_agent = LlmAgent(
    name="SaucerSwapQuoteAgent",
    model=model_name,
    instruction="Get swap quote from SaucerSwap DEX",
    tools=[get_swap_hedera_tool],
    output_key="saucerswap_quote"
)

heliswap_agent = LlmAgent(
    name="HeliSwapQuoteAgent",
    model=model_name,
    instruction="Get swap quote from HeliSwap DEX",
    tools=[get_swap_hedera_tool],
    output_key="heliswap_quote"
)

# Create parallel agent
parallel_quote_agent = ParallelAgent(
    name="MultiDEXQuoteAgent",
    sub_agents=[saucerswap_agent, heliswap_agent],
    description="Fetches quotes from multiple DEXes in parallel"
)

# Execute - all DEXes queried simultaneously!
results = await runner.run_async(
    user_id=user_id,
    session_id=session_id,
    message=f"Get quotes for {amount_in} {token_in} to {token_out}"
)
```

**Benefits:**
- 3x faster (if 3 DEXes queried)
- Better user experience (faster response)
- All quotes available at once for comparison

### Use Case 2: Checking Balances Across Multiple Chains

**Current (Sequential):**
```python
# Sequential - slow
hedera_balance = get_balance_hedera(account_address, token_address)
polygon_balance = get_balance_polygon(account_address, token_address)
```

**With ParallelAgent (Concurrent):**
```python
# Create balance check agents
hedera_balance_agent = LlmAgent(
    name="HederaBalanceAgent",
    model=model_name,
    instruction="Get balance from Hedera chain",
    tools=[get_balance_hedera],
    output_key="hedera_balance"
)

polygon_balance_agent = LlmAgent(
    name="PolygonBalanceAgent",
    model=model_name,
    instruction="Get balance from Polygon chain",
    tools=[get_balance_polygon],
    output_key="polygon_balance"
)

# Parallel execution
parallel_balance_agent = ParallelAgent(
    name="MultiChainBalanceAgent",
    sub_agents=[hedera_balance_agent, polygon_balance_agent]
)

# Execute - both chains queried simultaneously!
results = await runner.run_async(...)
```

### Use Case 3: Getting Token Addresses for Multiple Tokens

**Current (Sequential):**
```python
# Sequential
token1_address = get_token_address_for_chain("hedera", "USDC")
token2_address = get_token_address_for_chain("hedera", "HBAR")
token3_address = get_token_address_for_chain("hedera", "USDT")
```

**With ParallelAgent (Concurrent):**
```python
# Create address lookup agents
usdc_agent = LlmAgent(
    name="USDCAddressAgent",
    tools=[get_token_address_for_chain],
    output_key="usdc_address"
)

hbar_agent = LlmAgent(
    name="HBARAddressAgent",
    tools=[get_token_address_for_chain],
    output_key="hbar_address"
)

# Parallel execution
parallel_address_agent = ParallelAgent(
    sub_agents=[usdc_agent, hbar_agent]
)
```

## Implementation Example: Multi-DEX Quote Fetcher

Here's a complete example of how to implement parallel DEX quote fetching:

```python
# Note: Import paths may vary by ADK version - check your installed package
# Try these import paths:
# from google.adk.agents.parallel_agent import ParallelAgent
# from google.adk.agents.sequential_agent import SequentialAgent
# OR
# from google.adk.workflow import ParallelAgent, SequentialAgent

from google.adk.agents.llm_agent import LlmAgent

def _build_parallel_quote_agent(self) -> ParallelAgent:
    """Build a parallel agent that fetches quotes from multiple DEXes."""
    
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    # Sub-agent 1: SaucerSwap
    saucerswap_agent = LlmAgent(
        name="SaucerSwapQuoteAgent",
        model=model_name,
        instruction="""
        Get swap quote from SaucerSwap DEX for Hedera chain.
        Use get_swap_hedera tool with dex_name="SaucerSwap".
        Return the quote as JSON.
        """,
        tools=[get_swap_hedera],
        output_key="saucerswap_quote"
    )
    
    # Sub-agent 2: HeliSwap
    heliswap_agent = LlmAgent(
        name="HeliSwapQuoteAgent",
        model=model_name,
        instruction="""
        Get swap quote from HeliSwap DEX for Hedera chain.
        Use get_swap_hedera tool with dex_name="HeliSwap".
        Return the quote as JSON.
        """,
        tools=[get_swap_hedera],
        output_key="heliswap_quote"
    )
    
    # Create parallel agent
    parallel_quote_agent = ParallelAgent(
        name="MultiDEXQuoteFetcher",
        sub_agents=[saucerswap_agent, heliswap_agent],
        description="Fetches quotes from multiple DEXes concurrently"
    )
    
    return parallel_quote_agent

# Usage in swap execution
async def _get_swap_options_parallel(
    self,
    chain: str,
    token_in_symbol: str,
    token_out_symbol: str,
    amount_in: str,
    account_address: str,
    slippage_tolerance: float
) -> list[SwapOption]:
    """Get swap options from multiple DEXes in parallel."""
    
    # Create parallel quote agent
    parallel_agent = self._build_parallel_quote_agent()
    
    # Create runner
    runner = Runner(
        app_name="parallel_quote_fetcher",
        agent=parallel_agent,
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )
    
    # Execute parallel queries
    query = f"Get swap quotes for {amount_in} {token_in_symbol} to {token_out_symbol} on {chain}"
    result = await runner.run_async(
        user_id=self._user_id,
        session_id=session_id,
        message=query
    )
    
    # Extract results from state
    # Results are stored in state with output_key names
    saucerswap_quote = result.state.get("saucerswap_quote")
    heliswap_quote = result.state.get("heliswap_quote")
    
    # Process and return swap options
    options = []
    if saucerswap_quote:
        options.append(self._parse_quote_to_option(saucerswap_quote, "SaucerSwap"))
    if heliswap_quote:
        options.append(self._parse_quote_to_option(heliswap_quote, "HeliSwap"))
    
    return options
```

## State Management

**Important:** Parallel agents don't share state during execution. To collect results:

1. **Use `output_key`** - Each sub-agent stores its result in state with a unique key
2. **Access state after completion** - Results are available in the final state object
3. **Post-process results** - Combine results from all sub-agents after parallel execution

```python
# Each sub-agent stores result with output_key
saucerswap_agent = LlmAgent(
    ...
    output_key="saucerswap_quote"  # Stores result here
)

# After parallel execution, access state
results = await runner.run_async(...)
saucerswap_result = results.state.get("saucerswap_quote")
heliswap_result = results.state.get("heliswap_quote")
```

## Combining with SequentialAgent

You can combine ParallelAgent with SequentialAgent for complex workflows:

```python
from google.adk.agents.sequential_agent import SequentialAgent

# Step 1: Parallel quote fetching
parallel_quote_agent = ParallelAgent(
    sub_agents=[saucerswap_agent, heliswap_agent]
)

# Step 2: Balance check (sequential, depends on account)
balance_agent = LlmAgent(
    name="BalanceCheckAgent",
    tools=[get_balance_hedera],
    output_key="balance_result"
)

# Step 3: Best quote selector (sequential, depends on quotes)
selector_agent = LlmAgent(
    name="BestQuoteSelector",
    instruction="Select best quote from available options",
    output_key="selected_quote"
)

# Create sequential pipeline
swap_pipeline = SequentialAgent(
    name="SwapPipeline",
    sub_agents=[
        parallel_quote_agent,  # Step 1: Get quotes in parallel
        balance_agent,         # Step 2: Check balance
        selector_agent         # Step 3: Select best quote
    ]
)
```

## Performance Benefits

**Before (Sequential):**
- SaucerSwap: 500ms
- HeliSwap: 500ms
- QuickSwap: 500ms
- **Total: 1500ms**

**After (Parallel):**
- All DEXes queried simultaneously: 500ms
- **Total: 500ms** (3x faster!)

## Best Practices

1. **Use for independent tasks** - Only parallelize tasks that don't depend on each other
2. **Set unique output_key** - Each sub-agent should have a unique output_key
3. **Handle failures gracefully** - Some sub-agents may fail, handle partial results
4. **Combine with SequentialAgent** - Use SequentialAgent to orchestrate parallel and sequential steps
5. **Monitor performance** - Measure actual speedup to ensure parallelization is beneficial

## Implementation Checklist

Before implementing parallel agents:

1. **Check ADK Version** - Ensure you have ADK Python v0.1.0+ (required for ParallelAgent)
   ```bash
   pip show google-adk
   # OR
   uv pip show google-adk
   ```

2. **Verify Import Path** - Test the import:
   ```python
   # Try these import paths:
   try:
       from google.adk.agents.parallel_agent import ParallelAgent
   except ImportError:
       try:
           from google.adk.workflow.parallel_agent import ParallelAgent
       except ImportError:
           from google.adk.agents import ParallelAgent
   ```

3. **Test Basic Example** - Start with a simple parallel agent to verify it works

4. **Measure Performance** - Compare sequential vs parallel execution times

5. **Handle Errors** - Implement error handling for partial failures

## Current Limitations

- The orchestrator currently calls agents sequentially (see `ORCHESTRATOR_INSTRUCTION`)
- Parallel agents require ADK v0.1.0+ (check your version)
- State management between parallel agents requires careful design

## Next Steps

1. **Upgrade ADK** (if needed):
   ```bash
   uv pip install --upgrade google-adk
   ```

2. **Test Import**:
   ```python
   from google.adk.agents.parallel_agent import ParallelAgent
   ```

3. **Start Small** - Implement parallel DEX quote fetching first

4. **Measure Impact** - Compare performance before/after

## References

- [Google ADK Parallel Agents Documentation](https://google.github.io/adk-docs/agents/workflow-agents/parallel-agents/#independent-execution-and-state-management)
- [Parallel Web Research Example](https://google.github.io/adk-docs/agents/workflow-agents/parallel-agents/#full-example-parallel-web-research)
- [ADK Python API Reference](https://google.github.io/adk-docs/reference/api-reference/python-adk/)

