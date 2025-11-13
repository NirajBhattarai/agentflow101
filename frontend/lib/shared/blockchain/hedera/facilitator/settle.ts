/**
 * Hedera Payment Settlement
 * 
 * Settles verified Hedera payment transactions on-chain
 */

import {
  Transaction,
  TransactionResponse,
  Status,
  TransactionId,
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
    // Ensure the client has the operator set (required for execution)
    signer.client.setOperator(signer.accountId, signer.privateKey);

    // Check transaction ID to determine if facilitator signature is needed
    const transactionId = transaction.transactionId;
    const isFacilitatorTransaction = transactionId && 
      transactionId.accountId && 
      transactionId.accountId.toString() === signer.accountId.toString();

    let signedTransaction: Transaction;
    
    if (transaction.isFrozen()) {
      // Transaction is frozen (already signed)
      // If transaction ID is for facilitator account, we need to determine if facilitator signature is present
      // 
      // The issue: When verify route signs with facilitator (wallet signature flow), transaction is fully signed
      // When only payer signs (testFacilitatorEthers.ts), transaction needs facilitator signature
      //
      // Solution: Since we can't easily check signatures, we'll use a heuristic:
      // - If transaction was signed in verify route, it's in the payload and should be ready
      // - The safest approach: For facilitator transactions, always try signWithOperator
      //   BUT: signWithOperator on an already-signed transaction might fail
      // 
      // Better approach: Check if we can safely add signature without corrupting
      // Since signWithOperator should be safe, try it. If it fails, execute directly.
      if (isFacilitatorTransaction) {
        // Transaction ID is for facilitator - need facilitator signature
        // Try adding signature. If transaction already has it, signWithOperator should handle it gracefully
        // If it throws an error, the transaction might already be fully signed - try executing directly
        try {
          signedTransaction = await transaction.signWithOperator(signer.client);
          console.log("✅ Transaction frozen, added facilitator signature using signWithOperator");
        } catch (signError: any) {
          // signWithOperator failed - transaction might already be fully signed
          // Try executing directly
          console.log("⚠️ signWithOperator failed, transaction may already be fully signed. Attempting direct execution.");
          signedTransaction = transaction;
        }
      } else {
        // Transaction ID is not for facilitator, should be ready to execute
        signedTransaction = transaction;
        console.log("✅ Transaction frozen and ready to execute");
      }
    } else {
      // Transaction is not frozen, needs freezing and signing
      const frozenTransaction = await transaction.freezeWith(signer.client);
      signedTransaction = await frozenTransaction.signWithOperator(signer.client);
      console.log("✅ Transaction frozen and signed with facilitator operator");
    }

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

