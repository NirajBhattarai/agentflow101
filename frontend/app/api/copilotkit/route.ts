import { NextRequest } from "next/server";
import {
	CopilotRuntime,
	ExperimentalEmptyAdapter,
	copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";
import { A2AMiddlewareAgent } from "@ag-ui/a2a-middleware";

export async function POST(request: NextRequest) {
	// Orchestrator speaking AG-UI protocol
	const orchestratorUrl = process.env.ORCHESTRATOR_URL || "http://localhost:9000";

	// Wrap orchestrator
	const orchestrationAgent = new HttpAgent({ url: orchestratorUrl });

	// A2A middleware: for now, no downstream A2A agents registered; just the orchestrator bridge
	const a2aMiddlewareAgent = new A2AMiddlewareAgent({
		description: "DeFi liquidity orchestrator with future chain-specific agents (Hedera, Ethereum, Polygon, BSC)",
		agentUrls: [
			// Future: register chain-specific agents here
		],
		orchestrationAgent,
		instructions: `
		  You are a DeFi liquidity orchestrator that coordinates specialized liquidity agents/tools to fetch and aggregate on-chain liquidity information across chains (Hedera, Ethereum, Polygon, BSC). Use tools one at a time, wait for results, and return concise summaries plus structured JSON for pools, tokens, TVL, reserves, and fees.
		`,
	});

	const runtime = new CopilotRuntime({
		agents: { a2a_chat: a2aMiddlewareAgent },
	});

	const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
		runtime,
		serviceAdapter: new ExperimentalEmptyAdapter(),
		endpoint: "/api/copilotkit",
	});

	return handleRequest(request);
}
