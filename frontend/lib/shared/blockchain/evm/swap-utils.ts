/**
 * EVM-specific swap execution utilities
 *
 * Handles swap transaction execution for EVM-compatible chains
 */

import { ethers } from "ethers";
import * as evmOps from "./evm-operations";

/**
 * Get chain type - always returns "evm" for this module
 */
export function getChainType(): "evm" {
  return "evm";
}

/**
 * Parse token amount for EVM swaps
 */
export function parseTokenAmount(
  amount: string,
  tokenAddress: string,
  tokenSymbol: string,
  decimals: number = 18,
): bigint {
  return evmOps.parseEvmAmount(amount, decimals);
}

/**
 * Format token amount for EVM swaps
 */
export function formatTokenAmount(amount: bigint, decimals: number = 18): string {
  return evmOps.formatEvmAmount(amount, decimals);
}

/**
 * Get balance for EVM swaps
 */
export async function getBalance(
  provider: ethers.Provider,
  accountAddress: string,
  tokenAddress: string | undefined,
): Promise<{ balance: string; balanceRaw: string; decimals: number }> {
  if (!provider) {
    throw new Error("Provider required for EVM chains");
  }
  return await evmOps.getEvmBalance(provider, accountAddress, tokenAddress);
}

/**
 * Check if token is native for EVM
 */
export function isNativeToken(tokenAddress: string): boolean {
  return evmOps.isEvmNative(tokenAddress);
}

/**
 * Check if token symbol is native for EVM chains
 */
export function isNativeSymbol(tokenSymbol: string, chain: string): boolean {
  const nativeSymbols: Record<string, string[]> = {
    polygon: ["MATIC", "POL"], // POL is the new native token name on Polygon
    ethereum: ["ETH"],
    arbitrum: ["ETH"],
    optimism: ["ETH"],
    base: ["ETH"],
  };
  const symbols = nativeSymbols[chain.toLowerCase()] || ["ETH"];
  return symbols.some((sym) => sym.toUpperCase() === tokenSymbol.toUpperCase());
}

/**
 * Check if token is native by address or symbol
 */
export function isNative(tokenAddress: string, tokenSymbol: string, chain: string): boolean {
  return isNativeToken(tokenAddress) || isNativeSymbol(tokenSymbol, chain);
}

/**
 * Check if router is Uniswap V3
 */
function isUniswapV3Router(routerAddress: string): boolean {
  // Uniswap V3 SwapRouter address
  return routerAddress.toLowerCase() === "0xE592427A0AEce92De3Edee1F18E0157C05861564".toLowerCase();
}

/**
 * Get WMATIC address for Polygon
 */
function getWrappedNativeAddress(chain: string): string | null {
  const wrappedAddresses: Record<string, string> = {
    polygon: "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270", // WMATIC on Polygon
    ethereum: "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", // WETH
  };
  return wrappedAddresses[chain.toLowerCase()] || null;
}

/**
 * Determine swap function name based on token types for EVM
 */
export function getSwapFunctionName(
  tokenInAddress: string,
  tokenOutAddress: string,
  tokenInSymbol: string,
  tokenOutSymbol: string,
  chain: string,
  exactInput: boolean = true,
  routerAddress?: string,
): string {
  console.log(
    `[evm/swap-utils] getSwapFunctionName called: tokenIn=${tokenInSymbol}(${tokenInAddress}), tokenOut=${tokenOutSymbol}(${tokenOutAddress}), chain=${chain}, exactInput=${exactInput}, router=${routerAddress}`,
  );

  const isV3 = routerAddress ? isUniswapV3Router(routerAddress) : false;

  // For Uniswap V3, always use exactInputSingle
  if (isV3) {
    console.log(`[evm/swap-utils] Using Uniswap V3 exactInputSingle`);
    return "exactInputSingle";
  }

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

  console.log(`[evm/swap-utils] getSwapFunctionName result: ${functionName}`);
  return functionName;
}

/**
 * Prepare swap parameters for EVM chains
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
  routerAddress?: string,
): {
  functionName: string;
  params: any[];
  overrides: ethers.Overrides;
} {
  console.log(`[evm/swap-utils] prepareSwapParams called:`, {
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
    routerAddress,
  });

  const isV3 = routerAddress ? isUniswapV3Router(routerAddress) : false;
  const functionName = getSwapFunctionName(
    tokenInAddress,
    tokenOutAddress,
    tokenInSymbol,
    tokenOutSymbol,
    chain,
    exactInput,
    routerAddress,
  );

  // Pre-parse all amounts once (avoid repeated parsing)
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

  let params: any[] = [];
  let overrides: ethers.Overrides = {};

  // Use switch for better performance and clarity
  console.log(`[evm/swap-utils] prepareSwapParams processing function: ${functionName}`);

  // Handle Uniswap V3 exactInputSingle
  if (functionName === "exactInputSingle") {
    console.log(`[evm/swap-utils] prepareSwapParams case: exactInputSingle (Uniswap V3)`);

    // For V3, we need to use wrapped native token if input is native
    const tokenInIsNative = isNative(tokenInAddress, tokenInSymbol, chain);
    const tokenOutIsNative = isNative(tokenOutAddress, tokenOutSymbol, chain);

    // Uniswap V3 uses wrapped token addresses (WETH/WMATIC) for native tokens
    // The router automatically wraps/unwraps when you send native value
    const wrappedNative = getWrappedNativeAddress(chain);

    // For native tokens, use wrapped address; for others, use the actual address
    let actualTokenIn = tokenInAddress;
    let actualTokenOut = tokenOutAddress;

    if (
      tokenInIsNative ||
      tokenInAddress.toLowerCase() === "0x0000000000000000000000000000000000001010"
    ) {
      // Use wrapped native address (WMATIC for Polygon)
      if (wrappedNative) {
        actualTokenIn = wrappedNative;
      } else {
        throw new Error(`No wrapped native token address found for chain: ${chain}`);
      }
    }

    if (
      tokenOutIsNative ||
      tokenOutAddress.toLowerCase() === "0x0000000000000000000000000000000000001010"
    ) {
      // Use wrapped native address (WMATIC for Polygon)
      if (wrappedNative) {
        actualTokenOut = wrappedNative;
      } else {
        throw new Error(`No wrapped native token address found for chain: ${chain}`);
      }
    }

    // Default fee tier: 0.3% (3000) - most common for major pairs
    const fee = 3000;

    // exactInputSingle params: (ExactInputSingleParams)
    // struct ExactInputSingleParams {
    //   address tokenIn;
    //   address tokenOut;
    //   uint24 fee;
    //   address recipient;
    //   uint256 deadline;
    //   uint256 amountIn;
    //   uint256 amountOutMinimum;
    //   uint160 sqrtPriceLimitX96;
    // }
    params = [
      {
        tokenIn: actualTokenIn,
        tokenOut: actualTokenOut,
        fee: fee,
        recipient: recipient,
        deadline: deadline,
        amountIn: amountInBigInt,
        amountOutMinimum: amountOutMinBigInt,
        sqrtPriceLimitX96: 0, // 0 means no price limit
      },
    ];

    // For native token input, send ETH/MATIC value
    if (
      tokenInIsNative ||
      tokenInAddress.toLowerCase() === "0x0000000000000000000000000000000000001010"
    ) {
      overrides = { value: amountInBigInt };
    }
  } else {
    // V2 router functions
    const commonParams = [path, recipient, deadline];

    switch (functionName) {
      case "swapExactETHForTokens":
        // Native -> Token (exact input): (amountOutMin, path, to, deadline)
        console.log(`[evm/swap-utils] prepareSwapParams case: swapExactETHForTokens`);
        params = [amountOutMinBigInt, ...commonParams];
        overrides = { value: amountInBigInt };
        break;

      case "swapETHForExactTokens":
        // Native -> Token (exact output): (amountOut, path, to, deadline)
        console.log(`[evm/swap-utils] prepareSwapParams case: swapETHForExactTokens`);
        params = [amountOutBigInt, ...commonParams];
        overrides = { value: amountInBigInt }; // Max amount in
        break;

      case "swapExactTokensForETH":
      case "swapExactTokensForTokens":
        // Token -> Native/Token (exact input): (amountIn, amountOutMin, path, to, deadline)
        console.log(`[evm/swap-utils] prepareSwapParams case: ${functionName}`);
        params = [amountInBigInt, amountOutMinBigInt, ...commonParams];
        break;

      case "swapTokensForExactETH":
      case "swapTokensForExactTokens":
        // Token -> Native/Token (exact output): (amountOut, amountInMax, path, to, deadline)
        console.log(`[evm/swap-utils] prepareSwapParams case: ${functionName}`);
        params = [amountOutBigInt, amountInBigInt, ...commonParams]; // amountIn is max
        break;

      default:
        throw new Error(`Unsupported swap function: ${functionName}`);
    }
  }

  const result = { functionName, params, overrides };
  console.log(`[evm/swap-utils] prepareSwapParams result:`, {
    functionName: result.functionName,
    paramsLength: result.params.length,
    overrides: result.overrides,
  });
  return result;
}

/**
 * Execute swap transaction for EVM chains
 * Estimates gas and uses gasPrice
 */
export async function executeSwap(
  contract: ethers.Contract,
  functionName: string,
  params: any[],
  overrides: ethers.Overrides = {},
): Promise<ethers.TransactionResponse> {
  let gasLimit = 15_000_000; // Default for EVM chains

  try {
    const estimatedGas = await contract[functionName].estimateGas(...params, overrides);
    // Add 20% buffer
    const gasWithBuffer = estimatedGas + (estimatedGas * BigInt(20)) / BigInt(100);
    gasLimit = Number(gasWithBuffer);

    console.log(`   Estimated Gas: ${estimatedGas.toString()}, Using: ${gasLimit.toString()}`);
  } catch (error: any) {
    console.log(`⚠️  Gas estimation failed, using default: ${gasLimit}`);
    console.log(`   Error: ${error.message}`);
  }

  // Populate transaction
  let populatedTx: ethers.TransactionLike;
  try {
    // Ensure value is explicitly set (0 for token swaps, amount for native swaps)
    const populatedOverrides: ethers.Overrides = {
      ...overrides,
      gasLimit: gasLimit,
      value: overrides.value ?? 0,
    };

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
  // For EVM chains: use gasPrice from populatedTx or overrides
  const txValue = populatedTx.value ?? BigInt(0);

  const txRequest: ethers.TransactionRequest = {
    to: populatedTx.to,
    data: populatedTx.data,
    value: txValue,
    gasLimit: populatedTx.gasLimit,
  };

  // Add gasPrice for EVM chains
  if (populatedTx.gasPrice || overrides.gasPrice) {
    txRequest.gasPrice = populatedTx.gasPrice || overrides.gasPrice;
  }

  console.log(`   Sending transaction:`, {
    to: txRequest.to,
    value: txValue.toString(),
    valueHex: `0x${txValue.toString(16)}`,
    gasLimit: txRequest.gasLimit?.toString(),
    gasPrice: txRequest.gasPrice?.toString(),
    chain: "evm",
  });

  // Send transaction
  const txResponse = await signer.sendTransaction(txRequest);

  return txResponse;
}
