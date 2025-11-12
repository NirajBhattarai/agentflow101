/**
 * Hedera-specific swap execution utilities
 *
 * Handles swap transaction execution for Hedera network
 */

import { ethers } from "ethers";
import * as hederaOps from "./hedera-operations";
import { isHederaNative } from "./hedera-operations";

/**
 * Get chain type - always returns "hedera" for this module
 */
export function getChainType(): "hedera" {
  return "hedera";
}

/**
 * Parse token amount for Hedera swaps
 * For native HBAR in swaps: contract expects wei (18 decimals) for EVM compatibility
 * For tokens: use token decimals
 */
export function parseTokenAmount(
  amount: string,
  tokenAddress: string,
  tokenSymbol: string,
  decimals: number = 18,
): bigint {
  // For Hedera native (HBAR): contract expects wei (18 decimals) for EVM compatibility
  if (isHederaNative(tokenAddress)) {
    return ethers.parseEther(amount);
  }
  // For tokens: use provided decimals or default to 18
  return hederaOps.parseHederaAmount(amount, decimals);
}

/**
 * Format token amount for Hedera swaps
 */
export function formatTokenAmount(amount: bigint, decimals: number = 18): string {
  return hederaOps.formatHederaAmount(amount, decimals);
}

/**
 * Get balance for Hedera swaps
 */
export async function getBalance(
  accountAddress: string,
  tokenAddress: string | undefined,
  network: string = "mainnet",
): Promise<{ balance: string; balanceRaw: string; decimals: number }> {
  return await hederaOps.getHederaBalance(accountAddress, tokenAddress, network);
}

/**
 * Check if token is native for Hedera
 */
export function isNativeToken(tokenAddress: string): boolean {
  return hederaOps.isHederaNative(tokenAddress);
}

/**
 * Check if token symbol is native for Hedera
 */
export function isNativeSymbol(tokenSymbol: string): boolean {
  return tokenSymbol.toUpperCase() === "HBAR";
}

/**
 * Check if token is native by address or symbol
 */
export function isNative(tokenAddress: string, tokenSymbol: string): boolean {
  return isNativeToken(tokenAddress) || isNativeSymbol(tokenSymbol);
}

/**
 * Determine swap function name based on token types for Hedera
 */
export function getSwapFunctionName(
  tokenInAddress: string,
  tokenOutAddress: string,
  tokenInSymbol: string,
  tokenOutSymbol: string,
  exactInput: boolean = true,
): string {
  console.log(
    `[hedera/swap-utils] getSwapFunctionName called: tokenIn=${tokenInSymbol}(${tokenInAddress}), tokenOut=${tokenOutSymbol}(${tokenOutAddress}), exactInput=${exactInput}`,
  );
  const tokenInIsNative = isNative(tokenInAddress, tokenInSymbol);
  const tokenOutIsNative = isNative(tokenOutAddress, tokenOutSymbol);

  if (tokenInIsNative && tokenOutIsNative) {
    throw new Error("Cannot swap native token to native token");
  }

  let functionName: string;
  if (tokenInIsNative && !tokenOutIsNative) {
    // Native -> Token
    functionName = exactInput ? "swapExactETHForTokens" : "swapETHForExactTokens";
  } else if (!tokenInIsNative && tokenOutIsNative) {
    // Token -> Native
    functionName = exactInput ? "swapExactTokensForETH" : "swapTokensForExactETH";
  } else {
    // Token -> Token
    functionName = exactInput ? "swapExactTokensForTokens" : "swapTokensForExactTokens";
  }

  console.log(`[hedera/swap-utils] getSwapFunctionName result: ${functionName}`);
  return functionName;
}

/**
 * Prepare swap parameters for Hedera
 * Handles Hedera-specific amount parsing (HBAR uses wei for contracts)
 */
export function prepareSwapParams(
  tokenInAddress: string,
  tokenOutAddress: string,
  tokenInSymbol: string,
  tokenOutSymbol: string,
  amountIn: string,
  amountOutMin: string,
  amountOut: string,
  path: string[],
  recipient: string,
  deadline: number,
  exactInput: boolean = true,
  tokenInDecimals?: number,
  tokenOutDecimals?: number,
): {
  functionName: string;
  params: any[];
  overrides: ethers.Overrides;
} {
  console.log(`[hedera/swap-utils] prepareSwapParams called:`, {
    tokenIn: `${tokenInSymbol}(${tokenInAddress})`,
    tokenOut: `${tokenOutSymbol}(${tokenOutAddress})`,
    amountIn,
    amountOutMin,
    amountOut,
    path,
    recipient,
    deadline,
    exactInput,
    tokenInDecimals,
    tokenOutDecimals,
  });

  const functionName = getSwapFunctionName(
    tokenInAddress,
    tokenOutAddress,
    tokenInSymbol,
    tokenOutSymbol,
    exactInput,
  );

  // Pre-parse all amounts once (avoid repeated parsing)
  // For Hedera native (HBAR): contract expects wei (18 decimals) for EVM compatibility
  const amountInBigInt = parseTokenAmount(
    amountIn,
    tokenInAddress,
    tokenInSymbol,
    tokenInDecimals ?? 18,
  );
  const amountOutMinBigInt = parseTokenAmount(
    amountOutMin,
    tokenOutAddress,
    tokenOutSymbol,
    tokenOutDecimals ?? 18,
  );
  const amountOutBigInt = parseTokenAmount(
    amountOut,
    tokenOutAddress,
    tokenOutSymbol,
    tokenOutDecimals ?? 18,
  );

  // Common parameters for all swaps
  const commonParams = [path, recipient, deadline];

  let params: any[] = [];
  let overrides: ethers.Overrides = {};

  // Use switch for better performance and clarity
  console.log(`[hedera/swap-utils] prepareSwapParams processing function: ${functionName}`);
  switch (functionName) {
    case "swapExactETHForTokens":
      // Native -> Token (exact input): (amountOutMin, path, to, deadline)
      console.log(`[hedera/swap-utils] prepareSwapParams case: swapExactETHForTokens`);
      params = [amountOutMinBigInt, ...commonParams];
      overrides = { value: amountInBigInt };
      break;

    case "swapETHForExactTokens":
      // Native -> Token (exact output): (amountOut, path, to, deadline)
      console.log(`[hedera/swap-utils] prepareSwapParams case: swapETHForExactTokens`);
      params = [amountOutBigInt, ...commonParams];
      overrides = { value: amountInBigInt }; // Max amount in
      break;

    case "swapExactTokensForETH":
    case "swapExactTokensForTokens":
      // Token -> Native/Token (exact input): (amountIn, amountOutMin, path, to, deadline)
      console.log(`[hedera/swap-utils] prepareSwapParams case: ${functionName}`);
      params = [amountInBigInt, amountOutMinBigInt, ...commonParams];
      break;

    case "swapTokensForExactETH":
    case "swapTokensForExactTokens":
      // Token -> Native/Token (exact output): (amountOut, amountInMax, path, to, deadline)
      console.log(`[hedera/swap-utils] prepareSwapParams case: ${functionName}`);
      params = [amountOutBigInt, amountInBigInt, ...commonParams]; // amountIn is max
      break;

    default:
      throw new Error(`Unsupported swap function: ${functionName}`);
  }

  const result = { functionName, params, overrides };
  console.log(`[hedera/swap-utils] prepareSwapParams result:`, {
    functionName: result.functionName,
    paramsLength: result.params.length,
    overrides: result.overrides,
  });
  return result;
}

/**
 * Execute swap transaction for Hedera
 * Uses 7M gas limit cap and no gasPrice
 */
export async function executeSwap(
  contract: ethers.Contract,
  functionName: string,
  params: any[],
  overrides: ethers.Overrides = {},
): Promise<ethers.TransactionResponse> {
  let gasLimit = 7_000_000; // Default for Hedera

  try {
    const estimatedGas = await contract[functionName].estimateGas(...params, overrides);
    // Add 20% buffer
    const gasWithBuffer = estimatedGas + (estimatedGas * BigInt(20)) / BigInt(100);
    gasLimit = Number(gasWithBuffer);

    // Cap gas limit for Hedera (max 7M)
    if (gasLimit > 7_000_000) {
      gasLimit = 7_000_000;
    }

    console.log(`   Estimated Gas: ${estimatedGas.toString()}, Using: ${gasLimit.toString()}`);
  } catch (error: any) {
    console.log(`⚠️  Gas estimation failed, using default: ${gasLimit}`);
    console.log(`   Error: ${error.message}`);
  }

  // Populate transaction
  let populatedTx: ethers.TransactionLike;
  try {
    // Ensure value is explicitly set (0 for token swaps, amount for native swaps)
    // For Hedera: don't include gasPrice in overrides
    const populatedOverrides: ethers.Overrides = {
      ...overrides,
      gasLimit: gasLimit,
      value: overrides.value ?? 0,
    };

    // Remove gasPrice for Hedera - let RPC handle it
    if (populatedOverrides.gasPrice !== undefined) {
      delete populatedOverrides.gasPrice;
    }

    populatedTx = await contract[functionName].populateTransaction(...params, populatedOverrides);

    // Verify transaction data was populated
    if (!populatedTx.data || populatedTx.data === "0x") {
      throw new Error(
        `Transaction data is empty for function ${functionName}. Check parameters: ${JSON.stringify(params)}`,
      );
    }

    const populatedValue = populatedTx.value ?? BigInt(0);

    console.log(`   Populated transaction:`, {
      to: populatedTx.to,
      data: populatedTx.data?.substring(0, 50) + "...",
      dataLength: populatedTx.data?.length,
      value: populatedValue.toString(),
      valueHex: `0x${populatedValue.toString(16)}`,
      gasLimit: populatedTx.gasLimit?.toString(),
    });
    console.log(
      `   Full transaction data (first 100 chars): ${populatedTx.data?.substring(0, 100)}`,
    );
  } catch (error: any) {
    console.error(`   Failed to populate transaction:`, error);
    throw new Error(`Failed to populate transaction for ${functionName}: ${error.message}`);
  }

  // Get signer from contract
  const signer = contract.runner as ethers.Signer;
  if (!signer) {
    throw new Error("No signer available");
  }

  // Prepare transaction request
  // For Hedera: don't specify gasPrice (let RPC handle it)
  const txValue = populatedTx.value ?? BigInt(0);

  const txRequest: ethers.TransactionRequest = {
    to: populatedTx.to,
    data: populatedTx.data,
    value: txValue,
    gasLimit: populatedTx.gasLimit,
  };

  // Explicitly remove gasPrice for Hedera if it was set
  if (txRequest.gasPrice !== undefined) {
    delete txRequest.gasPrice;
  }

  console.log(`   Sending transaction:`, {
    to: txRequest.to,
    value: txValue.toString(),
    valueHex: `0x${txValue.toString(16)}`,
    gasLimit: txRequest.gasLimit?.toString(),
    gasPrice: "undefined (Hedera handles gasPrice)",
    chain: "hedera",
  });

  // Send transaction
  const txResponse = await signer.sendTransaction(txRequest);

  return txResponse;
}
