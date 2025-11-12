/**
 * Swap utility functions - Minimal router for executeSwap
 *
 * This file provides a minimal router for executeSwap.
 * All swap logic is in chain-specific files:
 * - hedera/swap-utils.ts for Hedera-specific logic
 * - evm/swap-utils.ts for EVM-compatible chains
 *
 * For better control, import directly from chain-specific files.
 */

import { ethers } from "ethers";
import * as hederaSwapUtils from "./hedera/swap-utils";
import * as evmSwapUtils from "./evm/swap-utils";
import * as hederaOps from "./hedera";
import * as evmOps from "./evm";

// Re-export chain-specific operations for convenience
export { hederaOps, evmOps };

// Chain type mapping
const CHAIN_TYPES: Record<string, "hedera" | "evm"> = {
  hedera: "hedera",
  polygon: "evm",
  ethereum: "evm",
  arbitrum: "evm",
  optimism: "evm",
  base: "evm",
};

/**
 * Execute swap transaction (chain-agnostic router)
 * Routes to chain-specific implementations
 */
export async function executeSwap(
  contract: ethers.Contract,
  functionName: string,
  params: any[],
  overrides: ethers.Overrides = {},
  chain?: string,
): Promise<ethers.TransactionResponse> {
  const chainType = CHAIN_TYPES[(chain || "evm").toLowerCase()] || "evm";

  if (chainType === "hedera") {
    return await hederaSwapUtils.executeSwap(contract, functionName, params, overrides);
  } else {
    return await evmSwapUtils.executeSwap(contract, functionName, params, overrides);
  }
}
