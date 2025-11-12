import { ethers } from "ethers";
import type { SwapTransaction as SwapTransactionType } from "@/types";

/**
 * Extended swap transaction interface for executor
 * Includes additional fields needed for swap execution
 */
export interface SwapTransaction extends Partial<SwapTransactionType> {
  chain?: string;
  token_in_address: string;
  token_out_address: string;
  token_in_symbol: string;
  token_out_symbol: string;
  amount_in: string;
  pool_address: string;
  dex_name?: string;
  swap_path?: string[] | string;
  token_in_address_evm?: string;
  token_out_address_evm?: string;
  token_in_address_hedera?: string;
  rpc_url?: string;
}

export interface SwapExecutionResult {
  success: boolean;
  txHash?: string;
  receipt?: ethers.TransactionReceipt;
  error?: string;
}

export interface SwapExecutionCallbacks {
  onStateChange?: (state: "idle" | "swapping" | "done") => void;
  onError?: (error: string) => void;
  onTxHash?: (hash: string) => void;
  onProgress?: (message: string) => void;
}
