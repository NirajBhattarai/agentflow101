/**
 * Swap utility functions for determining swap type and executing swaps
 *
 * This file handles swap logic that works across chains.
 * Chain-specific operations are delegated to:
 * - hedera-operations.ts for Hedera-specific logic
 * - evm-operations.ts for EVM-compatible chains
 */

import { ethers } from "ethers";
import * as hederaOps from "./hedera";
import * as evmOps from "./evm";
import { executeSwap as executeSwapHedera } from "./hedera/swap-utils";
import { executeSwap as executeSwapEvm } from "./evm/swap-utils";

// Re-export chain-specific operations for convenience
export { hederaOps, evmOps };

// Chain type mapping
const CHAIN_TYPES: Record<string, "hedera" | "evm"> = {
  hedera: "hedera",
  polygon: "evm",
  ethereum: "evm",
  arbitrum: "evm",
  optimism: "evm",
  base: "evm",
};

// Native token symbols
const NATIVE_SYMBOLS: Record<string, string[]> = {
  hedera: ["HBAR"],
  polygon: ["MATIC"],
  ethereum: ["ETH"],
};

/**
 * Get chain type (hedera or evm)
 */
export function getChainType(chain: string): "hedera" | "evm" {
  const result = CHAIN_TYPES[chain.toLowerCase()] || "evm";
  console.log(`[swap-utils] getChainType called: chain=${chain}, result=${result}`);
  return result;
}

/**
 * Check if a token address is native (ETH/HBAR/MATIC)
 */
export function isNativeToken(tokenAddress: string, chain: string): boolean {
  console.log(`[swap-utils] isNativeToken called: tokenAddress=${tokenAddress}, chain=${chain}`);
  const chainType = getChainType(chain);

  if (chainType === "hedera") {
    const result = hederaOps.isHederaNative(tokenAddress);
    console.log(`[swap-utils] isNativeToken result (hedera): ${result}`);
    return result;
  } else {
    const result = evmOps.isEvmNative(tokenAddress);
    console.log(`[swap-utils] isNativeToken result (evm): ${result}`);
    return result;
  }
}

/**
 * Check if a token symbol is native
 */
export function isNativeSymbol(tokenSymbol: string, chain: string): boolean {
  const nativeSymbols = NATIVE_SYMBOLS[chain.toLowerCase()] || [];
  return nativeSymbols.some((sym) => sym.toUpperCase() === tokenSymbol.toUpperCase());
}

/**
 * Check if token is native by address or symbol
 */
export function isNative(tokenAddress: string, tokenSymbol: string, chain: string): boolean {
  console.log(
    `[swap-utils] isNative called: tokenAddress=${tokenAddress}, tokenSymbol=${tokenSymbol}, chain=${chain}`,
  );
  const result = isNativeToken(tokenAddress, chain) || isNativeSymbol(tokenSymbol, chain);
  console.log(`[swap-utils] isNative result: ${result}`);
  return result;
}

/**
 * Determine swap function name based on token types
 */
export function getSwapFunctionName(
  tokenInAddress: string,
  tokenOutAddress: string,
  tokenInSymbol: string,
  tokenOutSymbol: string,
  chain: string,
  exactInput: boolean = true,
): string {
  console.log(
    `[swap-utils] getSwapFunctionName called: tokenIn=${tokenInSymbol}(${tokenInAddress}), tokenOut=${tokenOutSymbol}(${tokenOutAddress}), chain=${chain}, exactInput=${exactInput}`,
  );
  const tokenInIsNative = isNative(tokenInAddress, tokenInSymbol, chain);
  const tokenOutIsNative = isNative(tokenOutAddress, tokenOutSymbol, chain);

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

  console.log(`[swap-utils] getSwapFunctionName result: ${functionName}`);
  return functionName;
}

/**
 * Convert token amount to wei/tinybar based on chain
 */
export function parseTokenAmount(amount: string, chain: string, decimals: number = 18): bigint {
  console.log(
    `[swap-utils] parseTokenAmount called: amount=${amount}, chain=${chain}, decimals=${decimals}`,
  );
  const chainType = getChainType(chain);

  if (chainType === "hedera") {
    const result = hederaOps.parseHederaAmount(amount, decimals);
    console.log(`[swap-utils] parseTokenAmount result (hedera): ${result.toString()}`);
    return result;
  } else {
    const result = evmOps.parseEvmAmount(amount, decimals);
    console.log(`[swap-utils] parseTokenAmount result (evm): ${result.toString()}`);
    return result;
  }
}

/**
 * Format token amount from wei/tinybar based on chain
 */
export function formatTokenAmount(amount: bigint, chain: string, decimals: number = 18): string {
  const chainType = getChainType(chain);

  if (chainType === "hedera") {
    return hederaOps.formatHederaAmount(amount, decimals);
  } else {
    return evmOps.formatEvmAmount(amount, decimals);
  }
}

/**
 * Get balance for an account (chain-agnostic wrapper)
 */
export async function getBalance(
  accountAddress: string,
  tokenAddress: string | undefined,
  chain: string,
  provider?: ethers.Provider,
  network: string = "mainnet",
): Promise<{ balance: string; balanceRaw: string; decimals: number }> {
  console.log(
    `[swap-utils] getBalance called: accountAddress=${accountAddress}, tokenAddress=${tokenAddress}, chain=${chain}, network=${network}`,
  );
  const chainType = getChainType(chain);

  if (chainType === "hedera") {
    const result = await hederaOps.getHederaBalance(accountAddress, tokenAddress, network);
    console.log(`[swap-utils] getBalance result (hedera):`, result);
    return result;
  } else {
    if (!provider) {
      throw new Error("Provider required for EVM chains");
    }
    const result = await evmOps.getEvmBalance(provider, accountAddress, tokenAddress);
    console.log(`[swap-utils] getBalance result (evm):`, result);
    return result;
  }
}

/**
 * Execute swap transaction (chain-agnostic wrapper)
 * Delegates to chain-specific implementations
 */
export async function executeSwap(
  contract: ethers.Contract,
  functionName: string,
  params: any[],
  overrides: ethers.Overrides = {},
  chain?: string,
): Promise<ethers.TransactionResponse> {
  console.log(
    `[swap-utils] executeSwap called: functionName=${functionName}, chain=${chain || "evm"}, params=`,
    params,
    `overrides=`,
    overrides,
  );
  const chainType = getChainType(chain || "evm");

  if (chainType === "hedera") {
    console.log(`[swap-utils] executeSwap delegating to Hedera implementation`);
    const result = await executeSwapHedera(contract, functionName, params, overrides);
    console.log(`[swap-utils] executeSwap result (hedera):`, result);
    return result;
  } else {
    console.log(`[swap-utils] executeSwap delegating to EVM implementation`);
    const result = await executeSwapEvm(contract, functionName, params, overrides);
    console.log(`[swap-utils] executeSwap result (evm):`, result);
    return result;
  }
}

/**
 * Swap parameter configuration map
 * Maps function names to their parameter builders for optimal performance
 */
type ParamBuilder = (
  amounts: { in: bigint; outMin: bigint; out: bigint },
  common: [string[], string, number],
) => { params: any[]; overrides: ethers.Overrides };

const SWAP_PARAM_BUILDERS: Record<string, ParamBuilder> = {
  swapExactETHForTokens: ({ outMin }, [path, recipient, deadline]) => ({
    params: [outMin, path, recipient, deadline],
    overrides: {},
  }),
  swapETHForExactTokens: ({ out }, [path, recipient, deadline]) => ({
    params: [out, path, recipient, deadline],
    overrides: {},
  }),
  swapExactTokensForETH: ({ in: amountIn, outMin }, [path, recipient, deadline]) => ({
    params: [amountIn, outMin, path, recipient, deadline],
    overrides: {},
  }),
  swapExactTokensForTokens: ({ in: amountIn, outMin }, [path, recipient, deadline]) => ({
    params: [amountIn, outMin, path, recipient, deadline],
    overrides: {},
  }),
  swapTokensForExactETH: ({ out, in: amountInMax }, [path, recipient, deadline]) => ({
    params: [out, amountInMax, path, recipient, deadline],
    overrides: {},
  }),
  swapTokensForExactTokens: ({ out, in: amountInMax }, [path, recipient, deadline]) => ({
    params: [out, amountInMax, path, recipient, deadline],
    overrides: {},
  }),
};

/**
 * Prepare swap parameters based on swap type
 * Optimized version that pre-parses amounts and uses efficient switch statement
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
  chain: string,
  exactInput: boolean = true,
  tokenInDecimals?: number,
  tokenOutDecimals?: number,
): {
  functionName: string;
  params: any[];
  overrides: ethers.Overrides;
} {
  console.log(`[swap-utils] prepareSwapParams called:`, {
    tokenIn: `${tokenInSymbol}(${tokenInAddress})`,
    tokenOut: `${tokenOutSymbol}(${tokenOutAddress})`,
    amountIn,
    amountOutMin,
    amountOut,
    path,
    recipient,
    deadline,
    chain,
    exactInput,
    tokenInDecimals,
    tokenOutDecimals,
  });

  const functionName = getSwapFunctionName(
    tokenInAddress,
    tokenOutAddress,
    tokenInSymbol,
    tokenOutSymbol,
    chain,
    exactInput,
  );

  // Pre-parse all amounts once (avoid repeated parsing)
  // For Hedera native tokens: use wei (18 decimals) for EVM compatibility, not tinybars (8 decimals)
  // For other tokens/chains: use parseTokenAmount with appropriate decimals
  let amountInBigInt: bigint;
  let amountOutMinBigInt: bigint;
  let amountOutBigInt: bigint;

  if (chain === "hedera" && isNative(tokenInAddress, tokenInSymbol, chain)) {
    // Hedera native (HBAR): contract expects wei (18 decimals) for EVM compatibility
    amountInBigInt = ethers.parseEther(amountIn);
  } else {
    // Use provided decimals or default to 18
    const decimals = tokenInDecimals ?? 18;
    amountInBigInt = parseTokenAmount(amountIn, chain, decimals);
  }

  if (chain === "hedera" && isNative(tokenOutAddress, tokenOutSymbol, chain)) {
    // Hedera native (HBAR): contract expects wei (18 decimals) for EVM compatibility
    amountOutMinBigInt = ethers.parseEther(amountOutMin);
    amountOutBigInt = ethers.parseEther(amountOut);
  } else {
    // Use provided decimals or default to 18
    const decimals = tokenOutDecimals ?? 18;
    amountOutMinBigInt = parseTokenAmount(amountOutMin, chain, decimals);
    amountOutBigInt = parseTokenAmount(amountOut, chain, decimals);
  }

  // Common parameters for all swaps
  const commonParams = [path, recipient, deadline];

  let params: any[] = [];
  let overrides: ethers.Overrides = {};

  // Use switch for better performance and clarity
  console.log(`[swap-utils] prepareSwapParams processing function: ${functionName}`);
  switch (functionName) {
    case "swapExactETHForTokens":
      // Native -> Token (exact input): (amountOutMin, path, to, deadline)
      console.log(`[swap-utils] prepareSwapParams case: swapExactETHForTokens`);
      params = [amountOutMinBigInt, ...commonParams];
      overrides = { value: amountInBigInt };
      break;

    case "swapETHForExactTokens":
      // Native -> Token (exact output): (amountOut, path, to, deadline)
      console.log(`[swap-utils] prepareSwapParams case: swapETHForExactTokens`);
      params = [amountOutBigInt, ...commonParams];
      overrides = { value: amountInBigInt }; // Max amount in
      break;

    case "swapExactTokensForETH":
    case "swapExactTokensForTokens":
      // Token -> Native/Token (exact input): (amountIn, amountOutMin, path, to, deadline)
      console.log(`[swap-utils] prepareSwapParams case: ${functionName}`);
      params = [amountInBigInt, amountOutMinBigInt, ...commonParams];
      break;

    case "swapTokensForExactETH":
    case "swapTokensForExactTokens":
      // Token -> Native/Token (exact output): (amountOut, amountInMax, path, to, deadline)
      console.log(`[swap-utils] prepareSwapParams case: ${functionName}`);
      params = [amountOutBigInt, amountInBigInt, ...commonParams]; // amountIn is max
      break;

    default:
      throw new Error(`Unsupported swap function: ${functionName}`);
  }

  const result = { functionName, params, overrides };
  console.log(`[swap-utils] prepareSwapParams result:`, {
    functionName: result.functionName,
    paramsLength: result.params.length,
    overrides: result.overrides,
  });
  return result;
}
