/**
 * BalanceRequirementsForm Component
 *
 * HITL form that collects balance query details (account address, chain, token)
 * at the start of the workflow. Supports pre-filling from user messages
 * and validates input before submission.
 */

import React, { useState, useEffect } from "react";

interface BalanceRequirementsFormProps {
  args: any;
  respond: any;
}

export const BalanceRequirementsForm: React.FC<BalanceRequirementsFormProps> = ({
  args,
  respond,
}) => {
  let parsedArgs = args;
  if (typeof args === "string") {
    try {
      parsedArgs = JSON.parse(args);
    } catch (e) {
      parsedArgs = {};
    }
  }

  const [accountAddress, setAccountAddress] = useState("");
  const [chain, setChain] = useState("all");
  const [tokenAddress, setTokenAddress] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Pre-fill form from orchestrator extraction
  useEffect(() => {
    if (parsedArgs && parsedArgs.accountAddress && parsedArgs.accountAddress !== accountAddress) {
      setAccountAddress(parsedArgs.accountAddress);
    }
    if (parsedArgs && parsedArgs.chain && parsedArgs.chain !== chain) {
      setChain(parsedArgs.chain);
    }
    if (parsedArgs && parsedArgs.tokenAddress && parsedArgs.tokenAddress !== tokenAddress) {
      setTokenAddress(parsedArgs.tokenAddress);
    }
  }, [parsedArgs?.accountAddress, parsedArgs?.chain, parsedArgs?.tokenAddress]);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!accountAddress.trim()) {
      newErrors.accountAddress = "Please enter an account address";
    } else {
      // Validate Hedera format (0.0.123456) or EVM format (0x...)
      const hederaPattern = /^0\.0\.\d+$/;
      const evmPattern = /^0x[a-fA-F0-9]{40}$/;
      if (!hederaPattern.test(accountAddress.trim()) && !evmPattern.test(accountAddress.trim())) {
        newErrors.accountAddress =
          "Invalid address format. Use Hedera format (0.0.123456) or EVM format (0x...)";
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (!validateForm()) {
      return;
    }

    setSubmitted(true);
    respond?.({
      accountAddress: accountAddress.trim(),
      chain,
      tokenAddress: tokenAddress.trim() || undefined,
    });
  };

  if (submitted) {
    return (
      <div className="bg-[#85E0CE]/30 backdrop-blur-md border-2 border-[#85E0CE] rounded-lg p-4 my-3 shadow-elevation-md">
        <div className="flex items-center gap-2">
          <div className="text-2xl">✓</div>
          <div>
            <h3 className="text-base font-semibold text-[#010507]">Balance Query Submitted</h3>
            <p className="text-xs text-[#57575B]">
              Fetching balance for {accountAddress} on {chain === "all" ? "all chains" : chain}
              {tokenAddress ? ` for token ${tokenAddress}` : ""}...
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#BEC2FF]/30 backdrop-blur-md border-2 border-[#BEC2FF] rounded-lg p-4 my-3 shadow-elevation-md">
      <div className="flex items-center gap-2 mb-4">
        <div className="text-2xl">💱</div>
        <div>
          <h3 className="text-base font-semibold text-[#010507]">Balance Query Details</h3>
          <p className="text-xs text-[#57575B]">Please provide account information to check balance</p>
        </div>
      </div>

      <div className="space-y-3">
        <div>
          <label className="block text-xs font-medium text-[#010507] mb-1.5">
            Account Address *
          </label>
          <input
            type="text"
            value={accountAddress}
            onChange={(e) => setAccountAddress(e.target.value)}
            placeholder="e.g., 0.0.123456 (Hedera) or 0x1234... (EVM)"
            className={`w-full px-3 py-2 text-sm rounded-lg border-2 transition-colors ${
              errors.accountAddress
                ? "border-[#FFAC4D] bg-[#FFAC4D]/10"
                : "border-[#DBDBE5] bg-white/80 backdrop-blur-sm focus:border-[#BEC2FF] focus:outline-none"
            }`}
          />
          {errors.accountAddress && (
            <p className="text-xs text-[#FFAC4D] mt-1">{errors.accountAddress}</p>
          )}
        </div>

        <div>
          <label className="block text-xs font-medium text-[#010507] mb-1.5">Chain *</label>
          <div className="grid grid-cols-3 gap-2">
            {[
              { value: "hedera", label: "Hedera", icon: "🔷" },
              { value: "polygon", label: "Polygon", icon: "🟣" },
              { value: "all", label: "All", icon: "🌐" },
            ].map((option) => (
              <button
                key={option.value}
                onClick={() => setChain(option.value)}
                className={`py-2 px-3 rounded-lg font-medium text-xs transition-all shadow-elevation-sm ${
                  chain === option.value
                    ? "bg-[#BEC2FF] text-white shadow-elevation-md scale-105"
                    : "bg-white/80 backdrop-blur-sm text-[#010507] border-2 border-[#DBDBE5] hover:border-[#BEC2FF]"
                }`}
              >
                <div className="text-base mb-0.5">{option.icon}</div>
                <div>{option.label}</div>
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-[#010507] mb-1.5">
            Token Address (Optional)
          </label>
          <input
            type="text"
            value={tokenAddress}
            onChange={(e) => setTokenAddress(e.target.value)}
            placeholder="e.g., USDC, 0x2791... (leave empty for all tokens)"
            className="w-full px-3 py-2 text-sm rounded-lg border-2 border-[#DBDBE5] bg-white/80 backdrop-blur-sm focus:border-[#BEC2FF] focus:outline-none transition-colors"
          />
          <p className="text-xs text-[#57575B] mt-1">
            Leave empty to get all token balances, or specify a token symbol/address
          </p>
        </div>
      </div>

      <div className="mt-4">
        <button
          onClick={handleSubmit}
          className="w-full bg-[#1B936F] hover:bg-[#189370] text-white font-semibold py-2.5 px-4 text-sm rounded-lg transition-all shadow-elevation-md hover:shadow-elevation-lg"
        >
          Get Balance
        </button>
      </div>
    </div>
  );
};

