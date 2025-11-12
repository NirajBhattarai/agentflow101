/**
 * Bridge Executor - Main Router
 *
 * Routes bridge execution to chain-specific implementations.
 * All chain-specific logic is in:
 * - hedera/bridge-executor.ts for Hedera network
 * - evm/bridge-executor.ts for EVM-compatible chains
 */

import { executeBridgeHedera } from "./hedera/bridge-executor";
import { executeBridgeEVM } from "./evm/bridge-executor";
import type { AppDispatch } from "@/lib/store";
import type { BridgeTransaction, BridgeExecutionResult, BridgeExecutionCallbacks } from "./types";

// Chain type mapping helper
const CHAIN_TYPES: Record<string, "hedera" | "evm"> = {
  hedera: "hedera",
  polygon: "evm",
  ethereum: "evm",
  arbitrum: "evm",
  optimism: "evm",
  base: "evm",
};

function getChainType(chain: string): "hedera" | "evm" {
  return CHAIN_TYPES[chain.toLowerCase()] || "evm";
}

/**
 * Execute bridge transaction
 * Routes to chain-specific implementation based on source chain type
 */
export async function executeBridge(
  transaction: BridgeTransaction,
  walletClient: any, // WalletClient from wagmi/viem
  address: string,
  dispatch: AppDispatch,
  callbacks?: BridgeExecutionCallbacks,
): Promise<BridgeExecutionResult> {
  const sourceChain = transaction.source_chain || "hedera";
  const chainType = getChainType(sourceChain);

  console.log(`🌉 Routing bridge execution to ${chainType} executor for chain: ${sourceChain}`);

  if (chainType === "hedera") {
    return await executeBridgeHedera(transaction, walletClient, address, dispatch, callbacks);
  } else {
    return await executeBridgeEVM(transaction, walletClient, address, dispatch, callbacks);
  }
}

// Re-export types for convenience
export type { BridgeTransaction, BridgeExecutionResult, BridgeExecutionCallbacks };
