"use client";

import { createAppKit } from "@reown/appkit/react";
import { WagmiAdapter } from "@reown/appkit-adapter-wagmi";
import { cookieStorage, createStorage } from "@wagmi/core";
import { polygon, mainnet, hedera } from "@reown/appkit/networks";
import type { AppKitNetwork } from "@reown/appkit/networks";

// Delayed, client-only initialization to avoid module-eval side effects
export function initAppKit() {
  const projectId = process.env.NEXT_PUBLIC_REOWN_PROJECT_ID || "";

  if (!projectId && typeof window !== "undefined") {
    console.warn(
      "⚠️ Reown AppKit: NEXT_PUBLIC_REOWN_PROJECT_ID is not set. Please create a project at https://cloud.reown.com and add your project ID to .env.local",
    );
  }

  const metadata = {
    name: "AgentFlow101",
    description: "Multi-Agent DeFi Assistant",
    url: typeof window !== "undefined" ? window.location.origin : "https://example.com",
    icons: ["https://avatars.githubusercontent.com/u/179229932"],
  };

  const appKitNetworks: [AppKitNetwork, ...AppKitNetwork[]] = [polygon, mainnet, hedera];
  const wagmiNetworks = [polygon, mainnet, hedera];

  const wagmiAdapter = new WagmiAdapter({
    storage: createStorage({
      storage: cookieStorage,
    }),
    ssr: true,
    projectId,
    networks: wagmiNetworks,
  });

  createAppKit({
    adapters: [wagmiAdapter],
    networks: appKitNetworks,
    metadata,
    projectId,
    includeWalletIds: [
      "a29498d225fa4b13468ff4d6cf4ae0ea4adcbd95f07ce8a843a1dee10b632f3f",
      "c57ca95b47569778a828d19178114f4db188b89b763c899ba0be274e97267d96",
    ],
    excludeWalletIds: [
      "2bd8c14e035c2d48f184aaa168559e86b0e3433228d3c4075900a221785019b0",
      "541d5dcd4ede02f3afaf75bf8e3e4c4f1fb09edb5fa6c4377ebf31c2785d9adf",
    ],

    enableInjected: true,
    enableCoinbase: false,
    allWallets: "HIDE",
    features: {
      analytics: true,
      email: false,
      socials: [],
    },
  });

  return wagmiAdapter;
}
