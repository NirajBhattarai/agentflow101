/**
 * EVM-specific swap execution utilities
 *
 * Handles swap transaction execution for EVM-compatible chains
 */

import { ethers } from "ethers";

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
  debugger;
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
