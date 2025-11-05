"use client";

/**
 * DeFi Chat Component
 *
 * Demonstrates key patterns:
 * - A2A Communication: Visualizes message flow between orchestrator and agents
 * - HITL: Balance requirements form for gathering account information
 * - Multi-Agent: Coordinates balance and liquidity agents via A2A Protocol
 */

import React from "react";
import { CopilotKit, useCopilotChat } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import { useCopilotAction } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";
import { BalanceRequirementsForm } from "./forms/BalanceRequirementsForm";

const ChatInner = () => {
  const { visibleMessages } = useCopilotChat();

  // Register HITL balance requirements form (collects account info at start)
  useCopilotAction({
    name: "gather_balance_requirements",
    description:
      "Gather balance query requirements from the user (account address, chain, optional token)",
    parameters: [
      {
        name: "accountAddress",
        type: "string",
        description:
          "The account address to query (Hedera format: 0.0.123456 or EVM format: 0x...). May be pre-filled from user message.",
        required: false,
      },
      {
        name: "chain",
        type: "string",
        description: "The blockchain chain to query: hedera, polygon, or all",
        required: false,
      },
      {
        name: "tokenAddress",
        type: "string",
        description:
          "Optional token address or symbol to query. Leave empty for all tokens.",
        required: false,
      },
    ],
    renderAndWaitForResponse: ({ args, respond }) => {
      return <BalanceRequirementsForm args={args} respond={respond} />;
    },
  });

  return (
    <div className="h-full">
      <CopilotChat
        className="h-full"
        labels={{
          initial:
            "👋 Hi! I'm your DeFi liquidity assistant.\n\nAsk me to check balances or get liquidity information and I'll coordinate with specialized agents to fetch on-chain data!",
        }}
        instructions="You are a helpful DeFi assistant. Help users query balances and liquidity by coordinating with specialized agents."
      />
    </div>
  );
};

export default function DeFiChat() {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit" showDevConsole={false} agent="a2a_chat">
      <ChatInner />
    </CopilotKit>
  );
}

