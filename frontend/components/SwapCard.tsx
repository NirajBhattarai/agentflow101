/**
 * SwapCard Component
 *
 * Displays swap transaction information with status, fees, and estimated output.
 * Uses green/teal styling to match the Swap Agent branding.
 * Executes actual swap when user clicks swap button (hardcoded: HBAR to USDC on Hedera).
 */

import React, { useState } from "react";
import { SwapData, SwapOption } from "./types";
import { useAppKitAccount } from "@reown/appkit/react";
import { useWalletClient } from "wagmi";
import { ethers } from "ethers";
import { ROUTER_ABI } from "@/lib/contracts/router-abi";

interface SwapCardProps {
  data: SwapData;
  onSwapInitiate?: (dex: string) => void;
}

/**
 * Get chain badge color
 */
const getChainColor = (chain: string) => {
  const chainLower = chain.toLowerCase();
  if (chainLower === "hedera") {
    return "bg-gradient-to-r from-purple-500 to-indigo-500";
  }
  if (chainLower === "polygon") {
    return "bg-gradient-to-r from-blue-500 to-purple-500";
  }
  return "bg-gradient-to-r from-gray-500 to-gray-600";
};

/**
 * Get status badge color
 */
const getStatusColor = (status: string) => {
  const statusLower = status.toLowerCase();
  if (statusLower === "completed") {
    return "bg-green-100 text-green-800 border-green-300";
  }
  if (statusLower === "pending") {
    return "bg-yellow-100 text-yellow-800 border-yellow-300";
  }
  if (statusLower === "failed") {
    return "bg-red-100 text-red-800 border-red-300";
  }
  return "bg-gray-100 text-gray-800 border-gray-300";
};

/**
 * Get DEX icon
 */
const getDexIcon = (dex: string) => {
  const dexLower = dex.toLowerCase();
  if (dexLower.includes("saucer")) return "🍽️";
  if (dexLower.includes("heli")) return "🚁";
  if (dexLower.includes("quick")) return "⚡";
  if (dexLower.includes("uniswap")) return "🦄";
  return "💱";
};

export const SwapCard: React.FC<SwapCardProps> = ({ data, onSwapInitiate }) => {
  const { transaction, balance_check, swap_options } = data;
  const [initiating, setInitiating] = useState<string | null>(null);
  const [swappingState, setSwappingState] = useState<"idle" | "swapping" | "done">("idle");
  const [selectedDex, setSelectedDex] = useState<string | null>(null);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [showApprovalDialog, setShowApprovalDialog] = useState(false);
  const [txHash, setTxHash] = useState<string | null>(null);
  const [swapError, setSwapError] = useState<string | null>(null);

  // Wallet connection hooks
  const { address, isConnected } = useAppKitAccount?.() || ({} as any);
  const { data: walletClient } = useWalletClient();

  /**
   * Execute swap (hardcoded: HBAR to USDC on Hedera)
   * Uses ethers.js approach from swaptemp/page.tsx
   */
  const executeSwap = async () => {
    if (!isConnected) {
      setSwapError("Please connect your wallet first");
      return;
    }

    if (!address || !walletClient) {
      setSwapError("Wallet address or client not available");
      return;
    }

    setSwappingState("swapping");
    setSwapError(null);
    setShowApprovalDialog(false);

    try {
      // Hardcoded values: HBAR to USDC on Hedera
      const hbarAmountStr = data.amount_in || "0.01"; // Use amount from swap data
      const RPC_URL = "https://mainnet.hashio.io/api";
      const ROUTER_ADDRESS = "0x00000000000000000000000000000000006715e6"; // Mainnet router EVM address

      // Hardcoded path: WHBAR -> USDC
      const HARDCODED_PATH_EVM = [
        "0x0000000000000000000000000000000000163B5a", // WHBAR
        "0x000000000000000000000000000000000006f89a", // USDC
      ];

      console.log("🔄 Executing Swap (HBAR to USDC on Hedera):", {
        amountIn: hbarAmountStr,
        path: HARDCODED_PATH_EVM,
        recipient: address,
      });

      // Create ethers provider and signer from walletClient
      const provider = new ethers.BrowserProvider(walletClient as any);
      const signer = await provider.getSigner();

      // Check wallet balance first
      const balance = await provider.getBalance(address);
      console.log(`   Wallet Balance: ${ethers.formatEther(balance)} HBAR`);

      // Convert HBAR amount to wei (ethers uses wei, 1 HBAR = 1e18 wei)
      const amountInWei = ethers.parseEther(hbarAmountStr);
      console.log(`   Amount In: ${hbarAmountStr} HBAR = ${amountInWei.toString()} wei`);

      // Calculate deadline (20 minutes from now)
      const deadline = Math.floor(Date.now() / 1000) + 20 * 60;
      const amountOutMin = BigInt(0);

      // Create contract instance
      const contract = new ethers.Contract(ROUTER_ADDRESS, ROUTER_ABI, signer);

      // Get gas price
      const feeData = await provider.getFeeData();
      console.log(`   Gas Price: ${feeData.gasPrice?.toString()} wei`);

      // Estimate gas first
      let gasLimit = 15_000_000;
      try {
        const estimatedGas = await contract.swapExactETHForTokens.estimateGas(
          amountOutMin,
          HARDCODED_PATH_EVM,
          address,
          deadline,
          {
            value: amountInWei,
          },
        );
        // Add 20% buffer and convert to number
        const gasWithBuffer = estimatedGas + (estimatedGas * BigInt(20)) / BigInt(100);
        gasLimit = Number(gasWithBuffer);
        console.log(`   Estimated Gas: ${estimatedGas.toString()}, Using: ${gasLimit.toString()}`);
      } catch (error: any) {
        console.log(`   ⚠️  Gas estimation failed, using default: ${gasLimit}`);
        console.log(`   Error: ${error.message}`);
      }

      // Calculate total cost (value + gas)
      const gasPrice = feeData.gasPrice || BigInt(0);
      const gasCost = gasPrice * BigInt(gasLimit);
      const totalCost = amountInWei + gasCost;
      console.log(`   Gas Cost: ${ethers.formatEther(gasCost)} HBAR`);
      console.log(`   Total Cost: ${ethers.formatEther(totalCost)} HBAR (value + gas)`);

      if (balance < totalCost) {
        throw new Error(
          `Insufficient funds: Need ${ethers.formatEther(totalCost)} HBAR, but have ${ethers.formatEther(balance)} HBAR`,
        );
      }

      // Populate transaction to get encoded data
      const populatedTx = await contract.swapExactETHForTokens.populateTransaction(
        amountOutMin,
        HARDCODED_PATH_EVM,
        address,
        deadline,
        {
          value: amountInWei,
          gasLimit: gasLimit,
        },
      );

      // Send transaction directly using ethers with encoded data
      const txResponse = await signer.sendTransaction({
        to: populatedTx.to,
        data: populatedTx.data,
        value: populatedTx.value,
        gasLimit: populatedTx.gasLimit,
        gasPrice: feeData.gasPrice,
      });

      console.log("✅ Transaction sent!");
      console.log(`   Transaction Hash: ${txResponse.hash}`);
      setTxHash(txResponse.hash);

      // Wait for transaction receipt
      console.log("🔄 Waiting for transaction confirmation...");
      const receipt = await txResponse.wait();

      if (!receipt || receipt.status !== 1) {
        throw new Error(`Transaction failed with status: ${receipt?.status}`);
      }

      console.log("✅ Transaction confirmed!");
      console.log(`   Block Number: ${receipt.blockNumber}`);
      console.log(`   Gas Used: ${receipt.gasUsed.toString()}`);

      setSwappingState("done");
      onSwapInitiate?.(transaction?.dex_name || selectedDex || "SaucerSwap");
    } catch (err: any) {
      console.error("Swap execution error:", err);
      setSwappingState("idle");
      setSwapError(err?.message || "Swap failed. Please try again.");
    }
  };

  return (
    <div className="bg-white/60 backdrop-blur-md rounded-xl p-6 my-3 border-2 border-[#DBDBE5] shadow-elevation-md animate-fade-in-up">
      {/* Header */}
      <div className="mb-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-2xl">💱</span>
          <h2 className="text-2xl font-semibold text-[#010507]">
            {transaction ? "Swap Transaction" : "Swap Options"}
          </h2>
        </div>
        <div className="flex items-center gap-3">
          <span
            className={`px-3 py-1 rounded-full text-xs font-bold text-white ${getChainColor(data.chain)}`}
          >
            {data.chain.toUpperCase()}
          </span>
          {transaction && (
            <span
              className={`px-3 py-1 rounded-full text-xs font-bold border-2 ${getStatusColor(transaction.status)}`}
            >
              {transaction.status.toUpperCase()}
            </span>
          )}
        </div>
      </div>

      {/* Error Message */}
      {data.error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
          <p className="text-sm text-red-800">{data.error}</p>
        </div>
      )}

      {/* Balance Check */}
      {balance_check && (
        <div
          className={`rounded-xl p-4 mb-4 border ${
            balance_check.balance_sufficient
              ? "bg-green-50 border-green-200"
              : "bg-red-50 border-red-200"
          }`}
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs text-[#57575B] mb-1">Balance Check</div>
              <div className="text-sm font-semibold text-[#010507]">
                {balance_check.balance_sufficient ? (
                  <span className="text-green-700">✓ Sufficient Balance</span>
                ) : (
                  <span className="text-red-700">✗ Insufficient Balance</span>
                )}
              </div>
              <div className="text-xs text-[#57575B] mt-1">
                Available: {balance_check.balance} {balance_check.token_symbol} | Required:{" "}
                {balance_check.required_amount} {balance_check.token_symbol}
              </div>
            </div>
            {!balance_check.balance_sufficient && <div className="text-red-600 font-bold">⚠️</div>}
          </div>
        </div>
      )}

      {/* Swap Amount Summary */}
      <div className="bg-gradient-to-r from-green-50 to-teal-50 rounded-xl p-4 mb-4 border border-green-200">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-xs text-[#57575B] mb-1">Amount In</div>
            <div className="text-2xl font-bold text-[#010507]">
              {data.amount_in} {data.token_in_symbol}
            </div>
          </div>
          <div>
            <div className="text-xs text-[#57575B] mb-1">Amount Out</div>
            <div className="text-2xl font-bold text-green-600">
              {transaction?.amount_out || swap_options?.[0]?.amount_out || "—"}{" "}
              {data.token_out_symbol}
            </div>
          </div>
          {data.account_address && (
            <div className="col-span-2 mt-2">
              <div className="text-xs text-[#57575B] mb-1">Account</div>
              <div className="text-sm font-mono text-[#010507] break-all">
                {data.account_address.slice(0, 10)}...{data.account_address.slice(-8)}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* High Amount Warning */}
      {data.amount_exceeds_threshold && data.requires_confirmation && !transaction && (
        <div className="mb-4 bg-yellow-50 border-2 border-yellow-300 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <div className="text-2xl">⚠️</div>
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-yellow-900 mb-1">Confirmation Required</h4>
              <p className="text-xs text-yellow-800">
                The swap amount ({data.amount_in} {data.token_in_symbol}) exceeds the threshold of{" "}
                {data.confirmation_threshold} {data.token_in_symbol}. Please review the options
                below and confirm before proceeding.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Swap Options Display Box (if not yet initiated) */}
      {swap_options && swap_options.length > 0 && !transaction && !showConfirmation && (
        <div className="mb-4">
          <div className="bg-white/90 backdrop-blur-md rounded-xl p-5 border-2 border-[#DBDBE5] shadow-elevation-md">
            <h3 className="text-lg font-semibold text-[#010507] mb-2">Available DEX Options</h3>
            <p className="text-sm text-[#57575B] mb-4">
              {data.requires_confirmation && data.amount_exceeds_threshold
                ? "Please select a DEX and confirm to proceed with the swap."
                : "Please select a DEX to proceed with the swap. You can say 'Swap with [DEX Name]' or click on a DEX below."}
            </p>
            <div className="space-y-3">
              {swap_options.map((option: SwapOption, index: number) => (
                <div
                  key={index}
                  onClick={() => {
                    if (balance_check?.balance_sufficient && !initiating) {
                      setSelectedDex(option.dex_name);
                    }
                  }}
                  className={`rounded-lg p-4 border-2 transition-all cursor-pointer ${
                    selectedDex === option.dex_name
                      ? "border-green-500 bg-green-50 ring-2 ring-green-200"
                      : option.is_recommended
                        ? "border-green-300 bg-green-50/50 hover:border-green-400 hover:bg-green-50"
                        : "border-[#E9E9EF] bg-white/80 hover:border-green-200 hover:bg-green-50/30"
                  } ${!balance_check?.balance_sufficient ? "opacity-50 cursor-not-allowed" : ""}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-lg">{getDexIcon(option.dex_name)}</span>
                        <span className="text-base font-bold text-[#010507]">
                          {option.dex_name}
                        </span>
                        {option.is_recommended && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-green-500 text-white">
                            RECOMMENDED
                          </span>
                        )}
                      </div>
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <span className="text-[#57575B]">Output: </span>
                          <span className="font-bold text-green-600">
                            {option.amount_out} {data.token_out_symbol}
                          </span>
                        </div>
                        <div>
                          <span className="text-[#57575B]">Fee: </span>
                          <span className="font-bold text-[#010507]">{option.swap_fee}</span>
                        </div>
                        {option.price_impact && (
                          <div className="col-span-2">
                            <span className="text-[#57575B]">Price Impact: </span>
                            <span className="font-semibold text-[#010507]">
                              {option.price_impact}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                    {selectedDex === option.dex_name && (
                      <div className="ml-3 flex-shrink-0">
                        <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center">
                          <span className="text-white text-xs font-bold">✓</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Selected Option Action Button */}
            {selectedDex && (
              <div className="mt-4 pt-4 border-t border-[#E9E9EF]">
                {(() => {
                  const option = swap_options.find((opt) => opt.dex_name === selectedDex);
                  if (!option) return null;
                  return (
                    <button
                      onClick={() => {
                        if (!balance_check?.balance_sufficient) return;
                        if (!isConnected) {
                          setSwapError("Please connect your wallet first");
                          return;
                        }
                        setShowApprovalDialog(true);
                      }}
                      disabled={!balance_check?.balance_sufficient || !isConnected}
                      className={`w-full px-4 py-3 rounded-lg font-semibold text-sm transition-all shadow-sm ${
                        balance_check?.balance_sufficient && isConnected
                          ? "bg-green-500 hover:bg-green-600 text-white shadow-md hover:shadow-lg"
                          : "bg-gray-300 text-gray-500 cursor-not-allowed"
                      }`}
                    >
                      {!isConnected ? "Connect Wallet" : `Swap with ${option.dex_name}`}
                    </button>
                  );
                })()}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Transaction Information (after swap is initiated) */}
      {transaction && (
        <div className="space-y-3">
          <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 shadow-elevation-sm border border-[#E9E9EF]">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-xs text-[#57575B] mb-1">DEX</div>
                <div className="text-sm font-semibold text-[#010507] flex items-center gap-2">
                  <span>{getDexIcon(transaction.dex_name)}</span>
                  {transaction.dex_name}
                </div>
              </div>
              <div>
                <div className="text-xs text-[#57575B] mb-1">Estimated Time</div>
                <div className="text-sm font-semibold text-[#010507]">
                  {transaction.estimated_time}
                </div>
              </div>
            </div>
            <div className="mt-3 pt-3 border-t border-[#E9E9EF]">
              <div className="text-xs text-[#57575B] mb-1">Swap Fee</div>
              <div className="text-lg font-bold text-[#010507]">{transaction.swap_fee}</div>
            </div>
            {transaction.price_impact && (
              <div className="mt-3 pt-3 border-t border-[#E9E9EF]">
                <div className="text-xs text-[#57575B] mb-1">Price Impact</div>
                <div className="text-sm font-semibold text-[#010507]">
                  {transaction.price_impact}
                </div>
              </div>
            )}
          </div>

          {transaction.transaction_hash && (
            <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 shadow-elevation-sm border border-[#E9E9EF]">
              <div className="text-xs text-[#57575B] mb-1">Transaction Hash</div>
              <div className="text-sm font-mono text-[#010507] break-all">
                {transaction.transaction_hash}
              </div>
            </div>
          )}

          <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 shadow-elevation-sm border border-[#E9E9EF]">
            <div className="text-xs text-[#57575B] mb-1">Token In Address</div>
            <div className="text-sm font-mono text-[#010507] break-all">
              {transaction.token_in_address}
            </div>
          </div>

          <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 shadow-elevation-sm border border-[#E9E9EF]">
            <div className="text-xs text-[#57575B] mb-1">Token Out Address</div>
            <div className="text-sm font-mono text-[#010507] break-all">
              {transaction.token_out_address}
            </div>
          </div>
        </div>
      )}

      {/* Status Message */}
      {transaction && transaction.status === "pending" && (
        <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
          <p className="text-sm text-yellow-800">
            ⏳ Swap transaction is pending. It will be completed in approximately{" "}
            {transaction.estimated_time}.
          </p>
        </div>
      )}

      {/* Approval Dialog */}
      {showApprovalDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4 shadow-2xl border-2 border-green-200">
            <h3 className="text-xl font-bold text-[#010507] mb-4">Confirm Swap</h3>
            <div className="space-y-3 mb-6">
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="text-sm text-[#57575B] mb-1">You are swapping</div>
                <div className="text-lg font-bold text-[#010507]">
                  {data.amount_in} {data.token_in_symbol} → {data.token_out_symbol}
                </div>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="text-sm text-[#57575B] mb-1">You will receive (estimated)</div>
                <div className="text-lg font-bold text-green-600">
                  {swap_options?.[0]?.amount_out || transaction?.amount_out || "—"}{" "}
                  {data.token_out_symbol}
                </div>
              </div>
              {transaction?.swap_fee && (
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-sm text-[#57575B] mb-1">Swap Fee</div>
                  <div className="text-lg font-bold text-[#010507]">{transaction.swap_fee}</div>
                </div>
              )}
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowApprovalDialog(false);
                  setSwapError(null);
                }}
                className="flex-1 px-4 py-3 rounded-lg font-semibold text-sm bg-gray-200 text-gray-700 hover:bg-gray-300 transition-all"
              >
                Cancel
              </button>
              <button
                onClick={executeSwap}
                disabled={swappingState === "swapping"}
                className={`flex-1 px-4 py-3 rounded-lg font-semibold text-sm transition-all ${
                  swappingState === "swapping"
                    ? "bg-yellow-500 text-white cursor-not-allowed"
                    : "bg-green-600 hover:bg-green-700 text-white shadow-md hover:shadow-lg"
                }`}
              >
                {swappingState === "swapping" ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="animate-spin">⏳</span>
                    Processing...
                  </span>
                ) : (
                  "Confirm Swap"
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Swap Error */}
      {swapError && (
        <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3">
          <p className="text-sm text-red-800">{swapError}</p>
          <button
            onClick={() => setSwapError(null)}
            className="mt-2 text-xs text-red-600 hover:text-red-800 underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Swap Button for Transaction (when transaction exists) */}
      {transaction && transaction.status === "pending" && (
        <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <button
            onClick={() => {
              if (!isConnected) {
                setSwapError("Please connect your wallet first");
                return;
              }
              setShowApprovalDialog(true);
            }}
            disabled={swappingState === "swapping" || !isConnected}
            className={`w-full px-4 py-3 rounded-lg font-semibold text-sm transition-all shadow-sm ${
              swappingState === "swapping"
                ? "bg-yellow-500 text-white cursor-not-allowed"
                : !isConnected
                  ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                  : "bg-green-600 hover:bg-green-700 text-white shadow-md hover:shadow-lg"
            }`}
          >
            {swappingState === "swapping" ? (
              <span className="flex items-center justify-center gap-2">
                <span className="animate-spin">⏳</span>
                Swapping...
              </span>
            ) : !isConnected ? (
              "Connect Wallet to Swap"
            ) : (
              `Execute Swap with ${transaction.dex_name}`
            )}
          </button>
          {txHash && (
            <div className="mt-3 pt-3 border-t border-yellow-200">
              <div className="text-xs text-yellow-800 mb-1">Transaction Hash</div>
              <div className="text-sm font-mono text-yellow-900 break-all">{txHash}</div>
            </div>
          )}
        </div>
      )}

      {transaction && transaction.status === "completed" && (
        <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div>
              <p className="text-sm font-semibold text-green-800 mb-1">
                ✅ Swap transaction completed successfully!
              </p>
              <p className="text-xs text-green-700">
                You received {transaction.amount_out} {transaction.token_out_symbol} for{" "}
                {transaction.amount_in} {transaction.token_in_symbol}.
              </p>
            </div>
          </div>
          {txHash && (
            <div className="mt-3 pt-3 border-t border-green-200">
              <div className="text-xs text-green-800 mb-1">Transaction Hash</div>
              <div className="text-sm font-mono text-green-900 break-all">{txHash}</div>
            </div>
          )}
        </div>
      )}

      {transaction && transaction.status === "failed" && (
        <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3">
          <p className="text-sm text-red-800">
            ❌ Swap transaction failed. Please try again or contact support.
          </p>
        </div>
      )}
    </div>
  );
};
