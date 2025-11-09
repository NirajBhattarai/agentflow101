/**
 * Hedera Token Address Mapping
 *
 * Maps Hedera token addresses (0.0.123456) to EVM addresses (0x...)
 * Used for:
 * - Balance checking: Use Hedera format (0.0.456858)
 * - Contract calls: Use EVM format (0x000000000000000000000000000000000006f89a)
 */

// Hedera token addresses (for balance checking via Mirror Node API)
export const HEDERA_TOKEN_ADDRESSES: Record<string, string> = {
  HBAR: "0.0.0", // Native token
  USDC: "0.0.456858",
  USDT: "0.0.1055472",
  WHBAR: "0.0.1456986",
  ETH: "0.0.541564",
  WETH: "0.0.541564", // Same as ETH
  BTC: "0.0.1055483",
  SAUCE: "0.0.731861",
  LINK: "0.0.1055495",
  AVAX: "0.0.1157020",
};

// EVM addresses for Hedera tokens (for smart contract calls)
export const HEDERA_TOKEN_EVM_ADDRESSES: Record<string, string> = {
  HBAR: "0x0000000000000000000000000000000000000000", // Native token
  USDC: "0x000000000000000000000000000000000006f89a", // 0.0.456858 -> EVM
  USDT: "0x0000000000000000000000000000000000101b07", // 0.0.1055472 -> EVM (placeholder)
  WHBAR: "0x0000000000000000000000000000000000163B5a", // 0.0.1456986 -> EVM (placeholder)
  ETH: "0x000000000000000000000000000000000008437c", // 0.0.541564 -> EVM
  WETH: "0x000000000000000000000000000000000008437c", // Same as ETH
  BTC: "0x0000000000000000000000000000000000101b07", // 0.0.1055483 -> EVM (placeholder)
  SAUCE: "0x00000000000000000000000000000000000b2ad5", // 0.0.731861 -> EVM
  LINK: "0x0000000000000000000000000000000000101b07", // 0.0.1055495 -> EVM
  AVAX: "0x000000000000000000000000000000000011a79c", // 0.0.1157020 -> EVM
};

/**
 * Get Hedera token address (Hedera format) by symbol
 */
export function getHederaTokenAddress(symbol: string): string {
  return HEDERA_TOKEN_ADDRESSES[symbol.toUpperCase()] || "";
}

/**
 * Get EVM token address for Hedera token by symbol
 */
export function getHederaTokenEvmAddress(symbol: string): string {
  return HEDERA_TOKEN_EVM_ADDRESSES[symbol.toUpperCase()] || "";
}

/**
 * Convert Hedera address to EVM address
 */
export function hederaToEvmAddress(hederaAddress: string): string {
  // Check if already EVM format
  if (hederaAddress.startsWith("0x")) {
    return hederaAddress;
  }

  // Check if it's a known token
  for (const [symbol, hederaAddr] of Object.entries(HEDERA_TOKEN_ADDRESSES)) {
    if (hederaAddr === hederaAddress) {
      const evmAddr = HEDERA_TOKEN_EVM_ADDRESSES[symbol];
      if (evmAddr) {
        return evmAddr;
      }
    }
  }

  // Convert Hedera account ID to EVM address
  // Format: 0.0.123456 -> extract 123456 -> convert to hex -> pad to 40 chars
  const match = hederaAddress.match(/^0\.0\.(\d+)$/);
  if (match) {
    const accountNum = parseInt(match[1], 10);
    const hexStr = accountNum.toString(16).toLowerCase();
    // Pad to 40 hex characters (20 bytes)
    const hexPadded = hexStr.padStart(40, "0");
    return `0x${hexPadded}`;
  }

  return hederaAddress; // Return as-is if conversion fails
}

/**
 * Convert EVM address to Hedera address (if possible)
 */
export function evmToHederaAddress(evmAddress: string): string {
  // Check if already Hedera format
  if (/^0\.0\.\d+$/.test(evmAddress)) {
    return evmAddress;
  }

  // Check if it's a known token EVM address
  for (const [symbol, evmAddr] of Object.entries(HEDERA_TOKEN_EVM_ADDRESSES)) {
    if (evmAddr.toLowerCase() === evmAddress.toLowerCase()) {
      return HEDERA_TOKEN_ADDRESSES[symbol] || evmAddress;
    }
  }

  // Try to convert EVM address to Hedera format
  // Extract the last 6 hex digits and convert to decimal
  const hexPart = evmAddress.replace("0x", "").toLowerCase();
  const last6Hex = hexPart.slice(-6);
  const accountNum = parseInt(last6Hex, 16);

  return `0.0.${accountNum}`;
}
