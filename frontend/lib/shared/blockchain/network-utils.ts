/**
 * Network utilities for chain switching and validation
 */

// Chain ID mappings
export const CHAIN_IDS: Record<string, number> = {
  polygon: 137, // Polygon Mainnet
  ethereum: 1, // Ethereum Mainnet
  arbitrum: 42161, // Arbitrum One
  optimism: 10, // Optimism
  base: 8453, // Base
  hedera: 295, // Hedera (for reference, but Hedera uses different connection method)
};

/**
 * Get chain ID for a chain name
 */
export function getChainId(chain: string): number | null {
  return CHAIN_IDS[chain.toLowerCase()] || null;
}

/**
 * Get chain name from chain ID
 */
export function getChainName(chainId: number): string | null {
  for (const [name, id] of Object.entries(CHAIN_IDS)) {
    if (id === chainId) {
      return name;
    }
  }
  return null;
}

/**
 * Check if chain requires network switching (EVM chains only)
 */
export function requiresNetworkSwitch(chain: string): boolean {
  return chain.toLowerCase() !== "hedera" && getChainId(chain) !== null;
}
