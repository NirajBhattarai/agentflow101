/**
 * Hedera Address Conversion Utilities
 *
 * Converts between Hedera format (0.0.xxxxx) and EVM format (0x...)
 */

/**
 * Convert Hedera format address (0.0.xxxxx) to EVM format (0x...)
 * Uses Hedera Mirror Node API to resolve HTS token addresses
 */
export async function convertHederaToEvmAddress(hederaAddress: string): Promise<string> {
  debugger;
  // If already EVM format, return checksummed
  if (hederaAddress.startsWith("0x")) {
    try {
      const { ethers } = await import("ethers");
      return ethers.utils.isAddress(hederaAddress)
        ? ethers.utils.getAddress(hederaAddress)
        : hederaAddress;
    } catch {
      return hederaAddress;
    }
  }

  // For Hedera native token (HBAR)
  if (hederaAddress === "0.0.0") {
    return "0x0000000000000000000000000000000000000000";
  }

  // For HTS tokens (0.0.xxxxx), resolve via Hedera Mirror Node
  if (hederaAddress.match(/^0\.0\.\d+$/)) {
    try {
      // Use Hedera Mirror Node API to get EVM address
      const mirrorNodeUrl = "https://mainnet-public.mirrornode.hedera.com";
      const response = await fetch(`${mirrorNodeUrl}/api/v1/tokens/${hederaAddress}`);

      if (response.ok) {
        const data = await response.json();
        const evmAddress = data.evm_address;
        if (evmAddress) {
          return evmAddress.toLowerCase();
        }
      }

      // Fallback: if mirror node doesn't have EVM address, return original
      // This might be a token that doesn't have an EVM equivalent
      console.warn(`Could not resolve EVM address for Hedera token ${hederaAddress}`);
      return hederaAddress;
    } catch (error) {
      console.error(`Error resolving Hedera address ${hederaAddress}:`, error);
      return hederaAddress;
    }
  }

  return hederaAddress;
}

/**
 * Check if an address is in Hedera format
 */
export function isHederaFormat(address: string): boolean {
  return address.match(/^0\.0\.\d+$/) !== null;
}

/**
 * Check if an address is in EVM format
 */
export function isEvmFormat(address: string): boolean {
  if (!address.startsWith("0x")) return false;
  try {
    const { ethers } = require("ethers");
    return ethers.utils.isAddress(address);
  } catch {
    return address.length === 42 && /^0x[a-fA-F0-9]{40}$/.test(address);
  }
}
