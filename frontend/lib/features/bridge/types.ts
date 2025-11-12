/**
 * Bridge execution types
 */

import type { BridgeTransaction } from "@/types";

export interface BridgeExecutionResult {
  success: boolean;
  transactionHash?: string;
  receipt?: any;
  error?: string;
}

export interface BridgeExecutionCallbacks {
  onStateChange?: (state: "idle" | "bridging" | "done") => void;
  onError?: (error: string) => void;
  onTxHash?: (hash: string) => void;
  onProgress?: (message: string) => void;
}

export type { BridgeTransaction };
