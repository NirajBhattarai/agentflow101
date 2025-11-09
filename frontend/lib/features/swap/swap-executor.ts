/**
 * Swap Executor
 *
 * Centralized swap execution logic extracted from SwapCard component.
 * Handles all swap types (native/token) across different chains (Hedera/EVM).
 */

import { ethers } from "ethers";
import { ROUTER_ABI } from "@/lib/shared/contracts/router-abi";
import {
  prepareSwapParams,
  executeSwap as executeSwapTx,
  parseTokenAmount,
  isNative as isNativeTokenCheck,
  getBalance as getBalanceUtil,
} from "@/lib/shared/blockchain/swap-utils";
import { formatInsufficientBalanceError } from "@/lib/shared/blockchain/hedera/hbar-operations";
import { ensureTokenApproval, getTokenDecimals } from "@/lib/shared/blockchain/token-approval";
import type { SwapTransaction as SwapTransactionType } from "@/types";

// Constants
const WHBAR_ADDRESS = "0x0000000000000000000000000000000000163B5a"; // WHBAR EVM address (0.0.1456986)
const ZERO_ADDRESS = "0x0000000000000000000000000000000000000000";

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

/**
 * Fix swap path for Hedera native token swaps
 * Replaces zero addresses with WHBAR address
 */
function fixHederaSwapPath(
  swapPath: string[],
  tokenInIsNative: boolean,
  tokenOutIsNative: boolean,
): string[] {
  const fixedPath = [...swapPath];

  for (let i = 0; i < fixedPath.length; i++) {
    const pathAddr = fixedPath[i]?.toLowerCase();

    // Replace zero address with WHBAR
    if (pathAddr === ZERO_ADDRESS.toLowerCase()) {
      fixedPath[i] = WHBAR_ADDRESS;
      console.log(`   Fixed swap path[${i}]: ${ZERO_ADDRESS} -> ${WHBAR_ADDRESS}`);
    }

    // Fix first token if it's native
    if (tokenInIsNative && i === 0 && pathAddr !== WHBAR_ADDRESS.toLowerCase()) {
      fixedPath[i] = WHBAR_ADDRESS;
      console.log(`   Fixed swap path[0] (tokenIn is native): ${fixedPath[i]} -> ${WHBAR_ADDRESS}`);
    }

    // Fix last token if it's native
    if (
      tokenOutIsNative &&
      i === fixedPath.length - 1 &&
      pathAddr !== WHBAR_ADDRESS.toLowerCase()
    ) {
      fixedPath[i] = WHBAR_ADDRESS;
      console.log(
        `   Fixed swap path[${i}] (tokenOut is native): ${fixedPath[i]} -> ${WHBAR_ADDRESS}`,
      );
    }
  }

  console.log(`   Final swap path: ${fixedPath.join(" -> ")}`);
  return fixedPath;
}

/**
 * Prepare swap path from transaction data
 */
function prepareSwapPath(
  transaction: SwapTransaction,
  tokenInAddress: string,
  tokenOutAddress: string,
  chain: string,
  tokenInIsNative: boolean,
  tokenOutIsNative: boolean,
): string[] {
  let swapPath: string[] = Array.isArray(transaction.swap_path)
    ? transaction.swap_path
    : typeof transaction.swap_path === "string"
      ? transaction.swap_path.split(",").map((addr: string) => addr.trim())
      : [tokenInAddress, tokenOutAddress];

  // Fix path for Hedera native token swaps
  if (chain === "hedera") {
    swapPath = fixHederaSwapPath(swapPath, tokenInIsNative, tokenOutIsNative);
  }

  return swapPath;
}

/**
 * Get token addresses based on chain
 */
function getTokenAddresses(
  transaction: SwapTransaction,
  chain: string,
): {
  tokenInAddress: string;
  tokenOutAddress: string;
} {
  if (chain === "hedera") {
    // Use EVM addresses for contract calls on Hedera
    return {
      tokenInAddress: transaction.token_in_address_evm || transaction.token_in_address,
      tokenOutAddress: transaction.token_out_address_evm || transaction.token_out_address,
    };
  } else {
    // For EVM chains, addresses are already in EVM format
    return {
      tokenInAddress: transaction.token_in_address,
      tokenOutAddress: transaction.token_out_address,
    };
  }
}

/**
 * Check native token balance before swap
 */
async function checkNativeTokenBalance(
  provider: ethers.Provider,
  address: string,
  amountIn: string,
  amountInSmallestUnit: bigint,
  balance: bigint,
  chain: string,
  tokenSymbol: string,
  feeData: ethers.FeeData,
): Promise<void> {
  let balanceForComparison: bigint;

  if (chain === "hedera") {
    // Convert balance from tinybars to wei for comparison
    balanceForComparison = balance * BigInt(10 ** 10); // Convert tinybars to wei
  } else {
    balanceForComparison = balance;
  }

  console.log(`   Balance Check:`);
  console.log(`     Amount In: ${amountIn} ${tokenSymbol}`);
  console.log(`     Amount In (smallest unit): ${amountInSmallestUnit.toString()}`);
  console.log(`     Balance (smallest unit): ${balance.toString()}`);
  if (chain === "hedera") {
    console.log(
      `     Balance (converted to wei for comparison): ${balanceForComparison.toString()}`,
    );
  }

  let totalCost: bigint;
  let errorMessage: string;

  if (chain === "hedera") {
    // Hedera: only check if balance >= amountIn (gas is handled separately)
    totalCost = amountInSmallestUnit;

    console.log(`     Chain: Hedera - checking balance >= amountIn only (gas handled separately)`);
    console.log(`     Required: ${totalCost.toString()} wei (for contract call)`);

    if (balanceForComparison < totalCost) {
      const balanceTinybars = balance;
      const totalCostTinybars = totalCost / BigInt(10 ** 10);
      errorMessage = formatInsufficientBalanceError(balanceTinybars, totalCostTinybars);
      throw new Error(errorMessage);
    }
  } else {
    // EVM chains: check balance >= amountIn + gasCost
    const gasPrice = feeData.gasPrice || BigInt(0);
    const estimatedGas = BigInt(15_000_000);
    const gasCost = gasPrice * estimatedGas;
    totalCost = amountInSmallestUnit + gasCost;

    console.log(`     Chain: EVM - checking balance >= amountIn + gasCost`);
    console.log(`     Gas Price: ${gasPrice.toString()} wei`);
    console.log(`     Gas Cost: ${gasCost.toString()} wei`);
    console.log(`     Required: ${totalCost.toString()} wei`);

    if (balanceForComparison < totalCost) {
      const balanceFormatted = ethers.formatEther(balanceForComparison);
      const totalCostFormatted = ethers.formatEther(totalCost);
      errorMessage = `Insufficient funds: Need ${totalCostFormatted} ${tokenSymbol}, but have ${balanceFormatted} ${tokenSymbol}`;
      throw new Error(errorMessage);
    }
  }

  console.log(`   ✅ Balance check passed`);
}

/**
 * Ensure token approval for ERC20 swaps
 */
async function ensureTokenApprovalForSwap(
  provider: ethers.Provider,
  signer: ethers.Signer,
  tokenInAddress: string,
  address: string,
  routerAddress: string,
  amountIn: string,
  chain: string,
  tokenSymbol: string,
  balanceInfo: { balance: string; balanceRaw: string; decimals: number } | null,
): Promise<void> {
  console.log(`   🔐 Checking token approval for ERC20 token swap...`);

  // Get token decimals
  let tokenDecimals = 18;
  try {
    tokenDecimals = await getTokenDecimals(provider, tokenInAddress);
    console.log(`   Token decimals: ${tokenDecimals}`);
  } catch (error: any) {
    console.warn(`   Could not fetch token decimals, using fallback: ${error.message}`);
    if (balanceInfo) {
      tokenDecimals = balanceInfo.decimals;
    } else if (chain === "hedera") {
      if (tokenSymbol === "USDC" || tokenSymbol === "USDT") {
        tokenDecimals = 6;
      } else {
        tokenDecimals = 8;
      }
    }
  }

  const amountInSmallestUnit = parseTokenAmount(amountIn, chain, tokenDecimals);

  console.log(`   Approval check:`);
  console.log(`     Token: ${tokenSymbol} (${tokenInAddress})`);
  console.log(`     Amount: ${amountIn} (${amountInSmallestUnit.toString()} in smallest unit)`);
  console.log(`     Router: ${routerAddress}`);

  try {
    await ensureTokenApproval(
      provider,
      signer,
      tokenInAddress,
      address,
      routerAddress,
      amountInSmallestUnit,
      chain,
    );
    console.log(`   ✅ Token approval confirmed`);
  } catch (error: any) {
    console.warn(`   ⚠️  Token approval failed: ${error.message}`);
    console.log(`   ℹ️  Attempting swap anyway - contract will handle approval requirement`);
  }
}

/**
 * Execute swap transaction
 */
export async function executeSwap(
  transaction: SwapTransaction,
  walletClient: any, // WalletClient from wagmi/viem
  address: string,
  callbacks?: SwapExecutionCallbacks,
): Promise<SwapExecutionResult> {
  const { onStateChange, onError, onTxHash, onProgress } = callbacks || {};

  try {
    onStateChange?.("swapping");

    const chain = transaction.chain || "hedera";
    const { tokenInAddress, tokenOutAddress } = getTokenAddresses(transaction, chain);
    const amountIn = transaction.amount_in;
    const amountOutMin = "0"; // Hardcoded for testing - no slippage protection
    const amountOut = "0";

    // Check if tokens are native
    const tokenInIsNative = isNativeTokenCheck(tokenInAddress, transaction.token_in_symbol, chain);
    const tokenOutIsNative = isNativeTokenCheck(
      tokenOutAddress,
      transaction.token_out_symbol,
      chain,
    );

    // Prepare swap path
    const swapPath = prepareSwapPath(
      transaction,
      tokenInAddress,
      tokenOutAddress,
      chain,
      tokenInIsNative,
      tokenOutIsNative,
    );

    const routerAddress = transaction.pool_address || (transaction as any).pool_address;
    if (!routerAddress) {
      throw new Error("Router address not found in transaction data");
    }

    onProgress?.("🔄 Executing Swap...");
    console.log("🔄 Executing Swap:", {
      chain,
      tokenIn: transaction.token_in_symbol,
      tokenOut: transaction.token_out_symbol,
      amountIn,
      path: swapPath,
      recipient: address,
    });

    // Create provider and signer
    const provider = new ethers.BrowserProvider(walletClient as any);
    const signer = await provider.getSigner();

    // Check wallet balance
    let balance: bigint = BigInt(0);
    let balanceInfo: { balance: string; balanceRaw: string; decimals: number } | null = null;

    let balanceTokenAddress: string | undefined;
    if (!tokenInIsNative) {
      if (chain === "hedera") {
        balanceTokenAddress = transaction.token_in_address_hedera || transaction.token_in_address;
      } else {
        balanceTokenAddress = tokenInAddress;
      }
    }

    try {
      balanceInfo = await getBalanceUtil(address, balanceTokenAddress, chain, provider, "mainnet");
      balance = BigInt(balanceInfo.balanceRaw);
      console.log(`   Wallet Balance: ${balanceInfo.balance} ${transaction.token_in_symbol}`);
    } catch (error: any) {
      console.warn(`   Balance check failed: ${error.message}`);
    }

    // Calculate deadline (20 minutes from now)
    const deadline = Math.floor(Date.now() / 1000) + 20 * 60;

    // Create contract instance
    const contract = new ethers.Contract(routerAddress, ROUTER_ABI, signer);

    // Get gas price
    const feeData = await provider.getFeeData();
    console.log(`   Gas Price: ${feeData.gasPrice?.toString()} wei`);

    // Get token decimals for proper amount parsing
    let tokenInDecimals: number | undefined;
    let tokenOutDecimals: number | undefined;

    // Fetch token in decimals
    if (!tokenInIsNative) {
      try {
        tokenInDecimals = await getTokenDecimals(provider, tokenInAddress);
        console.log(`   Token In (${transaction.token_in_symbol}) decimals: ${tokenInDecimals}`);
      } catch (error: any) {
        console.warn(`   Could not fetch token in decimals: ${error.message}`);
        if (balanceInfo) {
          tokenInDecimals = balanceInfo.decimals;
        } else if (chain === "hedera") {
          // Fallback for Hedera tokens
          if (transaction.token_in_symbol === "USDC" || transaction.token_in_symbol === "USDT") {
            tokenInDecimals = 6;
          } else {
            tokenInDecimals = 8;
          }
        }
      }
    }

    // Fetch token out decimals
    if (!tokenOutIsNative) {
      try {
        tokenOutDecimals = await getTokenDecimals(provider, tokenOutAddress);
        console.log(`   Token Out (${transaction.token_out_symbol}) decimals: ${tokenOutDecimals}`);
      } catch (error: any) {
        console.warn(`   Could not fetch token out decimals: ${error.message}`);
        if (chain === "hedera") {
          // Fallback for Hedera tokens
          if (transaction.token_out_symbol === "USDC" || transaction.token_out_symbol === "USDT") {
            tokenOutDecimals = 6;
          } else {
            tokenOutDecimals = 8;
          }
        }
      }
    }

    // Prepare swap parameters
    const { functionName, params, overrides } = prepareSwapParams(
      tokenInAddress,
      tokenOutAddress,
      transaction.token_in_symbol,
      transaction.token_out_symbol,
      amountIn,
      amountOutMin,
      amountOut,
      swapPath,
      address,
      deadline,
      chain,
      true, // exactInput = true
      tokenInDecimals,
      tokenOutDecimals,
    );

    console.log(`   Using swap function: ${functionName}`);
    console.log(
      `   Parameters:`,
      params.map((p) => p.toString()),
    );
    console.log(`   Overrides:`, {
      ...overrides,
      value: overrides.value?.toString(),
    });
    console.log(`   Swap Path:`, swapPath);
    console.log(`   Router Address:`, routerAddress);

    // Check balance for native token swaps
    if (tokenInIsNative && overrides.value) {
      let amountInSmallestUnit: bigint;

      if (chain === "hedera") {
        amountInSmallestUnit = ethers.parseEther(amountIn);
      } else {
        amountInSmallestUnit = parseTokenAmount(amountIn, chain, 18);
      }

      await checkNativeTokenBalance(
        provider,
        address,
        amountIn,
        amountInSmallestUnit,
        balance,
        chain,
        transaction.token_in_symbol,
        feeData,
      );
    }

    // Check and request token approval for ERC20 swaps
    if (!tokenInIsNative) {
      await ensureTokenApprovalForSwap(
        provider,
        signer,
        tokenInAddress,
        address,
        routerAddress,
        amountIn,
        chain,
        transaction.token_in_symbol,
        balanceInfo,
      );
    } else {
      console.log(`   ℹ️  Native token swap - no approval needed`);
    }

    // Execute swap
    const swapOverrides: ethers.Overrides = { ...overrides };

    // For Hedera, never set gasPrice - let RPC handle it
    if (chain !== "hedera") {
      swapOverrides.gasPrice = feeData.gasPrice;
    } else {
      if (swapOverrides.gasPrice !== undefined) {
        delete swapOverrides.gasPrice;
      }
    }

    onProgress?.("Sending transaction...");
    const txResponse = await executeSwapTx(contract, functionName, params, swapOverrides, chain);

    console.log("✅ Transaction sent!");
    console.log(`   Transaction Hash: ${txResponse.hash}`);
    onTxHash?.(txResponse.hash);

    // Wait for transaction receipt
    onProgress?.("Waiting for transaction confirmation...");
    console.log("🔄 Waiting for transaction confirmation...");
    const receipt = await txResponse.wait();

    if (!receipt || receipt.status !== 1) {
      throw new Error(`Transaction failed with status: ${receipt?.status}`);
    }

    console.log("✅ Transaction confirmed!");
    console.log(`   Block Number: ${receipt.blockNumber}`);
    console.log(`   Gas Used: ${receipt.gasUsed.toString()}`);

    onStateChange?.("done");

    return {
      success: true,
      txHash: txResponse.hash,
      receipt,
    };
  } catch (err: any) {
    console.error("Swap execution error:", err);
    onStateChange?.("idle");
    const errorMessage = err?.message || "Swap failed. Please try again.";
    onError?.(errorMessage);

    return {
      success: false,
      error: errorMessage,
    };
  }
}
