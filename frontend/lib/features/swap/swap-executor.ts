/**
 * Swap Executor - Main Router
 *
 * Routes swap execution to chain-specific implementations.
 * All chain-specific logic is in:
 * - hedera/swap-executor.ts for Hedera network
 * - evm/swap-executor.ts for EVM-compatible chains
 */

import { executeSwapHedera } from "./hedera/swap-executor";
import { executeSwapEVM } from "./evm/swap-executor";
import type { AppDispatch } from "@/lib/store";
import type { SwapTransaction, SwapExecutionResult, SwapExecutionCallbacks } from "./types";

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
 * Execute swap transaction
 * Routes to chain-specific implementation based on chain type
 */
export async function executeSwap(
  transaction: SwapTransaction,
  walletClient: any, // WalletClient from wagmi/viem
  address: string,
  dispatch: AppDispatch,
  callbacks?: SwapExecutionCallbacks,
): Promise<SwapExecutionResult> {
  const chain = transaction.chain || "hedera";
  const chainType = getChainType(chain);

  if (chainType === "hedera") {
    return await executeSwapHedera(transaction, walletClient, address, dispatch, callbacks);
  } else {
    return await executeSwapEVM(transaction, walletClient, address, dispatch, callbacks);
  }
}

// Re-export types for convenience
export type { SwapTransaction, SwapExecutionResult, SwapExecutionCallbacks } from "./types";
