/**
 * Shared Type Definitions
 *
 * This file contains all TypeScript interfaces and types used across
 * the DeFi agent components. Centralizing types makes them
 * easier to maintain and reuse.
 */

import { ActionRenderProps } from "@copilotkit/react-core";

// ============================================================================
// A2A Action Types
// ============================================================================

/**
 * Type for the send_message_to_a2a_agent action parameters
 * Used when the orchestrator sends tasks to A2A agents
 */
export type MessageActionRenderProps = ActionRenderProps<
  [
    {
      readonly name: "agentName";
      readonly type: "string";
      readonly description: "The name of the A2A agent to send the message to";
    },
    {
      readonly name: "task";
      readonly type: "string";
      readonly description: "The message to send to the A2A agent";
    },
  ]
>;

/**
 * Type for balance requirements action parameters
 * Used to gather essential balance query information at the start
 */
export type BalanceRequirementsActionRenderProps = ActionRenderProps<
  [
    {
      readonly name: "accountAddress";
      readonly type: "string";
      readonly description: "The account address to query (Hedera format: 0.0.123456 or EVM format: 0x...)";
    },
    {
      readonly name: "chain";
      readonly type: "string";
      readonly description: "The blockchain chain to query: hedera, polygon, or all";
    },
    {
      readonly name: "tokenAddress";
      readonly type: "string";
      readonly description: "Optional token address or symbol to query";
    },
  ]
>;

/**
 * Type for bridge requirements action parameters
 */
export type BridgeRequirementsActionRenderProps = ActionRenderProps<
  [
    {
      readonly name: "accountAddress";
      readonly type: "string";
      readonly description: "The account address to bridge from (Hedera format: 0.0.123456 or EVM format: 0x...)";
    },
    {
      readonly name: "sourceChain";
      readonly type: "string";
      readonly description: "Source chain: hedera or polygon";
    },
    {
      readonly name: "destinationChain";
      readonly type: "string";
      readonly description: "Destination chain: hedera or polygon";
    },
    {
      readonly name: "tokenSymbol";
      readonly type: "string";
      readonly description: "Token symbol to bridge (e.g., USDC, HBAR, MATIC)";
    },
    {
      readonly name: "amount";
      readonly type: "string";
      readonly description: "Amount to bridge (e.g., 100.0)";
    },
  ]
>;

// ============================================================================
// Agent Data Structures
// ============================================================================

/**
 * Token balance structure
 */
export interface TokenBalance {
  token_type: string;
  token_symbol: string;
  token_address: string;
  balance: string;
  balance_raw: string;
  decimals: number;
  chain?: string;
  error?: string;
}

/**
 * Complete balance data from Balance Agent
 * Structured JSON output from the ADK balance agent
 */
export interface BalanceData {
  type: string;
  chain: string;
  account_address: string;
  balances: TokenBalance[];
  total_usd_value: string;
  error?: string;
}

/**
 * Liquidity pair structure
 */
export interface LiquidityPair {
  pool_address: string;
  dex_name: string;
  token0: string;
  token1: string;
  tvl: string;
  volume_24h: string;
  reserves_token0: string;
  reserves_token1: string;
  fee_rate: string;
  chain?: string;
}

/**
 * Complete liquidity data from Liquidity Agent
 */
export interface LiquidityData {
  type: string;
  chain: string;
  pairs: LiquidityPair[];
  error?: string;
}

/**
 * Bridge transaction details
 */
export interface BridgeTransaction {
  source_chain: string;
  destination_chain: string;
  token_symbol: string;
  token_address: string;
  amount: string;
  bridge_fee: string;
  estimated_time: string;
  bridge_protocol: string;
  transaction_hash?: string | null;
  status: string;
}

/**
 * Bridge option (for comparison)
 */
export interface BridgeOption {
  bridge_protocol: string;
  bridge_fee: string;
  bridge_fee_usd: number; // For sorting
  estimated_time: string;
  min_amount?: string;
  max_amount?: string;
  is_recommended?: boolean;
}

/**
 * Balance check result for bridge
 */
export interface BridgeBalanceCheck {
  account_address: string;
  token_symbol: string;
  balance: string;
  balance_sufficient: boolean;
  required_amount: string;
}

/**
 * Complete bridge data from Bridge Agent
 */
export interface BridgeData {
  type: string;
  source_chain: string;
  destination_chain: string;
  token_symbol: string;
  amount: string;
  account_address?: string;
  balance_check?: BridgeBalanceCheck;
  bridge_options?: BridgeOption[];
  transaction?: BridgeTransaction;
  requires_confirmation?: boolean;
  confirmation_threshold?: number;
  amount_exceeds_threshold?: boolean;
  error?: string;
}

// ============================================================================
// Component Props
// ============================================================================

/**
 * Props for the main DeFiChat component
 * Callbacks to update parent component state with agent data
 */
export interface DeFiChatProps {
  onBalanceUpdate?: (data: BalanceData | null) => void;
  onLiquidityUpdate?: (data: LiquidityData | null) => void;
  onBridgeUpdate?: (data: BridgeData | null) => void;
}

/**
 * Agent styling configuration
 * Used to style agent badges with consistent colors and icons
 */
export interface AgentStyle {
  bgColor: string;
  textColor: string;
  borderColor: string;
  icon: string;
  framework: string;
}
