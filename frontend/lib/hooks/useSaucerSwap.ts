/**
 * React Hook for SaucerSwap Integration
 */

import { useState, useEffect, useCallback } from "react";
import { useAppKitAccount } from "@reown/appkit/react";
import { ethers } from "ethers";
import type { providers, Signer } from "ethers";
import {
  getSwapQuote,
  checkAllowance,
  approveToken,
  executeSwap,
  getTokenBalance,
  getTokenDecimals,
  getDeadline,
  SAUCERSWAP_ROUTER_ADDRESS,
} from "../contracts/saucerswap";

interface SwapParams {
  tokenInAddress: string;
  tokenOutAddress: string;
  amountIn: string;
  slippagePercent: number;
}

export function useSaucerSwap() {
  const { address, isConnected } = useAppKitAccount?.() || {};
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [quote, setQuote] = useState<{ amountOut: string; path: string[] } | null>(null);
  const [balance, setBalance] = useState<string>("0");
  const [allowance, setAllowance] = useState<bigint>(BigInt(0));

  // Get provider and signer from window.ethereum
  const getProvider = useCallback(() => {
    if (typeof window === "undefined" || !(window as any).ethereum) return null;
    return new ethers.providers.Web3Provider((window as any).ethereum);
  }, []);

  const getSigner = useCallback(async () => {
    const prov = getProvider();
    if (!prov || !address) return null;
    return prov.getSigner(address);
  }, [getProvider, address]);

  // Get swap quote
  const fetchQuote = useCallback(
    async (params: SwapParams) => {
      if (
        !params.tokenInAddress ||
        !params.tokenOutAddress ||
        !params.amountIn ||
        parseFloat(params.amountIn) <= 0
      ) {
        setQuote(null);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const prov = getProvider();
        if (!prov) {
          throw new Error("Provider not available");
        }

        const decimalsIn = await getTokenDecimals(prov, params.tokenInAddress);
        const quoteResult = await getSwapQuote(
          prov,
          params.tokenInAddress,
          params.tokenOutAddress,
          params.amountIn,
          decimalsIn,
        );

        setQuote(quoteResult);
      } catch (err: any) {
        console.error("Error fetching quote:", err);
        setError(err.message || "Failed to fetch swap quote");
        setQuote(null);
      } finally {
        setLoading(false);
      }
    },
    [getProvider],
  );

  // Get token balance
  const fetchBalance = useCallback(
    async (tokenAddress: string) => {
      if (!address || !tokenAddress) {
        setBalance("0");
        return;
      }

      try {
        const prov = getProvider();
        if (!prov) {
          setBalance("0");
          return;
        }

        // Validate address format before calling
        // Hedera addresses are in format 0.0.xxxxx, EVM addresses are 0x...
        const isValidAddress =
          address.match(/^0\.0\.\d+$/) || (address.startsWith("0x") && address.length === 42);

        if (!isValidAddress) {
          console.warn("Invalid address format:", address);
          setBalance("0");
          return;
        }

        // For EVM addresses, ensure they're checksummed
        let balanceAddress = address;
        if (address.startsWith("0x") && ethers.utils.isAddress(address)) {
          balanceAddress = ethers.utils.getAddress(address);
        }

        const decimals = await getTokenDecimals(prov, tokenAddress);
        // getTokenBalance now uses Hedera Mirror Node API, so it handles both formats
        const bal = await getTokenBalance(prov, tokenAddress, balanceAddress, decimals);
        setBalance(bal);
      } catch (err: any) {
        // Silently handle ENS errors for non-ENS networks
        if (err.code === "UNSUPPORTED_OPERATION" && err.message?.includes("ENS")) {
          console.warn("ENS not supported, skipping balance fetch");
          setBalance("0");
          return;
        }
        console.error("Error fetching balance:", err);
        setBalance("0");
      }
    },
    [address, getProvider],
  );

  // Check allowance
  const fetchAllowance = useCallback(
    async (tokenAddress: string) => {
      if (!address || !tokenAddress || tokenAddress === "0.0.0") {
        setAllowance(BigInt(0));
        return;
      }

      try {
        const prov = getProvider();
        if (!prov) {
          setAllowance(BigInt(0));
          return;
        }

        const allow = await checkAllowance(prov, tokenAddress, address, SAUCERSWAP_ROUTER_ADDRESS);
        setAllowance(allow);
      } catch (err: any) {
        console.error("Error fetching allowance:", err);
        setAllowance(BigInt(0));
      }
    },
    [address, getProvider],
  );

  // Approve token
  const approve = useCallback(
    async (tokenAddress: string, amount: string) => {
      if (!address || !tokenAddress) {
        throw new Error("Missing address or token");
      }

      setLoading(true);
      setError(null);

      try {
        const signer = await getSigner();
        if (!signer) {
          throw new Error("Signer not available");
        }

        const prov = getProvider();
        if (!prov) {
          throw new Error("Provider not available");
        }

        const decimals = await getTokenDecimals(prov, tokenAddress);
        const tx = await approveToken(signer, tokenAddress, amount, decimals);
        await tx.wait();

        // Refresh allowance
        await fetchAllowance(tokenAddress);
      } catch (err: any) {
        console.error("Error approving token:", err);
        setError(err.message || "Failed to approve token");
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [address, getProvider, getSigner, fetchAllowance],
  );

  // Execute swap
  const swap = useCallback(
    async (params: SwapParams, recipientAddress?: string) => {
      if (!address) {
        throw new Error("Wallet not connected");
      }

      if (!params.tokenInAddress || !params.tokenOutAddress || !params.amountIn) {
        throw new Error("Missing swap parameters");
      }

      setLoading(true);
      setError(null);

      try {
        const signer = await getSigner();
        if (!signer) {
          throw new Error("Signer not available");
        }

        const prov = getProvider();
        if (!prov) {
          throw new Error("Provider not available");
        }

        const decimalsIn = await getTokenDecimals(prov, params.tokenInAddress);
        const decimalsOut = await getTokenDecimals(prov, params.tokenOutAddress);

        // Calculate minimum output with slippage
        const amountOut = quote?.amountOut || "0";
        const amountOutMin = (
          parseFloat(amountOut) *
          (1 - params.slippagePercent / 100)
        ).toString();

        const deadline = getDeadline();
        const recipient = recipientAddress || address;

        const tx = await executeSwap(
          signer,
          params.tokenInAddress,
          params.tokenOutAddress,
          params.amountIn,
          amountOutMin,
          recipient,
          deadline,
          decimalsIn,
          decimalsOut,
          params.slippagePercent,
        );

        const receipt = await tx.wait();
        return receipt;
      } catch (err: any) {
        console.error("Error executing swap:", err);
        setError(err.message || "Failed to execute swap");
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [address, quote, getProvider, getSigner],
  );

  return {
    loading,
    error,
    quote,
    balance,
    allowance,
    fetchQuote,
    fetchBalance,
    fetchAllowance,
    approve,
    swap,
    isConnected: Boolean(isConnected && address),
  };
}
