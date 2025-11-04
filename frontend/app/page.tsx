"use client";

import { CopilotKit } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";
import "./copilot.css";

export default function Home() {
	return (
		<div className="relative flex h-screen overflow-hidden bg-[#DEDEE9] p-2">
			{/* Background blobs (match ui) */}
			<div className="absolute w-[445.84px] h-[445.84px] left-[1040px] top-[11px] rounded-full z-0" style={{ background: "rgba(255, 172, 77, 0.2)", filter: "blur(103.196px)" }} />
			<div className="absolute w-[609.35px] h-[609.35px] left-[1338.97px] top-[624.5px] rounded-full z-0" style={{ background: "#C9C9DA", filter: "blur(103.196px)" }} />
			<div className="absolute w-[609.35px] h-[609.35px] left-[670px] top-[-365px] rounded-full z-0" style={{ background: "#C9C9DA", filter: "blur(103.196px)" }} />
			<div className="absolute w-[609.35px] h-[609.35px] left-[507.87px] top-[702.14px] rounded-full z-0" style={{ background: "#F3F3FC", filter: "blur(103.196px)" }} />
			<div className="absolute w-[445.84px] h-[445.84px] left-[127.91px] top-[331px] rounded-full z-0" style={{ background: "rgba(255, 243, 136, 0.3)", filter: "blur(103.196px)" }} />
			<div className="absolute w-[445.84px] h-[445.84px] left-[-205px] top-[802.72px] rounded-full z-0" style={{ background: "rgba(255, 172, 77, 0.2)", filter: "blur(103.196px)" }} />

			<div className="flex flex-1 overflow-hidden z-10 gap-2">
				{/* Left fixed chat card (450px) */}
				<div className="w-[450px] flex-shrink-0 border-2 border-white bg-white/50 backdrop-blur-md shadow-elevation-lg flex flex-col rounded-lg overflow-hidden">
					<div className="p-6 border-b border-[#DBDBE5]">
						<h1 className="text-2xl font-semibold text-[#010507] mb-1">DeFi Orchestrator</h1>
						<p className="text-sm text-[#57575B] leading-relaxed">
							Multi-Agent A2A: <span className="text-[#1B936F] font-semibold">Orchestrator</span> +
							<span className="text-[#BEC2FF] font-semibold"> Liquidity Tools</span>
						</p>
						<p className="text-xs text-[#838389] mt-1">Orchestrator-mediated A2A Protocol</p>
					</div>
					<div className="flex-1 overflow-hidden">
						<CopilotKit runtimeUrl="/api/copilotkit" showDevConsole={false} agent="a2a_chat">
							<div className="h-full">
								<CopilotChat
									className="h-full"
									labels={{
										initial: "Ask about on-chain liquidity, pools, and cross-chain comparisons.",
										placeholder: "e.g., Get liquidity for HBAR on Hedera",
									}}
								/>
							</div>
						</CopilotKit>
					</div>
				</div>

				{/* Right content area */}
				<div className="flex-1 overflow-y-auto rounded-lg bg-white/30 backdrop-blur-sm">
					<div className="max-w-5xl mx-auto p-8">
						<div className="mb-8">
							<h2 className="text-3xl font-semibold text-[#010507] mb-2">Your DeFi Insights</h2>
							<p className="text-[#57575B]">
								Multi-agent coordination via A2A with orchestrator-driven liquidity discovery and aggregation.
							</p>
						</div>

						{/* Empty state */}
						<div className="flex items-center justify-center h-[400px] bg-white/60 backdrop-blur-md rounded-xl border-2 border-dashed border-[#DBDBE5] shadow-elevation-sm">
							<div className="text-center">
								<div className="text-6xl mb-4">💱</div>
								<h3 className="text-xl font-semibold text-[#010507] mb-2">Start Exploring Liquidity</h3>
								<p className="text-[#57575B] max-w-md">
									Ask the assistant for pools, TVL, reserves and cross-chain comparisons. Results will render here.
								</p>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	);
}
