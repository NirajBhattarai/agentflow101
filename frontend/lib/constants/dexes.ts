/**
 * DEX and Router configurations
 *
 * DEX router addresses and configurations for different chains
 */

export interface DexConfig {
  name: string;
  routerAddress: string;
  routerAddressHedera?: string; // Hedera format address (0.0.123456)
  factoryAddress?: string;
  defaultFeePercent?: number;
}

// Polygon DEX configurations
export const POLYGON_DEX_CONFIG: Record<string, DexConfig> = {
  quickswap: {
    name: "QuickSwap",
    routerAddress: "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff", // QuickSwap Router V2
    factoryAddress: "0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32",
    defaultFeePercent: 0.3,
  },
  uniswap: {
    name: "Uniswap V3",
    routerAddress: "0xE592427A0AEce92De3Edee1F18E0157C05861564",
    factoryAddress: "0x1F98431c8aD98523631AE4a59f267346ea31F984",
    defaultFeePercent: 0.3,
  },
};

// Hedera DEX configurations
export const HEDERA_DEX_CONFIG: Record<string, DexConfig> = {
  saucerswap: {
    name: "SaucerSwap",
    routerAddress: "0x00000000000000000000000000000000006715e6", // Mainnet router EVM address
    routerAddressHedera: "0.0.6755814", // Mainnet router Hedera address
    factoryAddress: "0x0000000000000000000000000000000000000000", // TODO: Add actual factory
    defaultFeePercent: 0.3,
  },
  heliswap: {
    name: "HeliSwap",
    routerAddress: "0x0000000000000000000000000000000000000000", // TODO: Add actual router
    factoryAddress: "0x0000000000000000000000000000000000000000", // TODO: Add actual factory
    defaultFeePercent: 0.3,
  },
};

// Chain-specific DEX configurations
export const CHAIN_DEX_CONFIG: Record<string, Record<string, DexConfig>> = {
  polygon: POLYGON_DEX_CONFIG,
  hedera: HEDERA_DEX_CONFIG,
};

// Default DEX by chain
export const DEFAULT_DEX: Record<string, string> = {
  polygon: "quickswap",
  hedera: "saucerswap",
};

/**
 * Get DEX configuration for a chain and optional DEX name
 */
export function getDexConfig(chain: string, dexName?: string): DexConfig | null {
  const chainLower = chain.toLowerCase();
  const dexConfigs = CHAIN_DEX_CONFIG[chainLower];

  if (!dexConfigs) {
    return null;
  }

  if (dexName) {
    const dexLower = dexName.toLowerCase();
    // Try to find matching DEX
    for (const [key, config] of Object.entries(dexConfigs)) {
      if (key.toLowerCase() === dexLower || config.name.toLowerCase() === dexLower) {
        return config;
      }
    }
    return null;
  }

  // Return default DEX if no name specified
  const defaultDex = DEFAULT_DEX[chainLower];
  if (defaultDex && dexConfigs[defaultDex]) {
    return dexConfigs[defaultDex];
  }

  // Return first available DEX as fallback
  if (dexConfigs) {
    return Object.values(dexConfigs)[0];
  }

  return null;
}

/**
 * Get router address for a chain and optional DEX name
 */
export function getRouterAddress(
  chain: string,
  dexName?: string,
  useHederaFormat: boolean = false,
): string {
  const config = getDexConfig(chain, dexName);
  if (!config) {
    return "";
  }

  // For Hedera, optionally return Hedera format address
  if (chain.toLowerCase() === "hedera" && useHederaFormat && config.routerAddressHedera) {
    return config.routerAddressHedera;
  }

  return config.routerAddress;
}

// Re-export SaucerSwap router address for convenience (backward compatibility)
export const SAUCERSWAP_ROUTER_ADDRESS = HEDERA_DEX_CONFIG.saucerswap.routerAddress;

// Wrapped HBAR address on Hedera (for native HBAR swaps)
export const WHBAR_ADDRESS = "0.0.1456986"; // WHBAR on Hedera
export const WHBAR_ADDRESS_EVM = "0x0000000000000000000000000000000000163B5a"; // WHBAR EVM address
