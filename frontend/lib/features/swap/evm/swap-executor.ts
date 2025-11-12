/**
 * EVM Swap Executor
 *
 * Chain-specific swap execution logic for EVM-compatible chains (Polygon, Ethereum, etc.).
 * Handles EVM-specific token swaps, approvals, and balance checks.
 */

import { ethers } from "ethers";
import { ROUTER_ABI } from "@/lib/shared/contracts/router-abi";
import { UNISWAP_V3_ROUTER_ABI } from "@/lib/shared/contracts/uniswap-v3-router-abi";
import * as evmSwapUtils from "@/lib/shared/blockchain/evm/swap-utils";
import { ensureTokenApproval, getTokenDecimals } from "@/lib/shared/blockchain/token-approval";
import { getRouterAddress } from "@/lib/constants/dexes";
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
): string[] {
  const swapPath = parseSwapPath(transaction);
  return swapPath.length > 0 ? swapPath : [tokenInAddress, tokenOutAddress];
}

/**
 * Get token addresses for EVM chains
 */
function getTokenAddresses(transaction: SwapTransaction): {
  tokenInAddress: string;
  tokenOutAddress: string;
} {
  return {
    tokenInAddress: transaction.token_in_address,
    tokenOutAddress: transaction.token_out_address,
  };
}

/**
 * Log balance check details
 */
function logBalanceCheck(
  amountIn: string,
  amountInSmallestUnit: bigint,
  balance: bigint,
  tokenSymbol: string,
): void {
  console.log(`   Balance Check:`);
  console.log(`     Amount In: ${amountIn} ${tokenSymbol}`);
  console.log(`     Amount In (smallest unit): ${amountInSmallestUnit.toString()}`);
  console.log(`     Balance (smallest unit): ${balance.toString()}`);
}

/**
 * Calculate gas cost
 * Uses realistic gas estimate for swaps (200k-500k gas units)
 */
function calculateGasCost(feeData: ethers.FeeData): bigint {
  const gasPrice = feeData.gasPrice || BigInt(0);
  // Realistic gas estimate for Uniswap swaps: 200k-500k depending on path length
  // Using 300k as a safe estimate
  const estimatedGas = BigInt(300_000);
  return gasPrice * estimatedGas;
}

/**
 * Log gas details
 */
function logGasDetails(gasPrice: bigint, gasCost: bigint, totalCost: bigint): void {
  console.log(`     Chain: EVM - checking balance >= amountIn + gasCost`);
  console.log(`     Gas Price: ${gasPrice.toString()} wei`);
  console.log(`     Gas Cost: ${gasCost.toString()} wei`);
  console.log(`     Required: ${totalCost.toString()} wei`);
}

/**
 * Validate EVM balance
 */
function validateEVMBalance(
  balanceForComparison: bigint,
  totalCost: bigint,
  tokenSymbol: string,
): void {
  if (balanceForComparison < totalCost) {
    const balanceFormatted = ethers.formatEther(balanceForComparison);
    const totalCostFormatted = ethers.formatEther(totalCost);
    const errorMessage = `Insufficient funds: Need ${totalCostFormatted} ${tokenSymbol}, but have ${balanceFormatted} ${tokenSymbol}`;
    throw new Error(errorMessage);
  }
}

/**
 * Check native token balance before swap (EVM-specific)
 */
async function checkNativeTokenBalance(
  provider: ethers.Provider,
  address: string,
  amountIn: string,
  amountInSmallestUnit: bigint,
  balance: bigint,
  tokenSymbol: string,
  feeData: ethers.FeeData,
): Promise<void> {
  const balanceForComparison = balance;
  logBalanceCheck(amountIn, amountInSmallestUnit, balance, tokenSymbol);
  const gasCost = calculateGasCost(feeData);
  const totalCost = amountInSmallestUnit + gasCost;
  const gasPrice = feeData.gasPrice || BigInt(0);
  logGasDetails(gasPrice, gasCost, totalCost);
  validateEVMBalance(balanceForComparison, totalCost, tokenSymbol);
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
  balanceInfo: { balance: string; balanceRaw: string; decimals: number } | null,
): Promise<number> {
  try {
    return await getTokenDecimals(provider, tokenInAddress);
  } catch (error: any) {
    console.warn(`   Could not fetch token decimals, using fallback: ${error.message}`);
    return balanceInfo ? balanceInfo.decimals : 18;
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
  chain: string,
): Promise<void> {
  dispatch(setApprovalStatusField({ status: "needs_approval" }));
  await ensureTokenApproval(
    provider,
    signer,
    tokenInAddress,
    address,
    routerAddress,
    amountInSmallestUnit,
    chain,
  );
  dispatch(setApprovalStatusField({ status: "approved" }));
  console.log(`   ✅ Token approval confirmed`);
}

/**
 * Ensure token approval for ERC20 swaps (EVM-specific with Redux)
 */
async function ensureTokenApprovalForSwap(
  dispatch: AppDispatch,
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
  const approvalStatus = createApprovalStatus(tokenInAddress, tokenSymbol, routerAddress, amountIn);
  dispatch(setApprovalStatus(approvalStatus));
  const tokenDecimals = await getTokenDecimalsWithFallback(provider, tokenInAddress, balanceInfo);
  console.log(`   Token decimals: ${tokenDecimals}`);
  const amountInSmallestUnit = evmSwapUtils.parseTokenAmount(
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
      chain,
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
  const amountIn = transaction.amount_in || "0";
  // Validate amount
  if (!amountIn || amountIn === "0" || parseFloat(amountIn) <= 0) {
    throw new Error(`Invalid swap amount: ${amountIn}. Amount must be greater than 0.`);
  }
  return {
    amountIn,
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
  chain: string,
): { tokenInIsNative: boolean; tokenOutIsNative: boolean } {
  return {
    tokenInIsNative: evmSwapUtils.isNative(tokenInAddress, tokenInSymbol, chain),
    tokenOutIsNative: evmSwapUtils.isNative(tokenOutAddress, tokenOutSymbol, chain),
  };
}

/**
 * Get Uniswap router address for Polygon
 * Uses Uniswap V3 SwapRouter: 0xE592427A0AEce92De3Edee1F18E0157C05861564
 * This is the official Uniswap V3 SwapRouter deployed on Polygon
 */
function getUniswapRouterAddress(chain: string): string {
  if (chain.toLowerCase() === "polygon") {
    const routerAddress = getRouterAddress("polygon", "uniswap");
    if (!routerAddress) {
      // Fallback to known Uniswap V3 router address for Polygon
      const fallbackAddress = "0xE592427A0AEce92De3Edee1F18E0157C05861564";
      console.log(`   Using Uniswap V3 router (fallback): ${fallbackAddress}`);
      return fallbackAddress;
    }
    return routerAddress;
  }
  throw new Error(`Uniswap is only supported on Polygon, got chain: ${chain}`);
}

/**
 * Validate router address
 */
function validateRouterAddress(routerAddress: string | undefined, chain: string): string {
  // For Polygon, always use Uniswap router
  if (chain.toLowerCase() === "polygon") {
    return getUniswapRouterAddress(chain);
  }
  // For other chains, use provided address or throw error
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
  chain: string,
  amountIn: string,
  swapPath: string[],
  address: string,
  onProgress?: (message: string) => void,
): void {
  onProgress?.("🔄 Executing Swap...");
  console.log("🔄 Executing Swap (EVM):", {
    chain,
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
 * For native tokens, return undefined to fetch native balance
 */
function getBalanceTokenAddress(
  tokenInIsNative: boolean,
  tokenInAddress: string,
): string | undefined {
  if (tokenInIsNative) {
    return undefined; // Fetch native balance
  }
  // Check if address is Polygon native token address
  if (tokenInAddress.toLowerCase() === "0x0000000000000000000000000000000000001010") {
    return undefined; // Treat as native
  }
  return tokenInAddress;
}

/**
 * Fetch wallet balance
 */
async function fetchWalletBalance(
  provider: ethers.Provider,
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
    balanceInfo = await evmSwapUtils.getBalance(provider, address, balanceTokenAddress);
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
 * Check if router is Uniswap V3
 */
function isUniswapV3Router(routerAddress: string): boolean {
  return routerAddress.toLowerCase() === "0xE592427A0AEce92De3Edee1F18E0157C05861564".toLowerCase();
}

/**
 * Create contract instance with appropriate ABI
 */
function createContract(routerAddress: string, signer: ethers.Signer): ethers.Contract {
  // Use Uniswap V3 ABI for Uniswap V3 router, otherwise use standard router ABI
  const abi = isUniswapV3Router(routerAddress) ? UNISWAP_V3_ROUTER_ABI : ROUTER_ABI;
  return new ethers.Contract(routerAddress, abi, signer);
}

/**
 * Get fee data with Polygon RPC compatibility
 * Polygon doesn't support EIP-1559 methods, so we handle errors gracefully
 */
async function getFeeData(provider: ethers.Provider, chain: string): Promise<ethers.FeeData> {
  try {
    const feeData = await provider.getFeeData();
    // If gasPrice is null, try to get it from the latest block
    if (!feeData.gasPrice && chain.toLowerCase() === "polygon") {
      const block = await provider.getBlock("latest");
      let gasPrice: bigint;
      if (block && block.baseFeePerGas) {
        // Use baseFeePerGas * 2 as a safe gas price for Polygon
        gasPrice = block.baseFeePerGas * BigInt(2);
      } else {
        // Fallback: use a reasonable gas price for Polygon (50 gwei)
        gasPrice = BigInt(50_000_000_000);
      }
      // Create new FeeData with gasPrice
      return {
        gasPrice,
        maxFeePerGas: feeData.maxFeePerGas,
        maxPriorityFeePerGas: feeData.maxPriorityFeePerGas,
        toJSON: feeData.toJSON,
      };
    }
    console.log(`   Gas Price: ${feeData.gasPrice?.toString()} wei`);
    return feeData;
  } catch (error: any) {
    // If EIP-1559 methods fail (like on Polygon), use legacy gas
    console.warn(`   Fee data fetch failed, using fallback: ${error.message}`);
    if (chain.toLowerCase() === "polygon") {
      // Polygon fallback: use reasonable gas price (50 gwei)
      const fallbackGasPrice = BigInt(50_000_000_000);
      return {
        gasPrice: fallbackGasPrice,
        maxFeePerGas: null,
        maxPriorityFeePerGas: null,
        toJSON: () => ({ gasPrice: fallbackGasPrice.toString() }),
      };
    }
    throw error;
  }
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
    return balanceInfo ? balanceInfo.decimals : undefined;
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
  chain: string,
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
    // Fallback: USDC/USDT use 6 decimals on Polygon/Ethereum
    if (tokenOutSymbol === "USDC" || tokenOutSymbol === "USDT") {
      return 6;
    }
    // Default to 18 for other tokens
    return 18;
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
  chain: string,
  routerAddress: string,
  tokenInDecimals: number | undefined,
  tokenOutDecimals: number | undefined,
): ReturnType<typeof evmSwapUtils.prepareSwapParams> {
  return evmSwapUtils.prepareSwapParams(
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
    chain,
    true,
    tokenInDecimals,
    tokenOutDecimals,
    routerAddress,
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
  tokenInAddress: string,
  tokenInSymbol: string,
  balance: bigint,
  feeData: ethers.FeeData,
): Promise<void> {
  if (tokenInIsNative && overrides.value) {
    const amountInSmallestUnit = evmSwapUtils.parseTokenAmount(
      amountIn,
      tokenInAddress,
      tokenInSymbol,
      18,
    );
    await checkNativeTokenBalance(
      provider,
      address,
      amountIn,
      amountInSmallestUnit,
      balance,
      tokenInSymbol,
      feeData,
    );
  }
}

/**
 * Check if address is native token address
 */
function isNativeTokenAddress(address: string): boolean {
  const addrLower = address.toLowerCase();
  return (
    addrLower === "0x0000000000000000000000000000000000000000" ||
    addrLower === "0x0000000000000000000000000000000000001010" // Polygon native
  );
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
  chain: string,
  tokenInSymbol: string,
  balanceInfo: { balance: string; balanceRaw: string; decimals: number } | null,
): Promise<void> {
  // Skip approval for native tokens (including Polygon native address)
  if (tokenInIsNative || isNativeTokenAddress(tokenInAddress)) {
    console.log(`   ℹ️  Native token swap - no approval needed`);
    return;
  }
  // Validate amount before approval
  if (!amountIn || amountIn === "0" || parseFloat(amountIn) <= 0) {
    throw new Error(`Invalid swap amount: ${amountIn}. Amount must be greater than 0.`);
  }
  await ensureTokenApprovalForSwap(
    dispatch,
    provider,
    signer,
    tokenInAddress,
    address,
    routerAddress,
    amountIn,
    chain,
    tokenInSymbol,
    balanceInfo,
  );
}

/**
 * Prepare swap overrides
 * For Polygon, only use gasPrice (legacy), not EIP-1559 fields
 */
function prepareSwapOverrides(
  overrides: ethers.Overrides,
  feeData: ethers.FeeData,
  chain: string,
): ethers.Overrides {
  const swapOverrides: ethers.Overrides = { ...overrides };
  // Polygon uses legacy gas pricing
  if (chain.toLowerCase() === "polygon") {
    swapOverrides.gasPrice = feeData.gasPrice;
    // Remove EIP-1559 fields if present
    delete (swapOverrides as any).maxFeePerGas;
    delete (swapOverrides as any).maxPriorityFeePerGas;
  } else {
    // For other chains, use EIP-1559 if available
    if (feeData.maxFeePerGas) {
      swapOverrides.maxFeePerGas = feeData.maxFeePerGas;
    }
    if (feeData.maxPriorityFeePerGas) {
      swapOverrides.maxPriorityFeePerGas = feeData.maxPriorityFeePerGas;
    }
    if (feeData.gasPrice && !feeData.maxFeePerGas) {
      swapOverrides.gasPrice = feeData.gasPrice;
    }
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
  return await evmSwapUtils.executeSwap(contract, functionName, params, swapOverrides);
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
  console.error("Swap execution error (EVM):", err);
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
 * Execute swap transaction for EVM chains
 */
export async function executeSwapEVM(
  transaction: SwapTransaction,
  walletClient: any,
  address: string,
  dispatch: AppDispatch,
  callbacks?: SwapExecutionCallbacks,
): Promise<SwapExecutionResult> {
  const { onStateChange, onError, onTxHash, onProgress } = callbacks || {};
  const chain = transaction.chain || "polygon";

  try {
    initializeSwapState(dispatch, onStateChange);
    const { tokenInAddress, tokenOutAddress } = getTokenAddresses(transaction);
    const { amountIn, amountOutMin, amountOut } = getSwapAmounts(transaction);
    const { tokenInIsNative, tokenOutIsNative } = checkNativeTokens(
      tokenInAddress,
      tokenOutAddress,
      transaction.token_in_symbol,
      transaction.token_out_symbol,
      chain,
    );
    const swapPath = prepareSwapPath(transaction, tokenInAddress, tokenOutAddress);
    const routerAddress = validateRouterAddress(
      transaction.pool_address || (transaction as any).pool_address,
      chain,
    );
    console.log(`   ✅ Using Uniswap V3 for ${chain} swaps`);
    console.log(`   Router Address: ${routerAddress}`);
    logSwapStart(transaction, chain, amountIn, swapPath, address, onProgress);

    // Create provider to check current network
    const tempProvider = new ethers.BrowserProvider(walletClient as any);
    const currentChainId = await getCurrentChainId(tempProvider);
    const { needsSwitch, requiredChainId } = checkNetworkSwitch(currentChainId, chain);

    // Request network switch if needed
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

    const { provider, signer } = await createProviderAndSigner(walletClient);
    const balanceTokenAddress = getBalanceTokenAddress(tokenInIsNative, tokenInAddress);
    const { balance, balanceInfo } = await fetchWalletBalance(
      provider,
      address,
      balanceTokenAddress,
      transaction.token_in_symbol,
    );
    const deadline = calculateDeadline();
    const contract = createContract(routerAddress, signer);
    const feeData = await getFeeData(provider, chain);
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
      chain,
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
      chain,
      routerAddress,
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
      tokenInAddress,
      transaction.token_in_symbol,
      balance,
      feeData,
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
      chain,
      transaction.token_in_symbol,
      balanceInfo,
    );
    const swapOverrides = prepareSwapOverrides(overrides, feeData, chain);
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
