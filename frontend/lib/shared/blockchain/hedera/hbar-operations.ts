/**
 * HBAR-specific operations
 *
 * HBAR uses tinybars as its smallest unit:
 * - 1 HBAR = 100,000,000 tinybars (10^8)
 * - This is different from EVM chains which use wei (10^18)
 *
 * This file contains all HBAR-specific logic to make debugging easier
 * and keep HBAR operations separate from EVM operations.
 */

// HBAR constants
export const HBAR_DECIMALS = 8;
export const TINYBAR_PER_HBAR = BigInt(100_000_000); // 10^8

/**
 * Convert HBAR amount to tinybars
 * @param hbarAmount - Amount in HBAR (e.g., "1.5" for 1.5 HBAR)
 * @returns Amount in tinybars as bigint
 */
export function hbarToTinybars(hbarAmount: string): bigint {
  const amountFloat = parseFloat(hbarAmount);
  if (isNaN(amountFloat) || amountFloat < 0) {
    throw new Error(`Invalid HBAR amount: ${hbarAmount}`);
  }
  return BigInt(Math.floor(amountFloat * Number(TINYBAR_PER_HBAR)));
}

/**
 * Convert tinybars to HBAR amount
 * @param tinybars - Amount in tinybars as bigint or string
 * @returns Amount in HBAR as string (formatted to 8 decimals)
 */
export function tinybarsToHbar(tinybars: bigint | string): string {
  const tinybarsBigInt = typeof tinybars === "string" ? BigInt(tinybars) : tinybars;
  const hbarAmount = Number(tinybarsBigInt) / Number(TINYBAR_PER_HBAR);
  return hbarAmount.toFixed(HBAR_DECIMALS);
}

/**
 * Format HBAR amount for display
 * Similar to ethers.formatEther() but for HBAR (uses 10^8 instead of 10^18)
 * @param tinybars - Amount in tinybars
 * @returns Formatted string (e.g., "1.50000000")
 */
export function formatHbar(tinybars: bigint | string): string {
  return tinybarsToHbar(tinybars);
}

/**
 * Parse HBAR amount from string
 * Similar to ethers.parseEther() but for HBAR (uses 10^8 instead of 10^18)
 * @param hbarAmount - Amount in HBAR (e.g., "1.5")
 * @returns Amount in tinybars as bigint
 */
export function parseHbar(hbarAmount: string): bigint {
  return hbarToTinybars(hbarAmount);
}

/**
 * Check if balance is sufficient for a transaction
 * @param balanceTinybars - Current balance in tinybars
 * @param requiredTinybars - Required amount in tinybars
 * @returns Object with sufficient flag and formatted amounts
 */
export function checkHbarBalance(
  balanceTinybars: bigint,
  requiredTinybars: bigint,
): {
  sufficient: boolean;
  balance: string;
  required: string;
  shortfall: string;
} {
  const balance = formatHbar(balanceTinybars);
  const required = formatHbar(requiredTinybars);
  const shortfall =
    balanceTinybars < requiredTinybars ? formatHbar(requiredTinybars - balanceTinybars) : "0";

  return {
    sufficient: balanceTinybars >= requiredTinybars,
    balance,
    required,
    shortfall,
  };
}

/**
 * Format error message for insufficient HBAR balance
 * @param balanceTinybars - Current balance in tinybars
 * @param requiredTinybars - Required amount in tinybars
 * @returns Formatted error message
 */
export function formatInsufficientBalanceError(
  balanceTinybars: bigint,
  requiredTinybars: bigint,
): string {
  const { balance, required, shortfall } = checkHbarBalance(balanceTinybars, requiredTinybars);
  return `Insufficient funds: Need ${required} HBAR, but have ${balance} HBAR (shortfall: ${shortfall} HBAR)`;
}
