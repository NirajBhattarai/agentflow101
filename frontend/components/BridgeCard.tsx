/**
 * BridgeCard Component
 *
 * Displays bridge transaction information with status, fees, and estimated time.
 * Uses orange/amber styling to match the Bridge Agent branding.
 */

import React, { useState } from "react";
import { BridgeData, BridgeOption } from "./types";

interface BridgeCardProps {
  data: BridgeData;
  onBridgeInitiate?: (protocol: string) => void;
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

export const BridgeCard: React.FC<BridgeCardProps> = ({ data, onBridgeInitiate }) => {
  const { transaction, balance_check, bridge_options } = data;
  const [initiating, setInitiating] = useState<string | null>(null);
  const [bridgingState, setBridgingState] = useState<"idle" | "bridging" | "done">("idle");
  const [selectedProtocol, setSelectedProtocol] = useState<string | null>(null);
  const [showConfirmation, setShowConfirmation] = useState(false);

  return (
    <div className="bg-white/60 backdrop-blur-md rounded-xl p-6 my-3 border-2 border-[#DBDBE5] shadow-elevation-md animate-fade-in-up">
      {/* Header */}
      <div className="mb-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-2xl">🌉</span>
          <h2 className="text-2xl font-semibold text-[#010507]">
            {transaction ? "Bridge Transaction" : "Bridge Options"}
          </h2>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span
              className={`px-3 py-1 rounded-full text-xs font-bold text-white ${getChainColor(data.source_chain)}`}
            >
              {data.source_chain.toUpperCase()}
            </span>
            <span className="text-gray-400 text-lg">→</span>
            <span
              className={`px-3 py-1 rounded-full text-xs font-bold text-white ${getChainColor(data.destination_chain)}`}
            >
              {data.destination_chain.toUpperCase()}
            </span>
          </div>
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

      {/* Bridge Amount Summary */}
      <div className="bg-gradient-to-r from-orange-50 to-amber-50 rounded-xl p-4 mb-4 border border-orange-200">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-xs text-[#57575B] mb-1">Amount to Bridge</div>
            <div className="text-2xl font-bold text-[#010507]">
              {data.amount} {data.token_symbol}
            </div>
          </div>
          {data.account_address && (
            <div>
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
                The bridge amount ({data.amount} {data.token_symbol}) exceeds the threshold of{" "}
                {data.confirmation_threshold} {data.token_symbol}. Please review the options below
                and confirm before proceeding.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Bridge Options Display Box (if not yet initiated) */}
      {bridge_options && bridge_options.length > 0 && !transaction && !showConfirmation && (
        <div className="mb-4">
          <div className="bg-white/90 backdrop-blur-md rounded-xl p-5 border-2 border-[#DBDBE5] shadow-elevation-md">
            <h3 className="text-lg font-semibold text-[#010507] mb-2">
              Available Bridge Protocols
            </h3>
            <p className="text-sm text-[#57575B] mb-4">
              {data.requires_confirmation && data.amount_exceeds_threshold
                ? "Please select a protocol and confirm to proceed with the bridge."
                : "Please select a protocol to proceed with the bridge. You can say 'Proceed with [Protocol Name]' or click on a protocol below."}
            </p>
            <div className="space-y-3">
              {bridge_options.map((option: BridgeOption, index: number) => (
                <div
                  key={index}
                  onClick={() => {
                    if (balance_check?.balance_sufficient && !initiating) {
                      setSelectedProtocol(option.bridge_protocol);
                    }
                  }}
                  className={`rounded-lg p-4 border-2 transition-all cursor-pointer ${
                    selectedProtocol === option.bridge_protocol
                      ? "border-orange-500 bg-orange-50 ring-2 ring-orange-200"
                      : option.is_recommended
                        ? "border-orange-300 bg-orange-50/50 hover:border-orange-400 hover:bg-orange-50"
                        : "border-[#E9E9EF] bg-white/80 hover:border-orange-200 hover:bg-orange-50/30"
                  } ${!balance_check?.balance_sufficient ? "opacity-50 cursor-not-allowed" : ""}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-base font-bold text-[#010507]">
                          {option.bridge_protocol}
                        </span>
                        {option.is_recommended && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-orange-500 text-white">
                            RECOMMENDED
                          </span>
                        )}
                      </div>
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <span className="text-[#57575B]">Fee: </span>
                          <span className="font-bold text-[#010507]">{option.bridge_fee}</span>
                        </div>
                        <div>
                          <span className="text-[#57575B]">Estimated Time: </span>
                          <span className="font-semibold text-[#010507]">
                            {option.estimated_time}
                          </span>
                        </div>
                      </div>
                    </div>
                    {selectedProtocol === option.bridge_protocol && (
                      <div className="ml-3 flex-shrink-0">
                        <div className="w-6 h-6 rounded-full bg-orange-500 flex items-center justify-center">
                          <span className="text-white text-xs font-bold">✓</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Selected Option Action Button */}
            {selectedProtocol && (
              <div className="mt-4 pt-4 border-t border-[#E9E9EF]">
                {(() => {
                  const option = bridge_options.find(
                    (opt) => opt.bridge_protocol === selectedProtocol,
                  );
                  if (!option) return null;
                  return (
                    <button
                      onClick={() => {
                        if (!balance_check?.balance_sufficient) return;
                        setShowConfirmation(true);
                      }}
                      disabled={!balance_check?.balance_sufficient}
                      className={`w-full px-4 py-3 rounded-lg font-semibold text-sm transition-all shadow-sm ${
                        balance_check?.balance_sufficient
                          ? "bg-orange-500 hover:bg-orange-600 text-white shadow-md hover:shadow-lg"
                          : "bg-gray-300 text-gray-500 cursor-not-allowed"
                      }`}
                    >
                      Proceed with {option.bridge_protocol}
                    </button>
                  );
                })()}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Transaction Information (after bridge is initiated) */}
      {transaction && (
        <div className="space-y-3">
          <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 shadow-elevation-sm border border-[#E9E9EF]">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-xs text-[#57575B] mb-1">Bridge Protocol</div>
                <div className="text-sm font-semibold text-[#010507]">
                  {transaction.bridge_protocol}
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
              <div className="text-xs text-[#57575B] mb-1">Bridge Fee</div>
              <div className="text-lg font-bold text-[#010507]">{transaction.bridge_fee}</div>
            </div>
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
            <div className="text-xs text-[#57575B] mb-1">Token Address (Source Chain)</div>
            <div className="text-sm font-mono text-[#010507] break-all">
              {transaction.token_address}
            </div>
          </div>
        </div>
      )}

      {/* Status Message */}
      {transaction && transaction.status === "pending" && (
        <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
          <p className="text-sm text-yellow-800">
            ⏳ Bridge transaction is pending. It will be completed in approximately{" "}
            {transaction.estimated_time}.
          </p>
        </div>
      )}

      {transaction && transaction.status === "completed" && (
        <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div>
              <p className="text-sm font-semibold text-green-800 mb-1">
                ✅ Bridge transaction completed successfully!
              </p>
              <p className="text-xs text-green-700">
                Your {transaction.amount} {transaction.token_symbol} have been bridged to{" "}
                {transaction.destination_chain}.
              </p>
            </div>
          </div>
          <button
            onClick={() => {
              setInitiating(transaction.bridge_protocol);
              setBridgingState("bridging");

              // Simulate bridge confirmation process
              setTimeout(() => {
                setBridgingState("done");
                setTimeout(() => {
                  setInitiating(null);
                  setBridgingState("idle");
                }, 1000);
              }, 2000);
            }}
            disabled={initiating !== null && bridgingState !== "idle"}
            className={`w-full px-4 py-3 rounded-lg font-semibold text-sm transition-all shadow-sm ${
              initiating === null || bridgingState === "idle"
                ? "bg-green-600 hover:bg-green-700 text-white shadow-md hover:shadow-lg"
                : bridgingState === "bridging"
                  ? "bg-yellow-500 text-white cursor-not-allowed"
                  : "bg-green-500 text-white cursor-not-allowed"
            }`}
          >
            {bridgingState === "bridging" && initiating === transaction.bridge_protocol ? (
              <span className="flex items-center justify-center gap-2">
                <span className="animate-spin">⏳</span>
                Bridging...
              </span>
            ) : bridgingState === "done" && initiating === transaction.bridge_protocol ? (
              <span className="flex items-center justify-center gap-2">✓ Done</span>
            ) : (
              `Bridge with ${transaction.bridge_protocol}`
            )}
          </button>
          {bridgingState === "bridging" && initiating === transaction.bridge_protocol && (
            <p className="text-xs text-green-700 mt-2 text-center">
              Processing bridge confirmation...
            </p>
          )}
          {bridgingState === "done" && initiating === transaction.bridge_protocol && (
            <p className="text-xs text-green-700 mt-2 text-center">
              Bridge completed! Your tokens are now on {transaction.destination_chain}.
            </p>
          )}
        </div>
      )}

      {transaction && transaction.status === "failed" && (
        <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3">
          <p className="text-sm text-red-800">
            ❌ Bridge transaction failed. Please try again or contact support.
          </p>
        </div>
      )}
    </div>
  );
};
