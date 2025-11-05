"use client";

import { createAppKit } from "@reown/appkit/react";
import { Ethers5Adapter } from "@reown/appkit-adapter-ethers5";
import { polygon, mainnet } from "@reown/appkit/networks";

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

  const ethers5Adapter = new Ethers5Adapter({
    networks: [polygon, mainnet],
    projectId,
  });

  createAppKit({
    adapters: [ethers5Adapter],
    networks: [polygon, mainnet],
    metadata,
    projectId,
    features: {
      analytics: true,
    },
  });

  return ethers5Adapter;
}
