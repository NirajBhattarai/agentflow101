"use client";

import { createAppKit } from "@reown/appkit/react";
import { WagmiAdapter } from "@reown/appkit-adapter-wagmi";
import { polygon, mainnet } from "@reown/appkit/networks";

// Get project ID from environment variable
// You'll need to create a project at https://cloud.reown.com
// Set NEXT_PUBLIC_REOWN_PROJECT_ID in your .env.local file
const projectId = process.env.NEXT_PUBLIC_REOWN_PROJECT_ID || "";

if (!projectId && typeof window !== "undefined") {
  console.warn(
    "⚠️ Reown AppKit: NEXT_PUBLIC_REOWN_PROJECT_ID is not set. Please create a project at https://cloud.reown.com and add your project ID to .env.local"
  );
}

// App metadata
const metadata = {
  name: "AgentFlow101",
  description: "Multi-Agent DeFi Assistant",
  url: typeof window !== "undefined" ? window.location.origin : "https://example.com",
  icons: ["https://avatars.githubusercontent.com/u/179229932"],
};

// Create Wagmi adapter
export const wagmiAdapter = new WagmiAdapter({
  networks: [polygon, mainnet], // You can add more networks here
  projectId,
});

// Initialize AppKit
createAppKit({
  adapters: [wagmiAdapter],
  networks: [polygon, mainnet],
  metadata,
  projectId,
  features: {
    analytics: true,
  },
});

