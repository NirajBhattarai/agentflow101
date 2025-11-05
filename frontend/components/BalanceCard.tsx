/**
 * BalanceCard Component
 *
 * Displays account balance information with token breakdowns and USD values.
 * Uses purple/indigo styling to match the Balance Agent branding.
 */

import React from "react";
import { BalanceData } from "./types";

interface BalanceCardProps {
  data: BalanceData;
}

/**
 * Format token symbol for display
 */
const formatTokenSymbol = (symbol: string): string => {
  return symbol.toUpperCase();
};

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

export const BalanceCard: React.FC<BalanceCardProps> = ({ data }) => {
  // Group balances by chain if multiple chains
  const balancesByChain = data.chain === "all" 
    ? data.balances.reduce((acc, balance) => {
        const chain = balance.chain || "unknown";
        if (!acc[chain]) acc[chain] = [];
        acc[chain].push(balance);
        return acc;
      }, {} as Record<string, typeof data.balances>)
    : { [data.chain]: data.balances };

  return (
    <div className="bg-white/60 backdrop-blur-md rounded-xl p-6 my-3 border-2 border-[#DBDBE5] shadow-elevation-md animate-fade-in-up">
      {/* Header */}
      <div className="mb-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-2xl">💰</span>
          <h2 className="text-2xl font-semibold text-[#010507]">Account Balance</h2>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-[#57575B] font-mono">{data.account_address}</span>
          {data.chain !== "all" && (
            <span className={`px-2 py-1 rounded-full text-xs font-semibold text-white ${getChainColor(data.chain)}`}>
              {data.chain.toUpperCase()}
            </span>
          )}
        </div>
        {data.total_usd_value && (
          <div className="mt-2">
            <span className="text-3xl font-bold text-[#010507]">{data.total_usd_value}</span>
            <span className="text-sm text-[#57575B] ml-2">Total Value</span>
          </div>
        )}
      </div>

      {/* Error Message */}
      {data.error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
          <p className="text-sm text-red-800">{data.error}</p>
        </div>
      )}

      {/* Balances by Chain */}
      {Object.entries(balancesByChain).map(([chain, balances]) => (
        <div key={chain} className="mb-4">
          {data.chain === "all" && (
            <div className="mb-3">
              <h3 className={`text-lg font-semibold text-white px-3 py-1 rounded-lg inline-block ${getChainColor(chain)}`}>
                {chain.toUpperCase()}
              </h3>
            </div>
          )}

          {/* Token Balances */}
          <div className="space-y-2">
            {balances.map((balance, index) => (
              <div
                key={index}
                className="bg-white/80 backdrop-blur-sm rounded-lg p-4 shadow-elevation-sm border border-[#E9E9EF]"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center justify-center w-10 h-10 rounded-full bg-gradient-to-r from-purple-100 to-indigo-100 border-2 border-purple-300">
                      <span className="text-lg">{balance.token_type === "native" ? "🪙" : "🪙"}</span>
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-lg font-bold text-[#010507]">
                          {formatTokenSymbol(balance.token_symbol)}
                        </span>
                        {balance.token_type === "native" && (
                          <span className="text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-700 font-semibold">
                            Native
                          </span>
                        )}
                        {balance.token_type === "token" && (
                          <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 font-semibold">
                            Token
                          </span>
                        )}
                      </div>
                      <span className="text-xs text-[#838389] font-mono">{balance.token_address}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xl font-bold text-[#010507]">{balance.balance}</div>
                    <div className="text-xs text-[#838389]">
                      Raw: {balance.balance_raw}
                    </div>
                  </div>
                </div>

                {/* Token Details */}
                <div className="mt-2 pt-2 border-t border-[#E9E9EF]">
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-[#57575B]">Decimals: </span>
                      <span className="font-semibold text-[#010507]">{balance.decimals}</span>
                    </div>
                    <div>
                      <span className="text-[#57575B]">Type: </span>
                      <span className="font-semibold text-[#010507] capitalize">{balance.token_type}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Empty State */}
      {data.balances.length === 0 && !data.error && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-center">
          <p className="text-sm text-gray-600">No balances found for this account</p>
        </div>
      )}
    </div>
  );
};

