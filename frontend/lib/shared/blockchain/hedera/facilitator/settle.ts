/**
 * Hedera Payment Settlement
 * 
 * Settles verified Hedera payment transactions on-chain
 */

import {
  Transaction,
  TransactionResponse,
  Status,
} from "@hashgraph/sdk";
import { HederaSigner } from "./wallet";
import {
  deserializeTransaction,
  addSignatureToTransaction,
} from "./transaction";
import { PaymentPayload, PaymentRequirements, SettleResponse, ErrorReasons } from "./types";
import { verify } from "./verify";

/**
 * Settle the payment payload against the payment requirements.
 */
export async function settle(
  signer: HederaSigner,
  payload: PaymentPayload,
  paymentRequirements: PaymentRequirements,
): Promise<SettleResponse> {
  // First verify the payment
  const verifyResponse = await verify(signer, payload, paymentRequirements);
  if (!verifyResponse.isValid) {
    return {
      success: false,
      errorReason: verifyResponse.invalidReason,
      network: payload.network,
      transaction: "",
      payer: verifyResponse.payer || "",
    };
  }

  const transaction = deserializeTransaction(payload.payload.transaction);
  const payer = signer.accountId.toString();

  try {
    const { success, errorReason, transactionId } = await executeTransaction(transaction, signer);

    return {
      success,
      errorReason,
      payer,
      transaction: transactionId,
      network: payload.network,
    };
  } catch (error) {
    console.error("Unexpected error during transaction settlement:", error);
    return {
      success: false,
      errorReason: "unexpected_settle_error",
      network: payload.network,
      transaction: "",
      payer,
    };
  }
}

/**
 * Execute a Hedera transaction by adding facilitator signature and submitting to network
 */
export async function executeTransaction(
  transaction: Transaction,
  signer: HederaSigner,
): Promise<{
  success: boolean;
  errorReason?: (typeof ErrorReasons)[number];
  transactionId: string;
}> {
  try {
    // Add facilitator signature to the transaction
    const signedTransaction = await addSignatureToTransaction(transaction, signer);

    // Submit the transaction to the Hedera network
    const transactionResponse = await signedTransaction.execute(signer.client);

    // Wait for the transaction to be processed
    const receipt = await transactionResponse.getReceipt(signer.client);

    // Check if the transaction was successful
    if (receipt.status === Status.Success) {
      return {
        success: true,
        transactionId: transactionResponse.transactionId.toString(),
      };
    } else {
      return {
        success: false,
        errorReason: "settle_exact_hedera_transaction_failed",
        transactionId: transactionResponse.transactionId.toString(),
      };
    }
  } catch (error) {
    console.error("Transaction execution failed:", error);

    // Check for specific Hedera errors
    if (error instanceof Error) {
      if (error.message.includes("INSUFFICIENT_ACCOUNT_BALANCE")) {
        return {
          success: false,
          errorReason: "invalid_exact_hedera_payload_transaction_insufficient_balance",
          transactionId: "",
        };
      }

      if (error.message.includes("timeout") || error.message.includes("TIMEOUT")) {
        return {
          success: false,
          errorReason: "settle_exact_hedera_transaction_confirmation_timeout",
          transactionId: "",
        };
      }
    }

    return {
      success: false,
      errorReason: "settle_exact_hedera_transaction_failed",
      transactionId: "",
    };
  }
}

