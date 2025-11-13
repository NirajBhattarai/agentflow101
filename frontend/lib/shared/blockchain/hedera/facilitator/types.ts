/**
 * x402 Hedera Facilitator Types
 * 
 * Types for the Hedera facilitator implementation
 */

export interface PaymentRequirements {
  scheme: string;
  network: string;
  maxAmountRequired: string;
  asset: string;
  payTo: string;
  resource: string;
  description: string;
  mimeType?: string;
  outputSchema?: any;
  maxTimeoutSeconds: number;
  extra?: {
    feePayer?: string;
    [key: string]: any;
  };
}

export interface PaymentPayload {
  x402Version: number;
  scheme: string;
  network: string;
  payload: {
    transaction: string; // base64 encoded transaction
  };
}

export interface VerifyResponse {
  isValid: boolean;
  invalidReason?: string;
  payer?: string;
}

export interface SettleResponse {
  success: boolean;
  errorReason?: string;
  transaction: string;
  network: string;
  payer: string;
}

export type ErrorReason =
  | "insufficient_funds"
  | "invalid_exact_hedera_payload_transaction"
  | "invalid_exact_hedera_payload_transaction_signature"
  | "invalid_exact_hedera_payload_transaction_asset_mismatch"
  | "invalid_exact_hedera_payload_transaction_insufficient_balance"
  | "invalid_network"
  | "invalid_payload"
  | "invalid_payment_requirements"
  | "invalid_scheme"
  | "unsupported_scheme"
  | "invalid_x402_version"
  | "settle_exact_hedera_transaction_failed"
  | "settle_exact_hedera_transaction_confirmation_timeout"
  | "unexpected_verify_error"
  | "unexpected_settle_error";

export const ErrorReasons: ErrorReason[] = [
  "insufficient_funds",
  "invalid_exact_hedera_payload_transaction",
  "invalid_exact_hedera_payload_transaction_signature",
  "invalid_exact_hedera_payload_transaction_asset_mismatch",
  "invalid_exact_hedera_payload_transaction_insufficient_balance",
  "invalid_network",
  "invalid_payload",
  "invalid_payment_requirements",
  "invalid_scheme",
  "unsupported_scheme",
  "invalid_x402_version",
  "settle_exact_hedera_transaction_failed",
  "settle_exact_hedera_transaction_confirmation_timeout",
  "unexpected_verify_error",
  "unexpected_settle_error",
];

