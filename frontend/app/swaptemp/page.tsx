"use client";

import { useState, useEffect } from "react";
import {
  useAppKitAccount,
  useAppKitProvider,
  useAppKitNetworkCore,
  type Provider,
} from "@reown/appkit/react";
import { WalletConnect } from "@/components/WalletConnect";
import { ROUTER_ABI } from "@/lib/contracts/router-abi";
import {
  useReadContract,
  useWriteContract,
  useChainId,
  useSwitchChain,
  useWalletClient,
} from "wagmi";
import { ethers } from "ethers";
import { Client, AccountId, ContractExecuteTransaction, Hbar } from "@hashgraph/sdk";

export default function SwapTempPage() {
  const { writeContract, isSuccess } = useWriteContract();
  const chainId = useChainId();
  const { switchChainAsync } = useSwitchChain();
  const { data: walletClient } = useWalletClient();
  const { address } = useAppKitAccount?.() || ({} as any);
  const networkCore = useAppKitNetworkCore();
  const isConnected = Boolean(address);

  // Swap state
  const [tokenIn, setTokenIn] = useState({ symbol: "", amount: "", address: "" });
  const [tokenOut, setTokenOut] = useState({ symbol: "", amount: "", address: "" });
  const [slippage, setSlippage] = useState("0.5");
  const [showTokenInSelect, setShowTokenInSelect] = useState(false);
  const [showTokenOutSelect, setShowTokenOutSelect] = useState(false);
  const [showSlippageSettings, setShowSlippageSettings] = useState(false);
  const [swapping, setSwapping] = useState(false);
  // Fresh design: no explicit DEX selection in UI for now
  const [balance, setBalance] = useState("0.0000");
  const [tokenInSearch, setTokenInSearch] = useState("");
  const [tokenOutSearch, setTokenOutSearch] = useState("");

  // All available tokens - single source of truth
  const allTokens = [
    {
      symbol: "HBAR",
      name: "Hedera Hashgraph",
      address: "0.0.0",
      icon: "💎",
      evmAddress: "0x0000000000000000000000000000000000000000",
    },
    {
      symbol: "USDC",
      name: "USD Coin",
      address: "0.0.456858",
      icon: "💵",
      evmAddress: "0x000000000000000000000000000000000006f89a",
    },
    {
      symbol: "USDT",
      name: "Tether USD",
      address: "0.0.1055472",
      icon: "💵",
      evmAddress: "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
    },
    {
      symbol: "ETH",
      name: "Ethereum",
      address: "0.0.541564",
      icon: "🔷",
      evmAddress: "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
    },
    {
      symbol: "BTC",
      name: "Bitcoin",
      address: "0.0.1055483",
      icon: "₿",
      evmAddress: "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
    },
  ];

  // SaucerSwap Router Contract Address on Hedera Mainnet
  // Source: https://docs.saucerswap.finance/
  const SAUCERSWAP_ROUTER_ADDRESS = "0x00000000000000000000000000000000006715e6"; //

  // const routerContract = new ethers.Contract(SAUCERSWAP_ROUTER_ADDRESS, ROUTER_ABI, provider);

  // Use the same array for both token in and token out
  const currentTokens = allTokens;

  const handleSwapTokens = () => {
    const temp = { ...tokenIn };
    setTokenIn({ ...tokenOut });
    setTokenOut(temp);
  };

  const handleTokenInSelect = (token: (typeof currentTokens)[0]) => {
    setTokenIn({ symbol: token.symbol, amount: tokenIn.amount, address: token.address });
    setShowTokenInSelect(false);
  };

  const handleTokenOutSelect = (token: (typeof allTokens)[0]) => {
    setTokenOut({ symbol: token.symbol, amount: tokenOut.amount, address: token.address });
    setShowTokenOutSelect(false);
  };

  // Calculate estimated output (mock calculation for UI)
  useEffect(() => {
    if (tokenIn.amount && tokenIn.symbol && tokenOut.symbol && parseFloat(tokenIn.amount) > 0) {
      // Mock calculation - will be replaced with real quote later
      const mockRate = 1.05; // Example: 1 token in = 1.05 tokens out
      const estimated = (parseFloat(tokenIn.amount) * mockRate).toFixed(6);
      setTokenOut((prev) => ({ ...prev, amount: estimated }));
    } else if (!tokenIn.amount || parseFloat(tokenIn.amount) <= 0) {
      setTokenOut((prev) => ({ ...prev, amount: "" }));
    }
  }, [tokenIn.amount, tokenIn.symbol, tokenOut.symbol]);

  /**
   * Fetch balance from Hedera Mirror Node API
   * API endpoint: https://mainnet.mirrornode.hedera.com/api/v1/balances?account.id={address}
   * Accepts both EVM (0x...) and Hedera (0.0.xxxxx) address formats
   * Response structure:
   * {
   *   "balances": [{
   *     "account": "0.0.10083096",  // Hedera address from API
   *     "balance": 631419050,  // HBAR in tinybars
   *     "tokens": [{
   *       "token_id": "0.0.456858",
   *       "balance": 0
   *     }]
   *   }]
   * }
   */
  const fetchTokenBalance = async (tokenAddress: string, accountAddress: string) => {
    if (!tokenAddress || !accountAddress) {
      setBalance("0.0000");
      return;
    }

    try {
      // API accepts both EVM and Hedera format addresses directly
      const mirrorNodeUrl = "https://mainnet.mirrornode.hedera.com";
      const response = await fetch(`${mirrorNodeUrl}/api/v1/balances?account.id=${accountAddress}`);

      if (response.ok) {
        const data = await response.json();

        if (data.balances && data.balances.length > 0) {
          const accountBalance = data.balances[0]; // Get first balance entry

          // Get Hedera address from API response (account field)
          const hederaAccountId = accountBalance.account; // e.g., "0.0.10083096"

          // Handle native HBAR (0.0.0)
          if (tokenAddress === "0.0.0") {
            // HBAR balance is in tinybars (1 HBAR = 100,000,000 tinybars)
            const hbarBalance = accountBalance.balance / 100000000;
            setBalance(hbarBalance.toFixed(8));
            return;
          }

          // For HTS tokens, find token in tokens array
          // API returns tokens with token_id in Hedera format (0.0.xxxxx)
          // Our token addresses are also in Hedera format, so we can match directly
          if (accountBalance.tokens && accountBalance.tokens.length > 0) {
            // Find token balance in tokens array (token_id is already in Hedera format from API)
            const tokenBalanceData = accountBalance.tokens.find(
              (t: any) => t.token_id === tokenAddress,
            );

            if (tokenBalanceData) {
              // Token balance is in the smallest unit, assume 8 decimals (Hedera standard)
              // TODO: Fetch actual decimals from token info
              const decimals = 8;
              const decimalsValue = Math.pow(10, decimals);
              const formattedBalance = (tokenBalanceData.balance / decimalsValue).toFixed(decimals);
              setBalance(formattedBalance);
              return;
            }
          }
        }
      }

      // If no balance found, set to 0
      setBalance("0.0000");
    } catch (error) {
      console.error("Error fetching token balance:", error);
      setBalance("0.0000");
    }
  };

  // Fetch balance when token is selected
  useEffect(() => {
    if (tokenIn.address && address) {
      fetchTokenBalance(tokenIn.address, address);
    } else {
      setBalance("0.0000");
    }
  }, [tokenIn.address, address]);

  // Helper function to convert hex string to Uint8Array (from swapHbarToTokenHardcode)
  const hexStringToUint8Array = (hexString: string): Uint8Array => {
    if (hexString.length % 2 !== 0) {
      throw new Error("Invalid hexString: odd length");
    }
    const arrayBuffer = new Uint8Array(hexString.length / 2);
    for (let i = 0; i < hexString.length; i += 2) {
      const byteValue = parseInt(hexString.slice(i, i + 2), 16);
      if (isNaN(byteValue)) {
        throw new Error("Invalid hexString: contains non-hex characters");
      }
      arrayBuffer[i / 2] = byteValue;
    }
    return arrayBuffer;
  };

  // Direct swap using Hedera SDK approach with connected wallet
  const handleDirectSwap = async () => {
    handleDirectSwapHederaSDK();
  };

  // Direct swap using ethers.js approach (same as swapHbarToTokenEthers.ts)
  const handleDirectSwapEthers = async () => {
    if (!isConnected) {
      alert("Please connect your wallet first");
      return;
    }

    if (!address || !walletClient) {
      alert("Wallet address or client not available");
      return;
    }

    setSwapping(true);

    try {
      // Hardcoded values (same as swapHbarToTokenEthers.ts)
      const hbarAmountStr = "0.01"; // Hardcoded: 0.01 HBAR for easy testing
      const RPC_URL = "https://mainnet.hashio.io/api";
      const ROUTER_ADDRESS = "0x00000000000000000000000000000000006715e6"; // Mainnet router EVM address

      // Hardcoded path (same as swapHbarToTokenEthers.ts)
      const HARDCODED_PATH_EVM = [
        "0x0000000000000000000000000000000000163B5a", // WHBAR
        "0x000000000000000000000000000000000006f89a", // USDC
      ];

      console.log("🔄 Direct Swap (Ethers.js Approach - same as swapHbarToTokenEthers):", {
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
      console.log(`   Amount Out Min: ${amountOutMin} (using 0 - no minimum check)`);
      console.log(`   Deadline: ${deadline} (20 minutes from now)`);

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

      console.log(`   Transaction data: ${populatedTx.data}`);
      console.log(
        `   Transaction value: ${ethers.formatEther(populatedTx.value || BigInt(0))} HBAR`,
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

      // Wait for transaction receipt
      console.log("🔄 Waiting for transaction confirmation...");
      const receipt = await txResponse.wait();

      if (!receipt || receipt.status !== 1) {
        throw new Error(`Transaction failed with status: ${receipt?.status}`);
      }

      console.log("✅ Transaction confirmed!");
      console.log(`   Block Number: ${receipt.blockNumber}`);
      console.log(`   Gas Used: ${receipt.gasUsed.toString()}`);

      alert(
        `✅ Swap completed! Swapped ${hbarAmountStr} HBAR to USDC.\nTransaction Hash: ${txResponse.hash}`,
      );
      setSwapping(false);
    } catch (err: any) {
      console.error("Direct swap error (ethers):", err);
      setSwapping(false);
      alert(err?.message || "Direct swap failed. Please try again.");
    }
  };

  // Direct swap using Hedera SDK approach (same as swapHbarToTokenHardcode.ts)
  const handleDirectSwapHederaSDK = async () => {
    if (!isConnected) {
      alert("Please connect your wallet first");
      return;
    }

    if (!address) {
      alert("Wallet address not available");
      return;
    }

    setSwapping(true);

    try {
      // Hardcoded values (same as swapHbarToTokenHardcode.ts)
      const hbarAmount = 0.1; // Hardcoded: 0.1 HBAR
      const amountInTinybars = BigInt(Math.floor(hbarAmount * 100_000_000));
      const targetTokenEvmAddress = "0x000000000000000000000000000000000006f89a"; // Hardcoded: USDC

      // Hardcoded path from swapHbarToTokenHardcode.ts
      const swapPath = [
        "0x0000000000000000000000000000000000163B5a", // WHBAR
        "0x000000000000000000000000000000000078Eeda", // Token1
        "0x0000000000000000000000000000000000790451", // Token2
        targetTokenEvmAddress, // USDC
      ];

      const deadline = Math.floor(Date.now() / 1000) + 20 * 60;
      const amountOutMin = BigInt(0);

      console.log("🔄 Direct Swap (Hedera SDK Approach - same as swapHbarToTokenHardcode):", {
        amountIn: hbarAmount,
        amountInTinybars: amountInTinybars.toString(),
        path: swapPath,
        recipient: address,
      });

      // Use Hedera SDK approach (same as swapHbarToTokenHardcode.ts)
      const routerAbiInterface = new ethers.Interface(ROUTER_ABI);

      // Encode swapExactETHForTokens function call (same as swapHbarToTokenHardcode.ts line 190)
      const swapFunctionData = routerAbiInterface.encodeFunctionData("swapExactETHForTokens", [
        amountOutMin,
        swapPath,
        address.toLowerCase(), // Use connected wallet address
        deadline,
      ]);

      // Convert function data to Uint8Array (same as swapHbarToTokenHardcode.ts line 198)
      const functionParameters = hexStringToUint8Array(swapFunctionData.slice(2));

      // Create Hedera SDK transaction (same as swapHbarToTokenHardcode.ts lines 202-206)
      const V2_SWAP_ROUTER_ADDRESS_HEDERA = "0.0.6755814"; // Mainnet router (from swapHbarToTokenHardcode.ts)
      const swapTransaction = new ContractExecuteTransaction()
        .setContractId(V2_SWAP_ROUTER_ADDRESS_HEDERA)
        .setGas(7_000_000)
        .setFunctionParameters(functionParameters)
        .setPayableAmount(Hbar.fromTinybars(amountInTinybars.toString()));

      // Get Hedera client (same as swapHbarToTokenHardcode.ts)
      const client = Client.forMainnet();

      // For HashPack, we don't need to freeze with client since HashPack will handle it
      // But we can prepare the transaction for HashPack's API
      // Try to freeze if possible, otherwise HashPack will handle it
      let frozenTx;
      try {
        // Try to freeze the transaction (may fail if client doesn't have operator set)
        frozenTx = await swapTransaction.freezeWith(client);
      } catch (freezeError: any) {
        // If freezing fails, HashPack should be able to handle the unfrozen transaction
        console.warn("Could not freeze transaction, HashPack will handle it:", freezeError);
        frozenTx = swapTransaction; // Use unfrozen transaction
      }

      // Get account ID from EVM address using Mirror Node API
      // This is needed to sign with Hedera SDK
      let accountId: string;
      try {
        const mirrorNodeUrl = "https://mainnet-public.mirrornode.hedera.com";
        const response = await fetch(`${mirrorNodeUrl}/api/v1/accounts/${address}`);
        if (response.ok) {
          const data = await response.json();
          accountId = data.account || data.account_id;
        } else {
          throw new Error("Could not resolve account ID from address");
        }
      } catch (error) {
        console.warn("Could not get account ID from mirror node, using address directly");
        // Fallback: try to extract from address or use a default
        throw new Error(
          "Could not resolve Hedera account ID. Please ensure you're using HashPack wallet.",
        );
      }

      // Create custom signer function using walletClient from wagmi
      if (!walletClient) {
        throw new Error("Wallet client not available. Please reconnect your wallet.");
      }

      // Create signer function that uses HashPack to sign
      const customSigner = async (message: Uint8Array): Promise<Uint8Array> => {
        // Convert message to hex string
        const messageHex =
          "0x" +
          Array.from(message)
            .map((b) => b.toString(16).padStart(2, "0"))
            .join("");

        // Sign with wallet client
        const signature = await walletClient.signMessage({
          message: messageHex,
        });

        // Convert signature back to Uint8Array
        // Remove 0x prefix and convert to bytes
        const sigBytes = new Uint8Array(
          signature
            .slice(2)
            .match(/.{1,2}/g)
            ?.map((byte: string) => parseInt(byte, 16)) || [],
        );

        return sigBytes;
      };

      // Use Hedera SDK with custom signer from wagmi
      const hederaAccountId = AccountId.fromString(accountId);

      // Try HashPack's native Hedera SDK API first
      // HashPack can handle both frozen and unfrozen transactions
      if (typeof window !== "undefined" && (window as any).hashpack) {
        try {
          const hashpack = (window as any).hashpack;

          // Try with frozen transaction first, then unfrozen if needed
          let result;
          try {
            result = await hashpack.sendTransaction({
              transaction: frozenTx,
              returnTransaction: false,
            });
          } catch (frozenError: any) {
            // If frozen transaction fails, try with unfrozen
            console.warn("Frozen transaction failed, trying unfrozen:", frozenError);
            result = await hashpack.sendTransaction({
              transaction: swapTransaction,
              returnTransaction: false,
            });
          }

          console.log("✅ Direct swap transaction sent via HashPack (Hedera SDK):", result);
          alert(
            `Swap submitted! Swapping ${hbarAmount} HBAR to USDC. Transaction ID: ${result.transactionId}`,
          );
          setSwapping(false);
          return;
        } catch (error: any) {
          console.warn("HashPack native API failed, trying alternative method:", error);
        }
      }

      // Use Hedera SDK's signWithSigner with wagmi signer
      // Create signer function compatible with Hedera SDK
      // Note: Hedera SDK's signWithSigner expects a Signer object, not just a function
      // We'll use HashPack's native API or fall back to wagmi

      // Try to use HashPack's Hedera transaction signing
      // If HashPack native API is not available, we'll use wagmi as fallback

      // Final fallback: Use wagmi with same encoding
      console.log("Using wagmi writeContract with Hedera SDK encoding (fallback)");
      const tx = await writeContract({
        address: SAUCERSWAP_ROUTER_ADDRESS as `0x${string}`,
        abi: ROUTER_ABI,
        functionName: "swapExactETHForTokens",
        args: [amountOutMin, swapPath, address as `0x${string}`, deadline],
        value: amountInTinybars,
        gas: BigInt(7_000_000),
      });

      console.log("✅ Direct swap transaction sent (fallback to wagmi):", tx);
      alert(
        `Swap submitted! Swapping ${hbarAmount} HBAR to USDC. Check your wallet for confirmation.`,
      );

      setSwapping(false);
    } catch (err: any) {
      console.error("Direct swap error:", err);
      setSwapping(false);
      alert(err?.message || "Direct swap failed. Please try again.");
    }
  };

  // Handle swap execution (HBAR/native <-> token)
  const handleSwap = async () => {
    if (!isConnected) {
      alert("Please connect your wallet first");
      return;
    }

    if (!tokenIn.amount || parseFloat(tokenIn.amount) <= 0) {
      alert("Please enter a valid amount");
      return;
    }

    // Only support HBAR to Token swaps for now
    if (tokenIn.symbol !== "HBAR") {
      alert("Currently only HBAR to Token swaps are supported");
      return;
    }

    if (!tokenOut.address) {
      alert("Please select a token to swap to");
      return;
    }

    setSwapping(true);

    try {
      // Ensure we're on Hedera mainnet (chainId 295)
      if (chainId !== 295 && switchChainAsync) {
        await switchChainAsync({ chainId: 295 });
      }

      // Convert HBAR amount to tinybars (1 HBAR = 100,000,000 tinybars)
      const hbarAmount = parseFloat(tokenIn.amount);
      const amountInTinybars = BigInt(Math.floor(hbarAmount * 100_000_000));

      // Hardcoded path from swapHbarToTokenHardcode.ts
      // Path: WHBAR -> Token1 -> Token2 -> Target Token
      const hardcodedPath = [
        "0x0000000000000000000000000000000000163B5a", // WHBAR
        "0x000000000000000000000000000000000078Eeda", // Token1
        "0x0000000000000000000000000000000000790451", // Token2
      ];

      // Get target token EVM address
      const targetToken = allTokens.find((t) => t.address === tokenOut.address);
      if (!targetToken) {
        throw new Error("Target token not found");
      }

      // Use target token's EVM address (or convert Hedera ID to EVM if needed)
      let targetTokenEvmAddress: string;
      if (
        targetToken.evmAddress &&
        targetToken.evmAddress !== "0x0000000000000000000000000000000000000000"
      ) {
        targetTokenEvmAddress = targetToken.evmAddress.toLowerCase();
      } else {
        // Convert Hedera token ID to EVM address
        const parts = tokenOut.address.split(".");
        if (parts.length !== 3) {
          throw new Error("Invalid token address format");
        }
        const num = parseInt(parts[2], 10);
        const numHex = num.toString(16).padStart(6, "0").toLowerCase();
        targetTokenEvmAddress = `0x0000000000000000000000000000000000${numHex}`;
      }

      // Complete path with target token
      const swapPath = [...hardcodedPath, targetTokenEvmAddress];

      console.log("🔄 Swap Details:", {
        amountIn: hbarAmount,
        amountInTinybars: amountInTinybars.toString(),
        path: swapPath,
        recipient: address,
        tokenOut: tokenOut.symbol,
      });

      // Calculate deadline (20 minutes from now)
      const deadline = Math.floor(Date.now() / 1000) + 20 * 60;

      // Minimum amount out (0 for now - no minimum check)
      const amountOutMin = BigInt(0);

      if (!address) {
        throw new Error("Wallet address not available");
      }

      // Execute swap using wagmi's writeContract
      // Note: wagmi will handle gas pricing automatically through HashPack
      const tx = await writeContract({
        address: SAUCERSWAP_ROUTER_ADDRESS as `0x${string}`,
        abi: ROUTER_ABI,
        functionName: "swapExactETHForTokens",
        args: [
          amountOutMin,
          swapPath,
          address as `0x${string}`, // Use connected wallet address as recipient
          deadline,
        ],
        value: amountInTinybars,
        gas: BigInt(7_000_000),
      });

      console.log("✅ Swap transaction sent:", tx);
      alert("Swap transaction submitted! Check your wallet for confirmation.");

      setSwapping(false);
    } catch (err: any) {
      console.error("Swap error:", err);
      setSwapping(false);
      alert(err?.message || "Swap failed. Please try again.");
    }
  };

  return (
    <div className="min-h-screen bg-[#0d1117] w-full">
      {/* Header */}
      <div className="border-b border-gray-800 bg-[#161b22] sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-semibold text-white">Swap</h1>
            </div>
            <div className="flex items-center gap-3">
              {/* Direct Swap Button (Ethers.js - Hardcoded) */}
              <button
                onClick={handleDirectSwapEthers}
                disabled={!isConnected || swapping}
                className={`px-4 py-2 rounded-lg font-medium text-sm transition-all ${
                  !isConnected || swapping
                    ? "bg-gray-800 text-gray-600 cursor-not-allowed"
                    : "bg-blue-600 text-white hover:bg-blue-700"
                }`}
                title="Quick swap using ethers.js: 0.01 HBAR → USDC (hardcoded, easy to test)"
              >
                {swapping ? "Processing..." : "Quick Swap Ethers (0.01 HBAR → USDC)"}
              </button>
              {/* Direct Swap Button (Hedera SDK - Hardcoded) */}
              <button
                onClick={handleDirectSwap}
                disabled={!isConnected || swapping}
                className={`px-4 py-2 rounded-lg font-medium text-sm transition-all ${
                  !isConnected || swapping
                    ? "bg-gray-800 text-gray-600 cursor-not-allowed"
                    : "bg-green-600 text-white hover:bg-green-700"
                }`}
                title="Quick swap: 0.1 HBAR → USDC (hardcoded)"
              >
                {swapping ? "Processing..." : "Quick Swap SDK (0.1 HBAR → USDC)"}
              </button>
              <WalletConnect />
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pb-16 w-full">
        <div className="flex justify-center">
          <div className="w-full max-w-md">
            {/* Swap Card */}
            <div className="bg-[#161b22] rounded-2xl border border-gray-800 overflow-hidden shadow-xl">
              {/* Card Header */}
              <div className="px-6 py-4 border-b border-gray-800 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-white">Swap</h2>
                <button
                  onClick={() => setShowSlippageSettings(!showSlippageSettings)}
                  className="text-sm text-gray-400 hover:text-gray-300 flex items-center gap-1"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                  Slippage
                </button>
              </div>

              {/* Slippage Settings */}
              {showSlippageSettings && (
                <div className="px-6 py-4 border-b border-gray-800 bg-[#0d1117]">
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Slippage Tolerance (%)
                  </label>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setSlippage("0.1")}
                      className={`px-3 py-1.5 rounded-lg text-sm font-medium ${
                        slippage === "0.1"
                          ? "bg-blue-600 text-white"
                          : "bg-gray-800 text-gray-300 hover:bg-gray-700"
                      }`}
                    >
                      0.1%
                    </button>
                    <button
                      onClick={() => setSlippage("0.5")}
                      className={`px-3 py-1.5 rounded-lg text-sm font-medium ${
                        slippage === "0.5"
                          ? "bg-blue-600 text-white"
                          : "bg-gray-800 text-gray-300 hover:bg-gray-700"
                      }`}
                    >
                      0.5%
                    </button>
                    <button
                      onClick={() => setSlippage("1.0")}
                      className={`px-3 py-1.5 rounded-lg text-sm font-medium ${
                        slippage === "1.0"
                          ? "bg-blue-600 text-white"
                          : "bg-gray-800 text-gray-300 hover:bg-gray-700"
                      }`}
                    >
                      1.0%
                    </button>
                    <input
                      type="text"
                      value={slippage}
                      onChange={(e) => setSlippage(e.target.value)}
                      placeholder="Custom"
                      className="flex-1 px-3 py-1.5 rounded-lg border border-gray-700 bg-gray-800 text-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-600"
                    />
                  </div>
                </div>
              )}

              <div className="p-6 space-y-4">
                {/* You pay */}
                <div className="text-xs text-gray-400 mb-1 px-1">You pay</div>
                {/* Token In */}
                <div className="relative">
                  <div className="bg-[#0d1117] rounded-2xl p-4 border border-gray-800 hover:border-gray-700 transition-colors">
                    <div className="flex items-center justify-between mb-2">
                      <button
                        onClick={() => setShowTokenInSelect(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-[#161b22] rounded-xl border border-gray-800 hover:border-gray-700 transition-colors"
                      >
                        {tokenIn.symbol ? (
                          <>
                            <span className="text-lg">
                              {allTokens.find((t) => t.symbol === tokenIn.symbol)?.icon || "🪙"}
                            </span>
                            <span className="font-semibold text-white">{tokenIn.symbol}</span>
                            <svg
                              className="w-4 h-4 text-gray-400"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M19 9l-7 7-7-7"
                              />
                            </svg>
                          </>
                        ) : (
                          <>
                            <span className="text-gray-400">Select token</span>
                            <svg
                              className="w-4 h-4 text-gray-400"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M19 9l-7 7-7-7"
                              />
                            </svg>
                          </>
                        )}
                      </button>
                      {isConnected && (
                        <div className="flex flex-col gap-1">
                          <div className="flex items-center gap-2">
                            <div className="text-xs text-gray-400">
                              Balance:{" "}
                              <span className="font-semibold text-gray-300">{balance}</span>
                            </div>
                            {tokenIn.symbol && parseFloat(balance) > 0 && (
                              <button
                                onClick={(e) => {
                                  e.preventDefault();
                                  e.stopPropagation();
                                  // Set max amount
                                  if (tokenIn.address === "0.0.0") {
                                    // For HBAR, leave 0.1 HBAR for gas fees
                                    const balanceNum = parseFloat(balance);
                                    const gasReserve = 0.1;
                                    const maxAmount = Math.max(0, balanceNum - gasReserve).toFixed(
                                      8,
                                    );
                                    setTokenIn({ ...tokenIn, amount: maxAmount });
                                  } else {
                                    // For tokens, use full balance
                                    setTokenIn({
                                      ...tokenIn,
                                      amount: parseFloat(balance).toFixed(8),
                                    });
                                  }
                                }}
                                className="text-xs px-2 py-1 bg-blue-600/20 text-blue-400 rounded-lg hover:bg-blue-600/30 font-medium transition-colors"
                              >
                                MAX
                              </button>
                            )}
                          </div>
                          {address && (
                            <div className="text-xs text-gray-500 font-mono">{address}</div>
                          )}
                        </div>
                      )}
                    </div>
                    <input
                      type="text"
                      value={tokenIn.amount}
                      onChange={(e) => {
                        const val = e.target.value;
                        if (val === "" || /^\d*\.?\d*$/.test(val)) {
                          setTokenIn({ ...tokenIn, amount: val });
                        }
                      }}
                      placeholder="0.0"
                      className="w-full text-3xl font-semibold bg-transparent border-none outline-none text-white placeholder-gray-600"
                    />
                  </div>

                  {/* Token In Dropdown */}
                  {showTokenInSelect && (
                    <div className="absolute z-50 w-full mt-2 bg-[#161b22] rounded-2xl shadow-2xl border border-gray-800 max-h-80 overflow-hidden">
                      <div className="p-3 border-b border-gray-800">
                        <input
                          type="text"
                          placeholder="Search tokens..."
                          value={tokenInSearch}
                          onChange={(e) => setTokenInSearch(e.target.value)}
                          className="w-full px-3 py-2 rounded-lg border border-gray-800 bg-[#0d1117] text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-600"
                          autoFocus
                        />
                      </div>
                      <div className="max-h-64 overflow-y-auto">
                        {allTokens
                          .filter((token) => {
                            const search = tokenInSearch.toLowerCase();
                            return (
                              token.symbol.toLowerCase().includes(search) ||
                              token.name.toLowerCase().includes(search)
                            );
                          })
                          .map((token) => {
                            return (
                              <button
                                key={token.symbol}
                                onClick={() => {
                                  handleTokenInSelect(token);
                                  setTokenInSearch("");
                                }}
                                className="w-full px-4 py-3 flex items-center gap-3 hover:bg-[#0d1117] transition-colors border-b border-gray-800 last:border-b-0"
                              >
                                <span className="text-2xl">{token.icon}</span>
                                <div className="flex-1 text-left">
                                  <div className="font-semibold text-white">{token.symbol}</div>
                                  <div className="text-xs text-gray-400">{token.name}</div>
                                </div>
                              </button>
                            );
                          })}
                      </div>
                    </div>
                  )}
                </div>

                {/* Swap Button */}
                <div className="flex justify-center -my-2 relative z-10">
                  <button
                    onClick={handleSwapTokens}
                    className="w-10 h-10 rounded-full bg-[#161b22] border-2 border-gray-800 hover:border-gray-700 transition-all flex items-center justify-center hover:bg-[#0d1117]"
                  >
                    <svg
                      className="w-5 h-5 text-gray-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4"
                      />
                    </svg>
                  </button>
                </div>

                {/* You receive */}
                <div className="text-xs text-gray-400 mt-3 mb-1 px-1">You receive</div>
                {/* Token Out */}
                <div className="relative">
                  <div className="bg-[#0d1117] rounded-2xl p-4 border border-gray-800 hover:border-gray-700 transition-colors">
                    <div className="flex items-center justify-between mb-2">
                      <button
                        onClick={() => setShowTokenOutSelect(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-[#161b22] rounded-xl border border-gray-800 hover:border-gray-700 transition-colors"
                      >
                        {tokenOut.symbol ? (
                          <>
                            <span className="text-lg">
                              {allTokens.find((t) => t.symbol === tokenOut.symbol)?.icon || "🪙"}
                            </span>
                            <span className="font-semibold text-white">{tokenOut.symbol}</span>
                            <svg
                              className="w-4 h-4 text-gray-400"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M19 9l-7 7-7-7"
                              />
                            </svg>
                          </>
                        ) : (
                          <>
                            <span className="text-gray-400">Select token</span>
                            <svg
                              className="w-4 h-4 text-gray-400"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M19 9l-7 7-7-7"
                              />
                            </svg>
                          </>
                        )}
                      </button>
                      {isConnected && tokenOut.amount && (
                        <div className="text-xs text-gray-400">
                          ≈{" "}
                          <span className="font-semibold text-gray-300">
                            ${(parseFloat(tokenOut.amount) * 1).toFixed(2)}
                          </span>
                        </div>
                      )}
                    </div>
                    <input
                      type="text"
                      value={tokenOut.amount}
                      readOnly
                      placeholder="0.0"
                      className="w-full text-3xl font-semibold bg-transparent border-none outline-none text-white placeholder-gray-600"
                    />
                  </div>

                  {/* Token Out Dropdown - All Available Tokens */}
                  {showTokenOutSelect && (
                    <div className="absolute z-[60] w-full mt-2 bg-[#161b22] rounded-2xl shadow-2xl border border-gray-800 max-h-96 overflow-hidden">
                      <div className="p-3 border-b border-gray-800">
                        <input
                          type="text"
                          placeholder="Search tokens..."
                          value={tokenOutSearch}
                          onChange={(e) => setTokenOutSearch(e.target.value)}
                          className="w-full px-3 py-2 rounded-lg border border-gray-800 bg-[#0d1117] text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-600"
                          autoFocus
                        />
                      </div>
                      <div className="max-h-80 overflow-y-auto">
                        {/* Show all available tokens */}
                        {allTokens
                          .filter((token) => {
                            const search = tokenOutSearch.toLowerCase();
                            return (
                              token.symbol.toLowerCase().includes(search) ||
                              token.name.toLowerCase().includes(search)
                            );
                          })
                          .map((token, index) => {
                            return (
                              <button
                                key={`token-out-${token.symbol}-${index}`}
                                onClick={() => {
                                  handleTokenOutSelect(token);
                                  setShowTokenOutSelect(false);
                                  setTokenOutSearch("");
                                }}
                                className="w-full px-4 py-3 flex items-center gap-3 hover:bg-[#0d1117] transition-colors border-b border-gray-800 last:border-b-0"
                              >
                                <span className="text-2xl">{token.icon}</span>
                                <div className="flex-1 text-left">
                                  <div className="font-semibold text-white">{token.symbol}</div>
                                  <div className="text-xs text-gray-400">{token.name}</div>
                                </div>
                              </button>
                            );
                          })}
                        {allTokens.filter((token) => {
                          const search = tokenOutSearch.toLowerCase();
                          return (
                            token.symbol.toLowerCase().includes(search) ||
                            token.name.toLowerCase().includes(search)
                          );
                        }).length === 0 && (
                          <div className="px-4 py-8 text-center text-gray-400 text-sm">
                            No tokens found
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                {/* Swap Info */}
                {tokenIn.amount && tokenOut.amount && tokenIn.symbol && tokenOut.symbol && (
                  <div className="space-y-2 pt-2 border-t border-gray-800">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Price</span>
                      <span className="text-gray-300 font-medium">
                        1 {tokenIn.symbol} ={" "}
                        {(parseFloat(tokenOut.amount) / parseFloat(tokenIn.amount)).toFixed(6)}{" "}
                        {tokenOut.symbol}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Price Impact</span>
                      <span className="text-green-400 font-medium">0.01%</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Minimum Received</span>
                      <span className="text-gray-300 font-medium">
                        {(parseFloat(tokenOut.amount) * (1 - parseFloat(slippage) / 100)).toFixed(
                          6,
                        )}{" "}
                        {tokenOut.symbol}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Fee</span>
                      <span className="text-gray-300 font-medium">0.3%</span>
                    </div>
                  </div>
                )}

                {/* Swap Button */}
                <button
                  disabled={
                    !isConnected ||
                    !tokenIn.symbol ||
                    !tokenOut.symbol ||
                    !tokenIn.amount ||
                    parseFloat(tokenIn.amount) <= 0 ||
                    swapping
                  }
                  onClick={handleSwap}
                  className={`w-full py-4 rounded-xl font-semibold text-lg transition-all ${
                    !isConnected
                      ? "bg-gray-800 text-gray-600 cursor-not-allowed"
                      : !tokenIn.symbol ||
                          !tokenOut.symbol ||
                          !tokenIn.amount ||
                          parseFloat(tokenIn.amount) <= 0
                        ? "bg-gray-800 text-gray-600 cursor-not-allowed"
                        : swapping
                          ? "bg-gray-700 text-gray-400 cursor-not-allowed"
                          : "bg-blue-600 text-white hover:bg-blue-700"
                  }`}
                >
                  {swapping
                    ? "Processing..."
                    : !isConnected
                      ? "Connect Wallet"
                      : !tokenIn.symbol || !tokenOut.symbol
                        ? "Select Tokens"
                        : !tokenIn.amount || parseFloat(tokenIn.amount) <= 0
                          ? "Enter Amount"
                          : "Swap"}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Close dropdowns when clicking outside */}
      {(showTokenInSelect || showTokenOutSelect) && (
        <div
          className="fixed inset-0 z-[50] bg-black/20"
          onClick={() => {
            setShowTokenInSelect(false);
            setShowTokenOutSelect(false);
          }}
        />
      )}
    </div>
  );
}
