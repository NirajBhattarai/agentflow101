"use client";

/**
 * DeFi Chat Component
 *
 * Demonstrates key patterns:
 * - A2A Communication: Visualizes message flow between orchestrator and agents
 * - HITL: Balance requirements form for gathering account information
 * - Multi-Agent: Coordinates balance and liquidity agents via A2A Protocol
 */

import React, { useState, useEffect } from "react";
import { CopilotKit, useCopilotChat, useCopilotReadable } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import { useCopilotAction } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";
import { BalanceRequirementsForm } from "../forms/balance/BalanceRequirementsForm";
import { LiquidityRequirementsForm } from "../forms/liquidity/LiquidityRequirementsForm";
import { SwapRequirementsForm } from "../forms/swap/SwapRequirementsForm";
import { MessageToA2A } from "./a2a/MessageToA2A";
import { MessageFromA2A } from "./a2a/MessageFromA2A";
import type {
  DeFiChatProps,
  BalanceData,
  LiquidityData,
  ParallelLiquidityData,
  SwapData,
  MessageActionRenderProps,
} from "@/types";

const ChatInner = ({
  onBalanceUpdate,
  onLiquidityUpdate,
  onSwapUpdate,
}: DeFiChatProps) => {
  const { visibleMessages } = useCopilotChat();

  // Extract structured data from A2A agent responses
  useEffect(() => {
    const extractDataFromMessages = () => {
      for (const message of visibleMessages) {
        const msg = message as any;

        if (msg.type === "ResultMessage" && msg.actionName === "send_message_to_a2a_agent") {
          try {
            const result = msg.result;
            let parsed;

            if (typeof result === "string") {
              let cleanResult = result;
              if (result.startsWith("A2A Agent Response: ")) {
                cleanResult = result.substring("A2A Agent Response: ".length);
              }
              parsed = JSON.parse(cleanResult);
            } else if (typeof result === "object" && result !== null) {
              parsed = result;
            }

            if (parsed) {
              // Check if it's balance data
              if (parsed.type === "balance" && parsed.balances && Array.isArray(parsed.balances)) {
                onBalanceUpdate?.(parsed as BalanceData);
              }
              // Check if it's liquidity data (regular or parallel)
              else if (parsed.type === "parallel_liquidity" && parsed.token_pair) {
                console.log("💧 Parallel Liquidity Data Received:", {
                  token_pair: parsed.token_pair,
                  chains: parsed.chains,
                  hedera_pairs: parsed.hedera_pairs?.length || 0,
                  polygon_pairs: parsed.polygon_pairs?.length || 0,
                  ethereum_pairs: parsed.chains?.ethereum?.pairs?.length || 0,
                  all_pairs: parsed.all_pairs?.length || 0,
                });
                onLiquidityUpdate?.(parsed as ParallelLiquidityData);
              }
              else if (parsed.type === "liquidity" && parsed.pairs && Array.isArray(parsed.pairs)) {
                onLiquidityUpdate?.(parsed as LiquidityData);
              }
              // Check if it's swap data
              // Swap data can have transaction OR swap_options (or both)
              else if (parsed.type === "swap") {
                // Debug logging to verify swap direction
                console.log("🔄 Swap Data Received:", {
                  token_in_symbol: parsed.token_in_symbol,
                  token_out_symbol: parsed.token_out_symbol,
                  amount_in: parsed.amount_in,
                  chain: parsed.chain,
                });
                onSwapUpdate?.(parsed as SwapData);
              }
            }
          } catch (e) {
            // Silently ignore parsing errors
          }
        }
      }
    };

    extractDataFromMessages();
  }, [visibleMessages, onBalanceUpdate, onLiquidityUpdate, onSwapUpdate]);

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
        description: "Optional token address or symbol to query. Leave empty for all tokens.",
        required: false,
      },
    ],
    renderAndWaitForResponse: ({ args, respond }) => {
      return <BalanceRequirementsForm args={args} respond={respond} />;
    },
  });

  // Register HITL liquidity requirements form (collects chain and token pair info at start)
  useCopilotAction({
    name: "gather_liquidity_requirements",
    description: "Gather liquidity query requirements from the user (chain, optional token pair)",
    parameters: [
      {
        name: "chain",
        type: "string",
        description:
          "The blockchain chain to query: hedera, polygon, or all. May be pre-filled from user message.",
        required: false,
      },
      {
        name: "tokenPair",
        type: "string",
        description:
          "Optional token pair to query (e.g., HBAR/USDC). May be pre-filled from user message.",
        required: false,
      },
    ],
    renderAndWaitForResponse: ({ args, respond }) => {
      return <LiquidityRequirementsForm args={args} respond={respond} />;
    },
  });

  // Register HITL swap requirements form (collects swap details at start)
  useCopilotAction({
    name: "gather_swap_requirements",
    description:
      "Gather swap requirements from the user (account address, chain, token in, token out, amount, slippage tolerance)",
    parameters: [
      {
        name: "accountAddress",
        type: "string",
        description:
          "The account address to swap from (Hedera format: 0.0.123456 or EVM format: 0x...). May be pre-filled from user message.",
        required: false,
      },
      {
        name: "chain",
        type: "string",
        description: "Chain: hedera or polygon. May be pre-filled from user message.",
        required: false,
      },
      {
        name: "tokenInSymbol",
        type: "string",
        description:
          "Token symbol to swap from (e.g., USDC, HBAR, MATIC). May be pre-filled from user message.",
        required: false,
      },
      {
        name: "tokenOutSymbol",
        type: "string",
        description:
          "Token symbol to swap to (e.g., USDC, HBAR, MATIC). May be pre-filled from user message.",
        required: false,
      },
      {
        name: "amountIn",
        type: "string",
        description: "Amount to swap (e.g., 100.0). May be pre-filled from user message.",
        required: false,
      },
      {
        name: "slippageTolerance",
        type: "string",
        description:
          "Slippage tolerance percentage (e.g., 0.5 for 0.5%). May be pre-filled from user message.",
        required: false,
      },
    ],
    renderAndWaitForResponse: ({ args, respond }) => {
      return <SwapRequirementsForm args={args} respond={respond} />;
    },
  });

  // Register A2A message visualizer (renders green/blue communication boxes)
  useCopilotAction({
    name: "send_message_to_a2a_agent",
    description: "Sends a message to an A2A agent",
    available: "frontend",
    parameters: [
      {
        name: "agentName",
        type: "string",
        description: "The name of the A2A agent to send the message to",
      },
      {
        name: "task",
        type: "string",
        description: "The message to send to the A2A agent",
      },
    ],
    render: (actionRenderProps: MessageActionRenderProps) => {
      return (
        <>
          <MessageToA2A {...actionRenderProps} />
          <MessageFromA2A {...actionRenderProps} />
        </>
      );
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

export default function DeFiChat({
  onBalanceUpdate,
  onLiquidityUpdate,
  onSwapUpdate,
}: DeFiChatProps) {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit" showDevConsole={false} agent="a2a_chat">
      <ChatInner
        onBalanceUpdate={onBalanceUpdate}
        onLiquidityUpdate={onLiquidityUpdate}
        onSwapUpdate={onSwapUpdate}
      />
    </CopilotKit>
  );
}
