/**
 * Hedera Payment Verification
 * 
 * Verifies Hedera payment transactions before settlement
 */

import {
  Transaction,
  TransferTransaction,
  AccountId,
  TokenId,
} from "@hashgraph/sdk";
import { HederaSigner } from "./wallet";
import { deserializeTransaction } from "./transaction";
import { PaymentPayload, PaymentRequirements, VerifyResponse, ErrorReasons } from "./types";

const SCHEME = "exact";
const SUPPORTED_NETWORKS = ["hedera-testnet", "hedera-mainnet"];

/**
 * Verify the payment payload against the payment requirements.
 */
export async function verify(
  signer: HederaSigner,
  payload: PaymentPayload,
  paymentRequirements: PaymentRequirements,
): Promise<VerifyResponse> {
  try {
    // verify that the scheme and network are supported
    verifySchemesAndNetworks(payload, paymentRequirements);

    // decode the base64 encoded transaction
    const transaction = deserializeTransaction(payload.payload.transaction);

    // perform transaction introspection to validate the transaction structure and details
    await transactionIntrospection(signer, transaction, paymentRequirements);

    return {
      isValid: true,
      invalidReason: undefined,
    };
  } catch (error) {
    // if the error is one of the known error reasons, return the error reason
    if (error instanceof Error) {
      if (ErrorReasons.includes(error.message as any)) {
        return {
          isValid: false,
          invalidReason: error.message as any,
        };
      }
    }

    // if the error is not one of the known error reasons, return an unexpected error reason
    console.error(error);
    return {
      isValid: false,
      invalidReason: "unexpected_verify_error",
    };
  }
}

/**
 * Verify that the scheme and network are supported.
 */
export function verifySchemesAndNetworks(
  payload: PaymentPayload,
  paymentRequirements: PaymentRequirements,
): void {
  if (payload.scheme !== SCHEME || paymentRequirements.scheme !== SCHEME) {
    throw new Error("unsupported_scheme");
  }

  if (
    payload.network !== paymentRequirements.network ||
    !SUPPORTED_NETWORKS.includes(paymentRequirements.network)
  ) {
    throw new Error("invalid_network");
  }
}

/**
 * Perform transaction introspection to validate the transaction structure and transfer details.
 */
export async function transactionIntrospection(
  signer: HederaSigner,
  transaction: Transaction,
  paymentRequirements: PaymentRequirements,
): Promise<void> {
  // Validate that this is a transfer transaction
  if (!(transaction instanceof TransferTransaction)) {
    throw new Error("invalid_exact_hedera_payload_transaction");
  }

  // Validate transaction ID contains facilitator's account ID
  const transactionId = transaction.transactionId;
  if (!transactionId) {
    throw new Error("invalid_exact_hedera_payload_transaction");
  }

  const transactionAccountId = transactionId.accountId;
  if (!transactionAccountId || transactionAccountId.toString() !== signer.accountId.toString()) {
    throw new Error("invalid_exact_hedera_payload_transaction_signature");
  }

  // Validate facilitator account ID matches payment requirements
  const expectedFacilitatorId = paymentRequirements.extra?.feePayer as string;
  if (!expectedFacilitatorId || expectedFacilitatorId !== signer.accountId.toString()) {
    throw new Error("invalid_exact_hedera_payload_transaction_signature");
  }

  // Determine if this is HBAR or token transfer based on payment requirements
  if (isHbarTransfer(paymentRequirements.asset)) {
    // HBAR transfer validation
    await validateHbarTransfer(transaction, paymentRequirements);
  } else {
    // Token transfer validation
    await validateTokenTransfer(transaction, paymentRequirements);
  }
}

/**
 * Check if the asset represents HBAR
 */
function isHbarTransfer(asset: string): boolean {
  return asset === "0.0.0" || asset.toLowerCase() === "hbar";
}

/**
 * Validates HBAR transfer details
 */
async function validateHbarTransfer(
  transaction: Transaction,
  paymentRequirements: PaymentRequirements,
): Promise<void> {
  // Validate asset (should be HBAR)
  if (!isHbarTransfer(paymentRequirements.asset)) {
    throw new Error("invalid_exact_hedera_payload_transaction_asset_mismatch");
  }
}

/**
 * Validates token transfer details
 */
async function validateTokenTransfer(
  transaction: Transaction,
  paymentRequirements: PaymentRequirements,
): Promise<void> {
  // Validate that the asset is not HBAR (should be a token)
  if (isHbarTransfer(paymentRequirements.asset)) {
    throw new Error("invalid_exact_hedera_payload_transaction_asset_mismatch");
  }

  // Validate that the asset is a valid token ID format
  try {
    TokenId.fromString(paymentRequirements.asset);
  } catch (error) {
    throw new Error("invalid_exact_hedera_payload_transaction_asset_mismatch");
  }
}

