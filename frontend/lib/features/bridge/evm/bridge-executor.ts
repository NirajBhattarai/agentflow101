/**
 * EVM Bridge Executor
 *
 * Chain-specific bridge execution logic for EVM-compatible chains (Polygon, Ethereum, etc.).
 * Handles EVM-specific bridge transactions using EtaBridge contract.
 */

import { ethers } from "ethers";
import type { AppDispatch } from "@/lib/store";
import { ensureTokenApproval } from "@/lib/shared/blockchain/token-approval";
import { getChainId } from "@/lib/shared/blockchain/network-utils";
import {
  setApprovalStatus,
  setApprovalStatusField,
  setBridging,
  setTxHash,
  type ApprovalStatus,
} from "@/lib/store/slices/bridgeSlice";
import type { BridgeTransaction, BridgeExecutionResult, BridgeExecutionCallbacks } from "../types";

// EtaBridge ABI (minimal - only functions we need)
const ETABRIDGE_ABI = [
  "function bridgeTokens(string symbol, uint256 amount, address receiver, uint32 targetChainId, bytes _options) payable returns ((bytes32 guid, uint64 nonce, (uint256 nativeFee, uint256 lzTokenFee) fee) receipt)",
  "function quote(string symbol, uint256 amount, address receiver, uint32 targetChainId, bytes _options) view returns (uint256 nativeFee)",
  "function supportedTokens(string) view returns (address)",
];

/**
 * Get LayerZero options for bridge
 */
function getLayerZeroOptions(): string {
  // Default LayerZero options: version 3, gas type 1, extra data
  // Format: 0x000301001101000000000000000000000000000222e0
  return "0x000301001101000000000000000000000000000222e0";
}

/**
 * Convert amount to smallest unit (USDC has 6 decimals)
 */
function convertAmountToSmallestUnit(amount: string, decimals: number = 6): bigint {
  const amountFloat = parseFloat(amount);
  const multiplier = BigInt(10 ** decimals);
  return BigInt(Math.floor(amountFloat * Number(multiplier)));
}

/**
 * Create approval status object
 */
function createApprovalStatus(
  tokenAddress: string,
  tokenSymbol: string,
  spender: string,
  amount: string,
): ApprovalStatus {
  return {
    tokenAddress,
    tokenSymbol,
    spender,
    amount,
    status: "checking",
  };
}

/**
 * Execute token approval
 */
async function executeApproval(
  dispatch: AppDispatch,
  provider: ethers.Provider,
  signer: ethers.Signer,
  tokenAddress: string,
  address: string,
  spender: string,
  amountInSmallestUnit: bigint,
  chain: string,
): Promise<void> {
  dispatch(setApprovalStatusField({ status: "needs_approval" }));
  const approvalSuccess = await ensureTokenApproval(
    provider,
    signer,
    tokenAddress,
    address,
    spender,
    amountInSmallestUnit,
    chain,
  );
  if (approvalSuccess) {
    dispatch(setApprovalStatusField({ status: "approved" }));
    console.log(`   ✅ Token approval confirmed`);
  } else {
    dispatch(setApprovalStatusField({ status: "error", error: "Approval failed" }));
    throw new Error("Token approval failed");
  }
}

/**
 * Get current chain ID from provider
 */
async function getCurrentChainId(provider: ethers.Provider): Promise<number> {
  const network = await provider.getNetwork();
  return Number(network.chainId);
}

/**
 * Check and switch network if needed
 */
async function checkAndSwitchNetwork(
  walletClient: any,
  chain: string,
  onProgress?: (message: string) => void,
): Promise<void> {
  const provider = new ethers.BrowserProvider(walletClient as any);
  const currentChainId = await getCurrentChainId(provider);
  const requiredChainId = getChainId(chain);

  if (requiredChainId && currentChainId !== requiredChainId) {
    onProgress?.(`Switching to ${chain} network...`);
    try {
      await walletClient.switchChain({ id: requiredChainId });
      // Wait for network switch
      await new Promise((resolve) => setTimeout(resolve, 1000));
    } catch (error: any) {
      throw new Error(`Failed to switch to ${chain} network: ${error.message}`);
    }
  }
}

/**
 * Execute bridge transaction for EVM chains
 */
export async function executeBridgeEVM(
  transaction: BridgeTransaction,
  walletClient: any,
  address: string,
  dispatch: AppDispatch,
  callbacks?: BridgeExecutionCallbacks,
): Promise<BridgeExecutionResult> {
  const { onStateChange, onError, onTxHash, onProgress } = callbacks || {};

  try {
    dispatch(setBridging(true));
    onStateChange?.("bridging");
    onProgress?.("Initializing bridge transaction...");

    if (!transaction.bridge_contract_address) {
      throw new Error("Bridge contract address not provided");
    }

    if (!transaction.source_chain_id || !transaction.destination_chain_id) {
      throw new Error("Chain IDs not provided");
    }

    // Check and switch network if needed
    await checkAndSwitchNetwork(walletClient, transaction.source_chain, onProgress);

    // Create provider and signer
    const provider = new ethers.BrowserProvider(walletClient as any);
    const signer = await provider.getSigner();

    // Get token decimals (USDC has 6 decimals)
    const tokenDecimals = 6; // USDC always has 6 decimals
    const amountInSmallestUnit = convertAmountToSmallestUnit(transaction.amount, tokenDecimals);

    onProgress?.(
      `Bridging ${transaction.amount} ${transaction.token_symbol} from ${transaction.source_chain} to ${transaction.destination_chain}...`,
    );

    // Check and approve token if needed (USDC is ERC20, needs approval)
    onProgress?.("Checking token approval...");
    const approvalStatus = createApprovalStatus(
      transaction.token_address,
      transaction.token_symbol,
      transaction.bridge_contract_address,
      transaction.amount,
    );
    dispatch(setApprovalStatus(approvalStatus));
    dispatch(setApprovalStatusField({ status: "checking" }));

    await executeApproval(
      dispatch,
      provider,
      signer,
      transaction.token_address,
      address,
      transaction.bridge_contract_address,
      amountInSmallestUnit,
      transaction.source_chain,
    );

    // Create contract instance
    const bridgeContract = new ethers.Contract(
      transaction.bridge_contract_address,
      ETABRIDGE_ABI,
      signer,
    );

    // Get LayerZero options
    const options = getLayerZeroOptions();

    // Prepare bridge parameters
    const bridgeParams = [
      transaction.token_symbol, // symbol: "USDC"
      amountInSmallestUnit, // amount
      address, // receiver (same address on destination chain)
      transaction.destination_chain_id, // targetChainId (LayerZero endpoint ID)
      options, // _options (LayerZero options)
    ];

    onProgress?.("Sending bridge transaction...");

    // Estimate gas for EVM chains
    let gasLimit: bigint | undefined;
    try {
      const estimatedGas = await bridgeContract.bridgeTokens.estimateGas(...bridgeParams);
      // Add 20% buffer for EVM
      gasLimit = estimatedGas + (estimatedGas * BigInt(20)) / BigInt(100);
      onProgress?.(`Estimated gas: ${estimatedGas.toString()}, Using: ${gasLimit.toString()}`);
    } catch (gasError) {
      console.warn("Gas estimation failed, proceeding anyway:", gasError);
    }

    // Execute bridge transaction (no value needed - fees handled by contract)
    const txResponse = await bridgeContract.bridgeTokens(...bridgeParams, {
      gasLimit, // Include gas limit if estimated
      // Don't send value - fees are handled by the contract
    });

    onProgress?.("Transaction sent, waiting for confirmation...");
    dispatch(setTxHash(txResponse.hash));
    onTxHash?.(txResponse.hash);

    // Wait for transaction confirmation
    const receipt = await txResponse.wait();
    onProgress?.("Transaction confirmed!");

    dispatch(setBridging(false));
    dispatch(setApprovalStatus(null));
    onStateChange?.("done");

    return {
      success: true,
      transactionHash: txResponse.hash,
      receipt,
    };
  } catch (err: any) {
    console.error("Bridge execution error (EVM):", err);
    dispatch(setBridging(false));
    dispatch(setApprovalStatus(null));
    onError?.(err.message || "Bridge execution failed");
    onStateChange?.("idle");

    return {
      success: false,
      error: err.message || "Bridge execution failed",
    };
  }
}
