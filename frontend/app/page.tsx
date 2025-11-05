"use client";

import { useState } from "react";
import DeFiChat from "@/components/defi-chat";
import { BalanceCard } from "@/components/BalanceCard";
import { BridgeCard } from "@/components/BridgeCard";
import type { BalanceData, LiquidityData, BridgeData } from "@/components/types";
import "./copilot.css";

export default function Home() {
  const [balanceData, setBalanceData] = useState<BalanceData | null>(null);
  const [liquidityData, setLiquidityData] = useState<LiquidityData | null>(null);
  const [bridgeData, setBridgeData] = useState<BridgeData | null>(null);

  return (
    <div className="relative flex h-screen overflow-hidden bg-[#DEDEE9] p-2">
      {/* Background blobs (match ui) */}
      <div
        className="absolute w-[445.84px] h-[445.84px] left-[1040px] top-[11px] rounded-full z-0"
        style={{ background: "rgba(255, 172, 77, 0.2)", filter: "blur(103.196px)" }}
      />
      <div
        className="absolute w-[609.35px] h-[609.35px] left-[1338.97px] top-[624.5px] rounded-full z-0"
        style={{ background: "#C9C9DA", filter: "blur(103.196px)" }}
      />
      <div
        className="absolute w-[609.35px] h-[609.35px] left-[670px] top-[-365px] rounded-full z-0"
        style={{ background: "#C9C9DA", filter: "blur(103.196px)" }}
      />
      <div
        className="absolute w-[609.35px] h-[609.35px] left-[507.87px] top-[702.14px] rounded-full z-0"
        style={{ background: "#F3F3FC", filter: "blur(103.196px)" }}
      />
      <div
        className="absolute w-[445.84px] h-[445.84px] left-[127.91px] top-[331px] rounded-full z-0"
        style={{ background: "rgba(255, 243, 136, 0.3)", filter: "blur(103.196px)" }}
      />
      <div
        className="absolute w-[445.84px] h-[445.84px] left-[-205px] top-[802.72px] rounded-full z-0"
        style={{ background: "rgba(255, 172, 77, 0.2)", filter: "blur(103.196px)" }}
      />

      <div className="flex flex-1 overflow-hidden z-10 gap-2">
        {/* Left fixed chat card (450px) */}
        <div className="w-[450px] flex-shrink-0 border-2 border-white bg-white/50 backdrop-blur-md shadow-elevation-lg flex flex-col rounded-lg overflow-hidden">
          <div className="p-6 border-b border-[#DBDBE5]">
            <h1 className="text-2xl font-semibold text-[#010507] mb-1">DeFi Assistant</h1>
            <p className="text-sm text-[#57575B] leading-relaxed">
              Multi-Agent A2A Demo:{" "}
              <span className="text-purple-600 font-semibold">Balance</span> +{" "}
              <span className="text-teal-600 font-semibold">Liquidity</span> +{" "}
              <span className="text-orange-600 font-semibold">Bridge</span>
            </p>
            <p className="text-xs text-[#838389] mt-1">Orchestrator-mediated A2A Protocol</p>
          </div>
          <div className="flex-1 overflow-hidden">
            <DeFiChat
              onBalanceUpdate={setBalanceData}
              onLiquidityUpdate={setLiquidityData}
              onBridgeUpdate={setBridgeData}
            />
          </div>
        </div>

        {/* Right content area */}
        <div className="flex-1 overflow-y-auto rounded-lg bg-white/30 backdrop-blur-sm">
          <div className="max-w-5xl mx-auto p-8">
            <div className="mb-8">
              <h2 className="text-3xl font-semibold text-[#010507] mb-2">Your DeFi Data</h2>
              <p className="text-[#57575B]">
                Multi-agent coordination: Balance, Liquidity, and Bridge agents with A2A Protocol
              </p>
            </div>

            {!balanceData && !liquidityData && !bridgeData && (
              <div className="flex items-center justify-center h-[400px] bg-white/60 backdrop-blur-md rounded-xl border-2 border-dashed border-[#DBDBE5] shadow-elevation-sm">
                <div className="text-center">
                  <div className="text-6xl mb-4">💰</div>
                  <h3 className="text-xl font-semibold text-[#010507] mb-2">
                    Start Querying Your DeFi Data
                  </h3>
                  <p className="text-[#57575B] max-w-md">
                    Ask the assistant to check your balance or get liquidity information. 
                    Watch as specialized agents collaborate through A2A Protocol to fetch your on-chain data.
                  </p>
                </div>
              </div>
            )}

            {balanceData && (
              <div className="mb-4">
                <BalanceCard data={balanceData} />
              </div>
            )}

            {liquidityData && (
              <div className="mb-4">
                <div className="bg-white/60 backdrop-blur-md rounded-xl p-6 border-2 border-[#DBDBE5] shadow-elevation-md">
                  <h3 className="text-xl font-semibold text-[#010507] mb-4">Liquidity Data</h3>
                  <pre className="text-xs bg-gray-50 p-4 rounded overflow-auto">
                    {JSON.stringify(liquidityData, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {bridgeData && (
              <div className="mb-4">
                <BridgeCard 
                  data={bridgeData}
                  onBridgeInitiate={(protocol) => {
                    // When user clicks "Bridge" button, send a message to the chat
                    // to trigger the orchestrator to initiate the bridge
                    console.log("Initiating bridge with protocol:", protocol);
                    // The orchestrator will handle this via chat message
                    // In a real implementation, you might want to send a message programmatically
                    // For now, the user can click the button and the UI will show the state
                    // The actual bridge initiation happens via orchestrator when user says "do with [protocol]"
                  }}
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
