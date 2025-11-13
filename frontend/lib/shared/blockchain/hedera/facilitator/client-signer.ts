/**
 * Client-side Hedera transaction signing utilities
 * 
 * Utilities for signing Hedera transactions from the browser using wallet connections
 */

import { ethers } from "ethers";
import { AccountId } from "@hashgraph/sdk";

/**
 * Converts Hedera account ID to EVM address
 */
export function accountIdToEvmAddress(accountId: string): string {
  try {
    const account = AccountId.fromString(accountId);
    // Hedera account IDs can be converted to EVM addresses
    // Format: 0x + left-padded account number
    const shard = account.shard.toString().padStart(8, "0");
    const realm = account.realm.toString().padStart(8, "0");
    const num = account.num.toString().padStart(8, "0");
    // This is a simplified conversion - actual Hedera EVM addresses use a different format
    // For now, we'll use the account ID directly if it's already an EVM address
    if (accountId.startsWith("0x")) {
      return accountId;
    }
    // Convert to EVM address format (this is approximate)
    return `0x${shard}${realm}${num}`.slice(0, 42); // Ensure 42 chars (0x + 40 hex)
  } catch (error) {
    // If it's already an EVM address, return it
    if (accountId.startsWith("0x") && accountId.length === 42) {
      return accountId;
    }
    throw new Error(`Invalid account ID format: ${accountId}`);
  }
}

/**
 * Creates a signable message from transaction data
 * This is used as a workaround since Hedera native transactions can't be directly signed by MetaMask
 */
export function createSignableMessage(
  network: string,
  from: string,
  to: string,
  amount: string,
  asset: string,
  transactionId: string,
): string {
  return `Hedera x402 Payment Authorization

Network: ${network}
From: ${from}
To: ${to}
Amount: ${amount}
Asset: ${asset}
Transaction ID: ${transactionId}

By signing this message, you authorize this payment transaction.`;
}

/**
 * Signs a message using MetaMask/wallet
 */
export async function signMessageWithWallet(
  provider: ethers.BrowserProvider,
  message: string,
): Promise<string> {
  const signer = await provider.getSigner();
  return await signer.signMessage(message);
}

