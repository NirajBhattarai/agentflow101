/**
 * Hedera Address Conversion Utilities
 *
 * Converts between Hedera format (0.0.xxxxx) and EVM format (0x...)
 */

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
