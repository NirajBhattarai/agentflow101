/**
 * Hedera Transaction Utilities
 * 
 * Utilities for serializing, deserializing, and signing Hedera transactions
 */

import { Transaction } from "@hashgraph/sdk";
import { HederaSigner } from "./wallet";

/**
 * Serializes a transaction to base64 encoded bytes for transmission.
 */
export function serializeTransaction(transaction: Transaction): string {
  return Buffer.from(transaction.toBytes()).toString("base64");
}

/**
 * Deserializes a transaction from base64 encoded bytes.
 */
export function deserializeTransaction(transactionBytes: string): Transaction {
  const bytes = Buffer.from(transactionBytes, "base64");
  return Transaction.fromBytes(bytes);
}

/**
 * Adds an additional signature to a transaction (for fee payer scenarios).
 */
export async function addSignatureToTransaction(
  transaction: Transaction,
  signer: HederaSigner,
): Promise<Transaction> {
  return await transaction.sign(signer.privateKey);
}

