/**
 * Hedera Swap Executor
 *
 * Chain-specific swap execution logic for Hedera network.
 * Handles Hedera-specific token swaps, approvals, and balance checks.
 */

import { ethers } from "ethers";
import { ROUTER_ABI } from "@/lib/shared/contracts/router-abi";
import * as hederaSwapUtils from "@/lib/shared/blockchain/hedera/swap-utils";
import { formatInsufficientBalanceError } from "@/lib/shared/blockchain/hedera/hbar-operations";
import { ensureTokenApproval, getTokenDecimals } from "@/lib/shared/blockchain/token-approval";
import { getChainId } from "@/lib/shared/blockchain/network-utils";
import type { AppDispatch } from "@/lib/store";
import {
  setApprovalStatus,
  setApprovalStatusField,
  setSwapping,
  setSwapError,
  setTxHash,
  type ApprovalStatus,
} from "@/lib/store/slices/swapSlice";
import type { SwapTransaction, SwapExecutionResult, SwapExecutionCallbacks } from "../types";

// Constants
const WHBAR_ADDRESS = "0x0000000000000000000000000000000000163B5a";
const ZERO_ADDRESS = "0x0000000000000000000000000000000000000000";

/**
 * Replace zero address with WHBAR in path
 */
function replaceZeroAddress(fixedPath: string[], index: number): void {
  if (fixedPath[index]?.toLowerCase() === ZERO_ADDRESS.toLowerCase()) {
    fixedPath[index] = WHBAR_ADDRESS;
    console.log(`   Fixed swap path[${index}]: ${ZERO_ADDRESS} -> ${WHBAR_ADDRESS}`);
  }
}

/**
 * Fix first token if native
 */
function fixFirstTokenIfNative(fixedPath: string[], tokenInIsNative: boolean): void {
  if (tokenInIsNative && fixedPath[0]?.toLowerCase() !== WHBAR_ADDRESS.toLowerCase()) {
    fixedPath[0] = WHBAR_ADDRESS;
    console.log(`   Fixed swap path[0] (tokenIn is native): ${fixedPath[0]} -> ${WHBAR_ADDRESS}`);
  }
}

/**
 * Fix last token if native
 */
function fixLastTokenIfNative(fixedPath: string[], tokenOutIsNative: boolean): void {
  const lastIndex = fixedPath.length - 1;
  if (
    tokenOutIsNative &&
    lastIndex >= 0 &&
    fixedPath[lastIndex]?.toLowerCase() !== WHBAR_ADDRESS.toLowerCase()
  ) {
    fixedPath[lastIndex] = WHBAR_ADDRESS;
    console.log(
      `   Fixed swap path[${lastIndex}] (tokenOut is native): ${fixedPath[lastIndex]} -> ${WHBAR_ADDRESS}`,
    );
  }
}

/**
 * Fix swap path for Hedera native token swaps
 */
function fixHederaSwapPath(
  swapPath: string[],
  tokenInIsNative: boolean,
  tokenOutIsNative: boolean,
): string[] {
  const fixedPath = [...swapPath];
  for (let i = 0; i < fixedPath.length; i++) {
    replaceZeroAddress(fixedPath, i);
  }
  fixFirstTokenIfNative(fixedPath, tokenInIsNative);
  fixLastTokenIfNative(fixedPath, tokenOutIsNative);
  console.log(`   Final swap path: ${fixedPath.join(" -> ")}`);
  return fixedPath;
}

/**
 * Parse swap path from transaction
 */
function parseSwapPath(transaction: SwapTransaction): string[] {
  if (Array.isArray(transaction.swap_path)) {
    return transaction.swap_path;
  }
  if (typeof transaction.swap_path === "string") {
    return transaction.swap_path.split(",").map((addr: string) => addr.trim());
  }
  return [];
}

/**
 * Prepare swap path from transaction data
 */
function prepareSwapPath(
  transaction: SwapTransaction,
  tokenInAddress: string,
  tokenOutAddress: string,
  tokenInIsNative: boolean,
  tokenOutIsNative: boolean,
): string[] {
  let swapPath = parseSwapPath(transaction);
  if (swapPath.length === 0) {
    swapPath = [tokenInAddress, tokenOutAddress];
  }
  return fixHederaSwapPath(swapPath, tokenInIsNative, tokenOutIsNative);
}

/**
 * Get token addresses for Hedera
 */
function getTokenAddresses(transaction: SwapTransaction): {
  tokenInAddress: string;
  tokenOutAddress: string;
} {
  return {
    tokenInAddress: transaction.token_in_address_evm || transaction.token_in_address,
    tokenOutAddress: transaction.token_out_address_evm || transaction.token_out_address,
  };
}

/**
 * Log balance check details
 */
function logBalanceCheck(
  amountIn: string,
  amountInSmallestUnit: bigint,
  balance: bigint,
  balanceForComparison: bigint,
  tokenSymbol: string,
): void {
  console.log(`   Balance Check:`);
  console.log(`     Amount In: ${amountIn} ${tokenSymbol}`);
  console.log(`     Amount In (smallest unit): ${amountInSmallestUnit.toString()}`);
  console.log(`     Balance (smallest unit): ${balance.toString()}`);
  console.log(`     Balance (converted to wei for comparison): ${balanceForComparison.toString()}`);
}

/**
 * Validate balance for Hedera native swap
 */
function validateHederaBalance(
  balanceForComparison: bigint,
  totalCost: bigint,
  balance: bigint,
): void {
  if (balanceForComparison < totalCost) {
    const balanceTinybars = balance;
    const totalCostTinybars = totalCost / BigInt(10 ** 10);
    const errorMessage = formatInsufficientBalanceError(balanceTinybars, totalCostTinybars);
    throw new Error(errorMessage);
  }
}

/**
 * Check native token balance before swap (Hedera-specific)
 */
async function checkNativeTokenBalance(
  provider: ethers.Provider,
  address: string,
  amountIn: string,
  amountInSmallestUnit: bigint,
  balance: bigint,
  tokenSymbol: string,
): Promise<void> {
  const balanceForComparison = balance * BigInt(10 ** 10);
  logBalanceCheck(amountIn, amountInSmallestUnit, balance, balanceForComparison, tokenSymbol);
  const totalCost = amountInSmallestUnit;
  console.log(`     Chain: Hedera - checking balance >= amountIn only (gas handled separately)`);
  console.log(`     Required: ${totalCost.toString()} wei (for contract call)`);
  validateHederaBalance(balanceForComparison, totalCost, balance);
  console.log(`   ✅ Balance check passed`);
}

/**
 * Create initial approval status
 */
function createApprovalStatus(
  tokenInAddress: string,
  tokenSymbol: string,
  routerAddress: string,
  amountIn: string,
): ApprovalStatus {
  return {
    tokenAddress: tokenInAddress,
    tokenSymbol,
    spender: routerAddress,
    amount: amountIn,
    status: "checking",
  };
}

/**
 * Get token decimals with fallback
 */
async function getTokenDecimalsWithFallback(
  provider: ethers.Provider,
  tokenInAddress: string,
  tokenSymbol: string,
  balanceInfo: { balance: string; balanceRaw: string; decimals: number } | null,
): Promise<number> {
  try {
    return await getTokenDecimals(provider, tokenInAddress);
  } catch (error: any) {
    console.warn(`   Could not fetch token decimals, using fallback: ${error.message}`);
    if (balanceInfo) {
      return balanceInfo.decimals;
    }
    return tokenSymbol === "USDC" || tokenSymbol === "USDT" ? 6 : 8;
  }
}

/**
 * Log approval check details
 */
function logApprovalCheck(
  tokenSymbol: string,
  tokenInAddress: string,
  amountIn: string,
  amountInSmallestUnit: bigint,
  routerAddress: string,
): void {
  console.log(`   Approval check:`);
  console.log(`     Token: ${tokenSymbol} (${tokenInAddress})`);
  console.log(`     Amount: ${amountIn} (${amountInSmallestUnit.toString()} in smallest unit)`);
  console.log(`     Router: ${routerAddress}`);
}

/**
 * Execute token approval
 */
async function executeApproval(
  dispatch: AppDispatch,
  provider: ethers.Provider,
  signer: ethers.Signer,
  tokenInAddress: string,
  address: string,
  routerAddress: string,
  amountInSmallestUnit: bigint,
): Promise<void> {
  dispatch(setApprovalStatusField({ status: "needs_approval" }));
  await ensureTokenApproval(
    provider,
    signer,
    tokenInAddress,
    address,
    routerAddress,
    amountInSmallestUnit,
    "hedera",
  );
  dispatch(setApprovalStatusField({ status: "approved" }));
  console.log(`   ✅ Token approval confirmed`);
}

/**
 * Ensure token approval for ERC20 swaps (Hedera-specific with Redux)
 */
async function ensureTokenApprovalForSwap(
  dispatch: AppDispatch,
  provider: ethers.Provider,
  signer: ethers.Signer,
  tokenInAddress: string,
  address: string,
  routerAddress: string,
  amountIn: string,
  tokenSymbol: string,
  balanceInfo: { balance: string; balanceRaw: string; decimals: number } | null,
): Promise<void> {
  console.log(`   🔐 Checking token approval for ERC20 token swap...`);
  const approvalStatus = createApprovalStatus(tokenInAddress, tokenSymbol, routerAddress, amountIn);
  dispatch(setApprovalStatus(approvalStatus));
  const tokenDecimals = await getTokenDecimalsWithFallback(
    provider,
    tokenInAddress,
    tokenSymbol,
    balanceInfo,
  );
  console.log(`   Token decimals: ${tokenDecimals}`);
  const amountInSmallestUnit = hederaSwapUtils.parseTokenAmount(
    amountIn,
    tokenInAddress,
    tokenSymbol,
    tokenDecimals,
  );
  logApprovalCheck(tokenSymbol, tokenInAddress, amountIn, amountInSmallestUnit, routerAddress);
  try {
    await executeApproval(
      dispatch,
      provider,
      signer,
      tokenInAddress,
      address,
      routerAddress,
      amountInSmallestUnit,
    );
  } catch (error: any) {
    dispatch(setApprovalStatusField({ status: "error", error: error.message }));
    console.warn(`   ⚠️  Token approval failed: ${error.message}`);
    throw error;
  }
}

/**
 * Initialize swap state
 */
function initializeSwapState(
  dispatch: AppDispatch,
  onStateChange?: (state: "idle" | "swapping" | "done") => void,
): void {
  dispatch(setSwapping(true));
  onStateChange?.("swapping");
}

/**
 * Get swap amounts
 */
function getSwapAmounts(transaction: SwapTransaction): {
  amountIn: string;
  amountOutMin: string;
  amountOut: string;
} {
  return {
    amountIn: transaction.amount_in,
    amountOutMin: "0",
    amountOut: "0",
  };
}

/**
 * Check if tokens are native
 */
function checkNativeTokens(
  tokenInAddress: string,
  tokenOutAddress: string,
  tokenInSymbol: string,
  tokenOutSymbol: string,
): { tokenInIsNative: boolean; tokenOutIsNative: boolean } {
  return {
    tokenInIsNative: hederaSwapUtils.isNative(tokenInAddress, tokenInSymbol),
    tokenOutIsNative: hederaSwapUtils.isNative(tokenOutAddress, tokenOutSymbol),
  };
}

/**
 * Validate router address
 */
function validateRouterAddress(routerAddress: string | undefined): string {
  if (!routerAddress) {
    throw new Error("Router address not found in transaction data");
  }
  return routerAddress;
}

/**
 * Log swap execution start
 */
function logSwapStart(
  transaction: SwapTransaction,
  amountIn: string,
  swapPath: string[],
  address: string,
  onProgress?: (message: string) => void,
): void {
  onProgress?.("🔄 Executing Swap...");
  console.log("🔄 Executing Swap (Hedera):", {
    tokenIn: transaction.token_in_symbol,
    tokenOut: transaction.token_out_symbol,
    amountIn,
    path: swapPath,
    recipient: address,
  });
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
  requiredChain: string,
): { needsSwitch: boolean; requiredChainId: number | null } {
  const requiredChainId = getChainId(requiredChain);
  if (!requiredChainId) {
    return { needsSwitch: false, requiredChainId: null };
  }
  return {
    needsSwitch: currentChainId !== requiredChainId,
    requiredChainId,
  };
}

/**
 * Request network switch
 */
async function requestNetworkSwitch(
  walletClient: any,
  requiredChainId: number,
  chainName: string,
): Promise<void> {
  try {
    console.log(
      `   🔄 Requesting network switch to ${chainName} (Chain ID: ${requiredChainId})...`,
    );
    await walletClient.switchChain({ id: requiredChainId });
    console.log(`   ✅ Network switched to ${chainName}`);
  } catch (error: any) {
    // If switch fails, try to add the network first
    if (error.code === 4902 || error.message?.includes("Unrecognized chain")) {
      throw new Error(
        `Please add ${chainName} network to your wallet and try again. Chain ID: ${requiredChainId}`,
      );
    }
    // User rejected the switch
    if (error.code === 4001 || error.message?.includes("rejected")) {
      throw new Error(`Network switch rejected. Please switch to ${chainName} manually.`);
    }
    throw new Error(`Failed to switch network: ${error.message}`);
  }
}

/**
 * Create provider and signer
 */
async function createProviderAndSigner(walletClient: any): Promise<{
  provider: ethers.Provider;
  signer: ethers.Signer;
}> {
  const provider = new ethers.BrowserProvider(walletClient as any);
  const signer = await provider.getSigner();
  return { provider, signer };
}

/**
 * Get balance token address
 */
function getBalanceTokenAddress(
  tokenInIsNative: boolean,
  transaction: SwapTransaction,
): string | undefined {
  if (!tokenInIsNative) {
    return transaction.token_in_address_hedera || transaction.token_in_address;
  }
  return undefined;
}

/**
 * Fetch wallet balance
 */
async function fetchWalletBalance(
  address: string,
  balanceTokenAddress: string | undefined,
  tokenInSymbol: string,
): Promise<{
  balance: bigint;
  balanceInfo: { balance: string; balanceRaw: string; decimals: number } | null;
}> {
  let balance: bigint = BigInt(0);
  let balanceInfo: { balance: string; balanceRaw: string; decimals: number } | null = null;
  try {
    balanceInfo = await hederaSwapUtils.getBalance(address, balanceTokenAddress, "mainnet");
    balance = BigInt(balanceInfo.balanceRaw);
    console.log(`   Wallet Balance: ${balanceInfo.balance} ${tokenInSymbol}`);
  } catch (error: any) {
    console.warn(`   Balance check failed: ${error.message}`);
  }
  return { balance, balanceInfo };
}

/**
 * Calculate deadline
 */
function calculateDeadline(): number {
  return Math.floor(Date.now() / 1000) + 20 * 60;
}

/**
 * Create contract instance
 */
function createContract(routerAddress: string, signer: ethers.Signer): ethers.Contract {
  return new ethers.Contract(routerAddress, ROUTER_ABI, signer);
}

/**
 * Get token decimals with fallback for token in
 */
async function getTokenInDecimals(
  provider: ethers.Provider,
  tokenInAddress: string,
  tokenInSymbol: string,
  tokenInIsNative: boolean,
  balanceInfo: { balance: string; balanceRaw: string; decimals: number } | null,
): Promise<number | undefined> {
  if (tokenInIsNative) {
    return undefined;
  }
  try {
    const decimals = await getTokenDecimals(provider, tokenInAddress);
    console.log(`   Token In (${tokenInSymbol}) decimals: ${decimals}`);
    return decimals;
  } catch (error: any) {
    console.warn(`   Could not fetch token in decimals: ${error.message}`);
    if (balanceInfo) {
      return balanceInfo.decimals;
    }
    return tokenInSymbol === "USDC" || tokenInSymbol === "USDT" ? 6 : 8;
  }
}

/**
 * Get token decimals with fallback for token out
 */
async function getTokenOutDecimals(
  provider: ethers.Provider,
  tokenOutAddress: string,
  tokenOutSymbol: string,
  tokenOutIsNative: boolean,
): Promise<number | undefined> {
  if (tokenOutIsNative) {
    return undefined;
  }
  try {
    const decimals = await getTokenDecimals(provider, tokenOutAddress);
    console.log(`   Token Out (${tokenOutSymbol}) decimals: ${decimals}`);
    return decimals;
  } catch (error: any) {
    console.warn(`   Could not fetch token out decimals: ${error.message}`);
    return tokenOutSymbol === "USDC" || tokenOutSymbol === "USDT" ? 6 : 8;
  }
}

/**
 * Prepare swap parameters
 */
function prepareSwapParams(
  tokenInAddress: string,
  tokenOutAddress: string,
  tokenInSymbol: string,
  tokenOutSymbol: string,
  amountIn: string,
  amountOutMin: string,
  amountOut: string,
  swapPath: string[],
  address: string,
  deadline: number,
  tokenInDecimals: number | undefined,
  tokenOutDecimals: number | undefined,
): ReturnType<typeof hederaSwapUtils.prepareSwapParams> {
  return hederaSwapUtils.prepareSwapParams(
    tokenInAddress,
    tokenOutAddress,
    tokenInSymbol,
    tokenOutSymbol,
    amountIn,
    amountOutMin,
    amountOut,
    swapPath,
    address,
    deadline,
    true,
    tokenInDecimals,
    tokenOutDecimals,
  );
}

/**
 * Log swap parameters
 */
function logSwapParameters(
  functionName: string,
  params: any[],
  overrides: ethers.Overrides,
  swapPath: string[],
  routerAddress: string,
): void {
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
}

/**
 * Check native balance if needed
 */
async function checkNativeBalanceIfNeeded(
  tokenInIsNative: boolean,
  overrides: ethers.Overrides,
  provider: ethers.Provider,
  address: string,
  amountIn: string,
  balance: bigint,
  tokenInSymbol: string,
): Promise<void> {
  if (tokenInIsNative && overrides.value) {
    const amountInSmallestUnit = ethers.parseEther(amountIn);
    await checkNativeTokenBalance(
      provider,
      address,
      amountIn,
      amountInSmallestUnit,
      balance,
      tokenInSymbol,
    );
  }
}

/**
 * Handle token approval if needed
 */
async function handleTokenApprovalIfNeeded(
  tokenInIsNative: boolean,
  dispatch: AppDispatch,
  provider: ethers.Provider,
  signer: ethers.Signer,
  tokenInAddress: string,
  address: string,
  routerAddress: string,
  amountIn: string,
  tokenInSymbol: string,
  balanceInfo: { balance: string; balanceRaw: string; decimals: number } | null,
): Promise<void> {
  if (!tokenInIsNative) {
    await ensureTokenApprovalForSwap(
      dispatch,
      provider,
      signer,
      tokenInAddress,
      address,
      routerAddress,
      amountIn,
      tokenInSymbol,
      balanceInfo,
    );
  } else {
    console.log(`   ℹ️  Native token swap - no approval needed`);
  }
}

/**
 * Prepare swap overrides
 */
function prepareSwapOverrides(overrides: ethers.Overrides): ethers.Overrides {
  const swapOverrides: ethers.Overrides = { ...overrides };
  if (swapOverrides.gasPrice !== undefined) {
    delete swapOverrides.gasPrice;
  }
  return swapOverrides;
}

/**
 * Execute swap transaction
 */
async function executeSwapTransaction(
  contract: ethers.Contract,
  functionName: string,
  params: any[],
  swapOverrides: ethers.Overrides,
  onProgress?: (message: string) => void,
): Promise<ethers.TransactionResponse> {
  onProgress?.("Sending transaction...");
  return await hederaSwapUtils.executeSwap(contract, functionName, params, swapOverrides);
}

/**
 * Handle transaction sent
 */
function handleTransactionSent(
  txResponse: ethers.TransactionResponse,
  dispatch: AppDispatch,
  onTxHash?: (hash: string) => void,
): void {
  console.log("✅ Transaction sent!");
  console.log(`   Transaction Hash: ${txResponse.hash}`);
  dispatch(setTxHash(txResponse.hash));
  onTxHash?.(txResponse.hash);
}

/**
 * Wait for transaction confirmation
 */
async function waitForConfirmation(
  txResponse: ethers.TransactionResponse,
  onProgress?: (message: string) => void,
): Promise<ethers.TransactionReceipt | null> {
  onProgress?.("Waiting for transaction confirmation...");
  console.log("🔄 Waiting for transaction confirmation...");
  return await txResponse.wait();
}

/**
 * Validate transaction receipt
 */
function validateReceipt(receipt: ethers.TransactionReceipt | null): ethers.TransactionReceipt {
  if (!receipt || receipt.status !== 1) {
    throw new Error(`Transaction failed with status: ${receipt?.status}`);
  }
  return receipt;
}

/**
 * Log transaction confirmation
 */
function logTransactionConfirmation(receipt: ethers.TransactionReceipt): void {
  console.log("✅ Transaction confirmed!");
  console.log(`   Block Number: ${receipt.blockNumber}`);
  console.log(`   Gas Used: ${receipt.gasUsed.toString()}`);
}

/**
 * Handle swap success
 */
function handleSwapSuccess(
  txResponse: ethers.TransactionResponse,
  receipt: ethers.TransactionReceipt,
  dispatch: AppDispatch,
  onStateChange?: (state: "idle" | "swapping" | "done") => void,
): SwapExecutionResult {
  dispatch(setSwapping(false));
  onStateChange?.("done");
  return {
    success: true,
    txHash: txResponse.hash,
    receipt,
  };
}

/**
 * Handle swap error
 */
function handleSwapError(
  err: any,
  dispatch: AppDispatch,
  onStateChange?: (state: "idle" | "swapping" | "done") => void,
  onError?: (error: string) => void,
): SwapExecutionResult {
  console.error("Swap execution error (Hedera):", err);
  dispatch(setSwapping(false));
  const errorMessage = err?.message || "Swap failed. Please try again.";
  dispatch(setSwapError(errorMessage));
  onStateChange?.("idle");
  onError?.(errorMessage);
  return {
    success: false,
    error: errorMessage,
  };
}

/**
 * Execute swap transaction for Hedera
 */
export async function executeSwapHedera(
  transaction: SwapTransaction,
  walletClient: any,
  address: string,
  dispatch: AppDispatch,
  callbacks?: SwapExecutionCallbacks,
): Promise<SwapExecutionResult> {
  const { onStateChange, onError, onTxHash, onProgress } = callbacks || {};

  try {
    initializeSwapState(dispatch, onStateChange);
    const { tokenInAddress, tokenOutAddress } = getTokenAddresses(transaction);
    const { amountIn, amountOutMin, amountOut } = getSwapAmounts(transaction);
    const { tokenInIsNative, tokenOutIsNative } = checkNativeTokens(
      tokenInAddress,
      tokenOutAddress,
      transaction.token_in_symbol,
      transaction.token_out_symbol,
    );
    const swapPath = prepareSwapPath(
      transaction,
      tokenInAddress,
      tokenOutAddress,
      tokenInIsNative,
      tokenOutIsNative,
    );
    const routerAddress = validateRouterAddress(
      transaction.pool_address || (transaction as any).pool_address,
    );
    logSwapStart(transaction, amountIn, swapPath, address, onProgress);

    // Create provider to check current network
    const tempProvider = new ethers.BrowserProvider(walletClient as any);
    const currentChainId = await getCurrentChainId(tempProvider);
    const { needsSwitch, requiredChainId } = checkNetworkSwitch(currentChainId, "hedera");

    // Request network switch if needed
    if (needsSwitch && requiredChainId) {
      onProgress?.(`Please switch to Hedera network...`);
      await requestNetworkSwitch(walletClient, requiredChainId, "Hedera");
      // Wait a bit for the network to switch
      await new Promise((resolve) => setTimeout(resolve, 1000));
      // Verify the switch
      const newProvider = new ethers.BrowserProvider(walletClient as any);
      const newChainId = await getCurrentChainId(newProvider);
      if (newChainId !== requiredChainId) {
        throw new Error(`Network switch failed. Please switch to Hedera manually.`);
      }
      console.log(`   ✅ Verified network switch to Hedera (Chain ID: ${requiredChainId})`);
    }

    const { provider, signer } = await createProviderAndSigner(walletClient);
    const balanceTokenAddress = getBalanceTokenAddress(tokenInIsNative, transaction);
    const { balance, balanceInfo } = await fetchWalletBalance(
      address,
      balanceTokenAddress,
      transaction.token_in_symbol,
    );
    const deadline = calculateDeadline();
    const contract = createContract(routerAddress, signer);
    const tokenInDecimals = await getTokenInDecimals(
      provider,
      tokenInAddress,
      transaction.token_in_symbol,
      tokenInIsNative,
      balanceInfo,
    );
    const tokenOutDecimals = await getTokenOutDecimals(
      provider,
      tokenOutAddress,
      transaction.token_out_symbol,
      tokenOutIsNative,
    );
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
      tokenInDecimals,
      tokenOutDecimals,
    );
    logSwapParameters(functionName, params, overrides, swapPath, routerAddress);
    await checkNativeBalanceIfNeeded(
      tokenInIsNative,
      overrides,
      provider,
      address,
      amountIn,
      balance,
      transaction.token_in_symbol,
    );
    await handleTokenApprovalIfNeeded(
      tokenInIsNative,
      dispatch,
      provider,
      signer,
      tokenInAddress,
      address,
      routerAddress,
      amountIn,
      transaction.token_in_symbol,
      balanceInfo,
    );
    const swapOverrides = prepareSwapOverrides(overrides);
    const txResponse = await executeSwapTransaction(
      contract,
      functionName,
      params,
      swapOverrides,
      onProgress,
    );
    handleTransactionSent(txResponse, dispatch, onTxHash);
    const receipt = await waitForConfirmation(txResponse, onProgress);
    const validatedReceipt = validateReceipt(receipt);
    logTransactionConfirmation(validatedReceipt);
    return handleSwapSuccess(txResponse, validatedReceipt, dispatch, onStateChange);
  } catch (err: any) {
    return handleSwapError(err, dispatch, onStateChange, onError);
  }
}
