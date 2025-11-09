/**
 * SaucerSwap Contract Integration for Hedera Mainnet
 *
 * SaucerSwap is a Uniswap V2 fork on Hedera, so we can use standard Uniswap V2 Router ABI
 */

import { ROUTER_ABI } from "./router-abi";

// SaucerSwap Router Contract Address on Hedera Mainnet
// Source: https://docs.saucerswap.finance/
export const SAUCERSWAP_ROUTER_ADDRESS = "0x00000000000000000000000000000000006715e6"; //

// Re-export ROUTER_ABI for convenience
export { ROUTER_ABI };

// ERC20 Token ABI
export const ERC20_ABI = [
  "function balanceOf(address account) external view returns (uint256)",
  "function decimals() external view returns (uint8)",
  "function symbol() external view returns (string)",
  "function approve(address spender, uint256 amount) external returns (bool)",
  "function allowance(address owner, address spender) external view returns (uint256)",
  "function transfer(address to, uint256 amount) external returns (bool)",
];

// Wrapped HBAR address on Hedera (for native HBAR swaps)
export const WETH_ADDRESS = "0.0.1456986"; // WHBAR on Hedera

/**
 * Calculate deadline (20 minutes from now)
 */
export function getDeadline(): number {
  return Math.floor(Date.now() / 1000) + 20 * 60; // 20 minutes
}
