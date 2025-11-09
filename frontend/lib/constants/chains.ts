/**
 * Chain configurations and options
 *
 * Chain-specific settings and UI options
 */

export interface ChainOption {
  value: string;
  label: string;
  icon: string;
}

// Chain options for forms (with "all" option for some forms)
export const CHAIN_OPTIONS: ChainOption[] = [
  { value: "hedera", label: "Hedera", icon: "🔷" },
  { value: "polygon", label: "Polygon", icon: "🟣" },
];

// Chain options with "all" option (for balance and liquidity forms)
export const CHAIN_OPTIONS_WITH_ALL: ChainOption[] = [
  { value: "hedera", label: "Hedera", icon: "🔷" },
  { value: "polygon", label: "Polygon", icon: "🟣" },
  { value: "all", label: "All", icon: "🌐" },
];

// RPC URLs by chain and network
export const RPC_URLS: Record<string, Record<string, string>> = {
  polygon: {
    mainnet: "https://polygon-rpc.com",
    testnet: "https://rpc-mumbai.maticvigil.com",
  },
  hedera: {
    mainnet: "https://mainnet.hashio.io/api",
    testnet: "https://testnet.hashio.io/api",
  },
};

// Explorer URLs by chain and network
export const EXPLORER_URLS: Record<string, Record<string, string>> = {
  polygon: {
    mainnet: "https://polygonscan.com",
    testnet: "https://mumbai.polygonscan.com",
  },
  hedera: {
    mainnet: "https://hashscan.io/mainnet",
    testnet: "https://hashscan.io/testnet",
  },
};

/**
 * Get RPC URL for a chain and network
 */
export function getRpcUrl(chain: string, network: string = "mainnet"): string {
  return RPC_URLS[chain.toLowerCase()]?.[network.toLowerCase()] || "";
}

/**
 * Get explorer URL for a chain and network
 */
export function getExplorerUrl(chain: string, network: string = "mainnet"): string {
  return EXPLORER_URLS[chain.toLowerCase()]?.[network.toLowerCase()] || "";
}

/**
 * Get transaction explorer URL
 */
export function getTransactionUrl(
  chain: string,
  txHash: string,
  network: string = "mainnet",
): string {
  const baseUrl = getExplorerUrl(chain, network);
  return `${baseUrl}/transaction/${txHash}`;
}
