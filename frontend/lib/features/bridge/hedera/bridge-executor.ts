/**
 * Hedera Bridge Executor
 *
 * Chain-specific bridge execution logic for Hedera network.
 * Handles Hedera-specific bridge transactions using EtaBridge contract.
 * Similar to Hedera swap executor - uses ethers but with Hedera-specific handling.
 */

import { ethers } from "ethers";
import type { AppDispatch } from "@/lib/store";
import { ensureTokenApproval } from "@/lib/shared/blockchain/token-approval";
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
 * Check if network switch is needed
 */
function checkNetworkSwitch(
  currentChainId: number,
  chain: string,
): {
  needsSwitch: boolean;
  requiredChainId: number | null;
} {
  // Hedera chain ID is 295 (mainnet) or 296 (testnet)
  // Using 295 for mainnet
  const HEDERA_CHAIN_ID = 295;
  const requiredChainId = chain.toLowerCase() === "hedera" ? HEDERA_CHAIN_ID : null;

  return {
    needsSwitch: requiredChainId !== null && currentChainId !== requiredChainId,
    requiredChainId,
  };
}

/**
 * Add Hedera network to wallet
 */
async function addHederaNetwork(walletClient: any): Promise<void> {
  try {
    await walletClient.request({
      method: "wallet_addEthereumChain",
      params: [
        {
          chainId: "0x127", // 295 in hex (Hedera mainnet)
          chainName: "Hedera Mainnet",
          nativeCurrency: {
            name: "HBAR",
            symbol: "HBAR",
            decimals: 18,
          },
          rpcUrls: ["https://mainnet.hashio.io/api"],
          blockExplorerUrls: ["https://hashscan.io/mainnet"],
        },
      ],
    });
    console.log("   ✅ Hedera network added to wallet");
  } catch (error: any) {
    if (error.code === 4001) {
      throw new Error("Network addition rejected. Please add Hedera network manually.");
    }
    throw new Error(`Failed to add Hedera network: ${error.message}`);
  }
}

/**
 * Request network switch
 */
async function requestNetworkSwitch(
  walletClient: any,
  chainId: number,
  chainName: string,
): Promise<void> {
  try {
    console.log(`   🔄 Requesting network switch to ${chainName} (Chain ID: ${chainId})...`);
    await walletClient.switchChain({ id: chainId });
    console.log(`   ✅ Network switched to ${chainName}`);
  } catch (error: any) {
    // If switch fails because chain is not recognized, add it first
    if (error.code === 4902 || error.message?.includes("Unrecognized chain")) {
      console.log(`   ⚠️  Chain not recognized, adding ${chainName} network...`);
      await addHederaNetwork(walletClient);
      // Wait a bit for the network to be added
      await new Promise((resolve) => setTimeout(resolve, 1000));
      // Try switching again
      try {
        await walletClient.switchChain({ id: chainId });
        console.log(`   ✅ Network switched to ${chainName} after adding`);
      } catch (retryError: any) {
        throw new Error(`Failed to switch to ${chainName} after adding: ${retryError.message}`);
      }
      return;
    }
    // User rejected the switch
    if (error.code === 4001 || error.message?.includes("rejected")) {
      throw new Error(`Network switch rejected. Please switch to ${chainName} manually.`);
    }
    throw new Error(`Failed to switch network: ${error.message}`);
  }
}

/**
 * Check and switch network if needed (for Hedera)
 */
async function checkAndSwitchNetwork(
  walletClient: any,
  chain: string,
  onProgress?: (message: string) => void,
): Promise<void> {
  const provider = new ethers.BrowserProvider(walletClient as any);
  const currentChainId = await getCurrentChainId(provider);
  const { needsSwitch, requiredChainId } = checkNetworkSwitch(currentChainId, chain);

  if (needsSwitch && requiredChainId) {
    onProgress?.(`Please switch to ${chain} network...`);
    await requestNetworkSwitch(walletClient, requiredChainId, chain);
    // Wait a bit for the network to switch
    await new Promise((resolve) => setTimeout(resolve, 1000));
    // Verify the switch
    const newProvider = new ethers.BrowserProvider(walletClient as any);
    const newChainId = await getCurrentChainId(newProvider);
    if (newChainId !== requiredChainId) {
      throw new Error(`Network switch failed. Please switch to ${chain} manually.`);
    }
    console.log(`   ✅ Verified network switch to ${chain} (Chain ID: ${requiredChainId})`);
  }
}

/**
 * Execute bridge transaction for Hedera
 * Uses Hedera-specific handling: no gasPrice, capped gas limit at 7M
 */
export async function executeBridgeHedera(
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

    // Estimate gas for Hedera (with Hedera-specific handling)
    let gasLimit: number = 7_000_000; // Default: Hedera max gas limit
    try {
      const estimatedGas = await bridgeContract.bridgeTokens.estimateGas(...bridgeParams);
      // Add 20% buffer
      const gasWithBuffer = estimatedGas + (estimatedGas * BigInt(20)) / BigInt(100);
      gasLimit = Number(gasWithBuffer);

      // Cap gas limit for Hedera (max 7M)
      if (gasLimit > 7_000_000) {
        gasLimit = 7_000_000;
      }

      console.log(`   Estimated Gas: ${estimatedGas.toString()}, Using: ${gasLimit.toString()}`);
    } catch (gasError) {
      console.warn("Gas estimation failed, using default (7M):", gasError);
    }

    // Prepare transaction with Hedera-specific overrides
    // For Hedera: don't include gasPrice (let RPC handle it) and don't send value
    const overrides: ethers.Overrides = {
      gasLimit: gasLimit,
      // Explicitly don't set gasPrice for Hedera
      // Don't send value - fees are handled by the contract
    };

    // Populate transaction first (Hedera-specific)
    let populatedTx: ethers.TransactionLike;
    try {
      populatedTx = await bridgeContract.bridgeTokens.populateTransaction(
        ...bridgeParams,
        overrides,
      );

      // Verify transaction data was populated
      if (!populatedTx.data || populatedTx.data === "0x") {
        throw new Error(
          `Transaction data is empty for bridgeTokens. Check parameters: ${JSON.stringify(bridgeParams)}`,
        );
      }

      console.log(`   Populated transaction:`, {
        to: populatedTx.to,
        data: populatedTx.data?.substring(0, 50) + "...",
        dataLength: populatedTx.data?.length,
        value: populatedTx.value?.toString(),
        gasLimit: populatedTx.gasLimit?.toString(),
      });
    } catch (error: any) {
      console.error(`   Failed to populate transaction:`, error);
      throw new Error(`Failed to populate bridge transaction: ${error.message}`);
    }

    // Execute bridge transaction (Hedera-specific: no gasPrice, no value)
    const txRequest: ethers.TransactionRequest = {
      to: populatedTx.to,
      data: populatedTx.data,
      value: BigInt(0), // No value needed - fees handled by contract
      gasLimit: populatedTx.gasLimit,
      // Don't set gasPrice for Hedera
    };

    const txResponse = await signer.sendTransaction(txRequest);

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
    console.error("Bridge execution error (Hedera):", err);
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
