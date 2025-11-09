/**
 * EVM-compatible chain operations
 *
 * Supports standard EVM chains like Polygon, Ethereum, etc.
 * Uses standard Web3/Ethers.js patterns:
 * - RPC calls instead of REST APIs
 * - EVM addresses (0x...)
 * - Wei-based amounts (1 token = 10^decimals wei)
 * - ERC20 token standard
 */

import { ethers } from "ethers";

// Standard ERC20 ABI for balance checking
const ERC20_ABI = [
  "function balanceOf(address owner) view returns (uint256)",
  "function decimals() view returns (uint8)",
  "function symbol() view returns (string)",
];

/**
 * Check if address is native token (ETH/MATIC/etc)
 */
export function isEvmNative(address: string): boolean {
  return address.toLowerCase() === "0x0000000000000000000000000000000000000000";
}

/**
 * Fetch native token balance (ETH, MATIC, etc.) using RPC
 */
export async function fetchNativeBalance(
  provider: ethers.Provider,
  address: string,
): Promise<{ balance: string; balanceRaw: string }> {
  const balanceWei = await provider.getBalance(address);
  const balanceEther = ethers.formatEther(balanceWei);

  return {
    balance: balanceEther,
    balanceRaw: balanceWei.toString(),
  };
}

/**
 * Fetch ERC20 token balance using RPC
 */
export async function fetchTokenBalance(
  provider: ethers.Provider,
  tokenAddress: string,
  accountAddress: string,
): Promise<{ balance: string; balanceRaw: string; decimals: number; symbol: string }> {
  // Create ERC20 contract instance
  const tokenContract = new ethers.Contract(tokenAddress, ERC20_ABI, provider);

  // Get token balance, decimals, and symbol
  const [balanceRaw, decimals, symbol] = await Promise.all([
    tokenContract.balanceOf(accountAddress),
    tokenContract.decimals(),
    tokenContract.symbol(),
  ]);

  // Format balance
  const balance = ethers.formatUnits(balanceRaw, decimals);

  return {
    balance,
    balanceRaw: balanceRaw.toString(),
    decimals: Number(decimals),
    symbol,
  };
}

/**
 * Parse token amount for EVM chains (wei)
 * EVM uses wei: 1 token = 10^decimals wei
 */
export function parseEvmAmount(amount: string, decimals: number = 18): bigint {
  return ethers.parseUnits(amount, decimals);
}

/**
 * Format token amount for EVM chains (from wei)
 */
export function formatEvmAmount(amount: bigint, decimals: number = 18): string {
  return ethers.formatUnits(amount, decimals);
}

/**
 * Get balance for EVM chain (native or token)
 */
export async function getEvmBalance(
  provider: ethers.Provider,
  accountAddress: string,
  tokenAddress?: string,
): Promise<{ balance: string; balanceRaw: string; decimals: number }> {
  if (!tokenAddress || isEvmNative(tokenAddress)) {
    // Fetch native token balance
    const nativeBalance = await fetchNativeBalance(provider, accountAddress);
    return {
      balance: nativeBalance.balance,
      balanceRaw: nativeBalance.balanceRaw,
      decimals: 18, // Native tokens typically have 18 decimals
    };
  } else {
    // Fetch ERC20 token balance
    const tokenBalance = await fetchTokenBalance(provider, tokenAddress, accountAddress);
    return {
      balance: tokenBalance.balance,
      balanceRaw: tokenBalance.balanceRaw,
      decimals: tokenBalance.decimals,
    };
  }
}

/**
 * Validate EVM address format
 */
export function isValidEvmAddress(address: string): boolean {
  try {
    return ethers.isAddress(address);
  } catch {
    return false;
  }
}

/**
 * Convert address to checksum format
 */
export function toChecksumAddress(address: string): string {
  return ethers.getAddress(address);
}
