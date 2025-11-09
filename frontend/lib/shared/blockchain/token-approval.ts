/**
 * Token approval utilities (chain-agnostic wrapper)
 *
 * Delegates to chain-specific implementations:
 * - hedera/token-approval.ts for Hedera
 * - evm/token-approval.ts for EVM chains
 */

import { ethers } from "ethers";
import { getTokenDecimals as getTokenDecimalsHedera } from "./hedera/token-approval";
import { getTokenDecimals as getTokenDecimalsEvm } from "./evm/token-approval";
import { checkTokenApproval as checkTokenApprovalHedera } from "./hedera/token-approval";
import { checkTokenApproval as checkTokenApprovalEvm } from "./evm/token-approval";
import { approveToken as approveTokenHedera } from "./hedera/token-approval";
import { approveToken as approveTokenEvm } from "./evm/token-approval";
import { ensureTokenApproval as ensureTokenApprovalHedera } from "./hedera/token-approval";
import { ensureTokenApproval as ensureTokenApprovalEvm } from "./evm/token-approval";

/**
 * Get chain type helper
 */
function getChainType(chain?: string): "hedera" | "evm" {
  if (!chain) return "evm";
  return chain.toLowerCase() === "hedera" ? "hedera" : "evm";
}

/**
 * Get token decimals (chain-agnostic)
 */
export async function getTokenDecimals(
  provider: ethers.Provider,
  tokenAddress: string,
  chain?: string,
): Promise<number> {
  const chainType = getChainType(chain);

  if (chainType === "hedera") {
    return await getTokenDecimalsHedera(provider, tokenAddress);
  } else {
    return await getTokenDecimalsEvm(provider, tokenAddress);
  }
}

/**
 * Check if token approval is needed (chain-agnostic)
 */
export async function checkTokenApproval(
  provider: ethers.Provider,
  tokenAddress: string,
  owner: string,
  spender: string,
  amount: bigint,
  chain?: string,
): Promise<{
  needsApproval: boolean;
  currentAllowance: bigint;
  sufficient: boolean;
}> {
  const chainType = getChainType(chain);

  if (chainType === "hedera") {
    return await checkTokenApprovalHedera(provider, tokenAddress, owner, spender, amount);
  } else {
    return await checkTokenApprovalEvm(provider, tokenAddress, owner, spender, amount);
  }
}

/**
 * Approve token spending (chain-agnostic)
 */
export async function approveToken(
  signer: ethers.Signer,
  tokenAddress: string,
  spender: string,
  amount: bigint,
  chain?: string,
): Promise<ethers.TransactionResponse> {
  const chainType = getChainType(chain);

  if (chainType === "hedera") {
    return await approveTokenHedera(signer, tokenAddress, spender, amount);
  } else {
    return await approveTokenEvm(signer, tokenAddress, spender, amount);
  }
}

/**
 * Check and approve token if needed (chain-agnostic)
 */
export async function ensureTokenApproval(
  provider: ethers.Provider,
  signer: ethers.Signer,
  tokenAddress: string,
  owner: string,
  spender: string,
  amount: bigint,
  chain?: string,
): Promise<boolean> {
  const chainType = getChainType(chain);

  if (chainType === "hedera") {
    return await ensureTokenApprovalHedera(provider, signer, tokenAddress, owner, spender, amount);
  } else {
    return await ensureTokenApprovalEvm(provider, signer, tokenAddress, owner, spender, amount);
  }
}
