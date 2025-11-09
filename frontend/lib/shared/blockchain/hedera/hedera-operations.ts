/**
 * Hedera-specific operations
 *
 * Hedera uses different mechanisms than EVM chains:
 * - Mirror Node API (REST) instead of RPC calls
 * - Account IDs (0.0.123456) instead of EVM addresses
 * - Tinybars (1 HBAR = 100,000,000 tinybars) instead of wei
 * - Token addresses in Hedera format (0.0.456858) instead of hex
 * - Limited EVM compatibility (Hedera doesn't fully support EVM)
 */

import {
  getHederaTokenAddress,
  getHederaTokenEvmAddress,
  evmToHederaAddress,
} from "./hedera-token-map";

// Hedera Mirror Node API endpoints
const HEDERA_MAINNET_API = "https://mainnet-public.mirrornode.hedera.com";
const HEDERA_TESTNET_API = "https://testnet.mirrornode.hedera.com";

/**
 * Get Hedera API base URL based on network
 */
function getHederaApiBase(network: string = "mainnet"): string {
  return network.toLowerCase() === "testnet" ? HEDERA_TESTNET_API : HEDERA_MAINNET_API;
}

/**
 * Resolve Hedera account ID from EVM address or Hedera account ID
 * Hedera accounts can be represented as:
 * - Hedera format: 0.0.123456
 * - EVM format: 0x...
 */
export async function resolveHederaAccountId(
  identifier: string,
  network: string = "mainnet",
): Promise<string> {
  identifier = identifier.trim();

  // If already in Hedera format, return as-is
  if (/^0\.0\.\d+$/.test(identifier)) {
    return identifier;
  }

  // If EVM address, resolve via Mirror Node
  if (identifier.startsWith("0x") && identifier.length === 42) {
    const apiBase = getHederaApiBase(network);
    const response = await fetch(`${apiBase}/api/v1/accounts/${identifier}`);

    if (response.ok) {
      const data = await response.json();
      const accountId = data.account || data.account_id;
      if (accountId) {
        return accountId;
      }
    }

    throw new Error(`Could not resolve Hedera account ID from EVM address: ${identifier}`);
  }

  throw new Error(`Invalid Hedera account identifier: ${identifier}`);
}

/**
 * Fetch HBAR balance using Hedera Mirror Node API
 */
export async function fetchHbarBalance(
  accountId: string,
  network: string = "mainnet",
): Promise<{ balance: string; balanceRaw: string }> {
  const apiBase = getHederaApiBase(network);
  const response = await fetch(`${apiBase}/api/v1/accounts/${accountId}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch HBAR balance: ${response.statusText}`);
  }

  const data = await response.json();
  const balanceTinybar = data.balance?.balance || 0;

  // Convert tinybars to HBAR (1 HBAR = 100,000,000 tinybars)
  const balanceHbar = balanceTinybar / 100_000_000;

  return {
    balance: balanceHbar.toFixed(8),
    balanceRaw: balanceTinybar.toString(),
  };
}

/**
 * Fetch token balance using Hedera Mirror Node API
 * If tokenAddress is provided, returns balance for that specific token
 * If not provided, returns balances for all known tokens the account holds
 */
export async function fetchTokenBalance(
  accountId: string,
  tokenAddress: string,
  network: string = "mainnet",
): Promise<{ balance: string; balanceRaw: string; decimals: number; symbol: string }> {
  const apiBase = getHederaApiBase(network);
  const response = await fetch(`${apiBase}/api/v1/accounts/${accountId}/tokens`);

  if (!response.ok) {
    throw new Error(`Failed to fetch token balance: ${response.statusText}`);
  }

  const data = await response.json();
  const tokens = data.tokens || [];

  // Convert tokenAddress to Hedera format if it's a symbol
  let hederaTokenAddress = tokenAddress;
  if (tokenAddress && !tokenAddress.startsWith("0.") && !tokenAddress.startsWith("0x")) {
    // Might be a symbol, try to look it up
    const mappedAddress = getHederaTokenAddress(tokenAddress);
    if (mappedAddress) {
      hederaTokenAddress = mappedAddress;
    }
  }

  // Find the token in the list
  const token = tokens.find((t: any) => {
    const tokenId = t.token_id;
    // Match by exact token_id or by checking if it's in our known token list
    return tokenId === hederaTokenAddress || tokenId === tokenAddress;
  });

  if (!token) {
    // Token not found, return zero balance
    return {
      balance: "0",
      balanceRaw: "0",
      decimals: 8, // Default Hedera token decimals
      symbol: "UNKNOWN",
    };
  }

  const balanceRaw = parseInt(token.balance || "0", 10);
  const decimals = token.decimals || 8; // Hedera tokens typically have 6-8 decimals
  const balance = (balanceRaw / Math.pow(10, decimals)).toFixed(decimals);

  return {
    balance,
    balanceRaw: balanceRaw.toString(),
    decimals,
    symbol: token.symbol || "UNKNOWN",
  };
}

/**
 * Parse token amount for Hedera (tinybars)
 * Hedera uses tinybars: 1 HBAR = 100,000,000 tinybars
 * Delegates to hbar-operations.ts for HBAR-specific logic
 */
export function parseHederaAmount(amount: string, decimals: number = 8): bigint {
  const amountFloat = parseFloat(amount);
  if (decimals === 8) {
    // For HBAR - use dedicated HBAR operations
    // Import synchronously since this is a sync function
    const hbarOps = require("./hbar-operations");
    return hbarOps.parseHbar(amount);
  } else {
    // For tokens with different decimals
    return BigInt(Math.floor(amountFloat * Math.pow(10, decimals)));
  }
}

/**
 * Format token amount for Hedera (from tinybars)
 * Delegates to hbar-operations.ts for HBAR-specific logic
 */
export function formatHederaAmount(amount: bigint, decimals: number = 8): string {
  if (decimals === 8) {
    // For HBAR - use dedicated HBAR operations
    // Import synchronously since this is a sync function
    const hbarOps = require("./hbar-operations");
    return hbarOps.formatHbar(amount);
  } else {
    // For tokens with different decimals
    return (Number(amount) / Math.pow(10, decimals)).toFixed(decimals);
  }
}

/**
 * Check if address is native HBAR
 */
export function isHederaNative(address: string): boolean {
  return (
    address === "0.0.0" || address.toLowerCase() === "0x0000000000000000000000000000000000000000"
  );
}

/**
 * Convert Hedera account ID to EVM address format (if possible)
 * Note: Hedera has limited EVM support, this may not always work
 */
export function hederaAccountToEvm(accountId: string): string {
  // Extract the account number from 0.0.123456 format
  const match = accountId.match(/^0\.0\.(\d+)$/);
  if (match) {
    const accountNum = parseInt(match[1], 10);
    // Convert to hex and pad to 20 bytes (40 hex chars)
    const hex = accountNum.toString(16).padStart(40, "0");
    return `0x${hex}`;
  }
  return accountId; // Return as-is if not in expected format
}

/**
 * Get balance for Hedera (native or token)
 * IMPORTANT: tokenAddress should be in Hedera format (0.0.456858) for balance checking
 * If tokenAddress is EVM format (0x...), it will be converted to Hedera format
 * If tokenAddress is a symbol (USDC, SAUCE, etc.), it will be looked up
 */
export async function getHederaBalance(
  accountId: string,
  tokenAddress?: string,
  network: string = "mainnet",
): Promise<{ balance: string; balanceRaw: string; decimals: number }> {
  // Resolve account ID if needed
  const resolvedAccountId = await resolveHederaAccountId(accountId, network);

  // Convert tokenAddress to Hedera format if needed
  let hederaTokenAddress = tokenAddress;
  if (tokenAddress) {
    // If it's EVM format, convert to Hedera format
    if (tokenAddress.startsWith("0x")) {
      hederaTokenAddress = evmToHederaAddress(tokenAddress);
    }
    // If it's a symbol (not starting with 0. or 0x), look it up
    else if (!tokenAddress.startsWith("0.")) {
      const mappedAddress = getHederaTokenAddress(tokenAddress);
      if (mappedAddress) {
        hederaTokenAddress = mappedAddress;
      }
    }
  }

  if (!hederaTokenAddress || isHederaNative(hederaTokenAddress)) {
    // Fetch native HBAR balance
    const hbarBalance = await fetchHbarBalance(resolvedAccountId, network);
    return {
      ...hbarBalance,
      decimals: 8, // HBAR always has 8 decimals
    };
  } else {
    // Fetch token balance using Hedera format
    const tokenBalance = await fetchTokenBalance(resolvedAccountId, hederaTokenAddress, network);
    return {
      balance: tokenBalance.balance,
      balanceRaw: tokenBalance.balanceRaw,
      decimals: tokenBalance.decimals,
    };
  }
}

/**
 * Get EVM address for Hedera token (for contract calls)
 */
export function getHederaTokenEvmAddressForContract(tokenSymbol: string): string {
  return getHederaTokenEvmAddress(tokenSymbol);
}

/**
 * Convert token address to appropriate format based on use case
 */
export function getTokenAddressForUseCase(
  tokenSymbol: string,
  useCase: "balance" | "contract",
): string {
  if (useCase === "balance") {
    // Use Hedera format for balance checking
    return getHederaTokenAddress(tokenSymbol);
  } else {
    // Use EVM format for contract calls
    return getHederaTokenEvmAddress(tokenSymbol);
  }
}
