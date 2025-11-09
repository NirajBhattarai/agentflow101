/**
 * Default values for forms and operations
 *
 * Centralized default configurations used across the application
 */

// Default tokens by chain (for swap forms)
export const DEFAULT_TOKENS: Record<string, { tokenIn: string; tokenOut: string }> = {
  hedera: { tokenIn: "HBAR", tokenOut: "USDC" },
  polygon: { tokenIn: "MATIC", tokenOut: "USDC" },
};

// Default slippage tolerance (%)
export const DEFAULT_SLIPPAGE_TOLERANCE = "0.5";

// Default network
export const DEFAULT_NETWORK = "mainnet";

// Default gas limits
export const DEFAULT_GAS_LIMITS: Record<string, number> = {
  hedera: 7_000_000,
  polygon: 15_000_000,
  ethereum: 15_000_000,
  arbitrum: 15_000_000,
  optimism: 15_000_000,
  base: 15_000_000,
};

// Default transaction deadline (minutes)
export const DEFAULT_TRANSACTION_DEADLINE_MINUTES = 20;

/**
 * Get default tokens for a chain
 */
export function getDefaultTokensForChain(chain: string): { tokenIn: string; tokenOut: string } {
  return DEFAULT_TOKENS[chain.toLowerCase()] || { tokenIn: "", tokenOut: "" };
}

/**
 * Get default gas limit for a chain
 */
export function getDefaultGasLimit(chain: string): number {
  return DEFAULT_GAS_LIMITS[chain.toLowerCase()] || 15_000_000;
}

/**
 * Calculate transaction deadline (seconds from now)
 */
export function getTransactionDeadline(
  minutes: number = DEFAULT_TRANSACTION_DEADLINE_MINUTES,
): number {
  return Math.floor(Date.now() / 1000) + minutes * 60;
}
