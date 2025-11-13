import { NextRequest, NextResponse } from "next/server";
import {
  createHederaSigner,
  verify,
  PaymentPayload,
  PaymentRequirements,
} from "@/lib/shared/blockchain/hedera/facilitator";

/**
 * POST /api/facilitator/verify - Verify a payment payload
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { paymentPayload, paymentRequirements } = body as {
      paymentPayload: PaymentPayload;
      paymentRequirements: PaymentRequirements;
    };

    if (!paymentPayload || !paymentRequirements) {
      return NextResponse.json(
        { error: "Missing paymentPayload or paymentRequirements" },
        { status: 400 }
      );
    }

    const HEDERA_ACCOUNT_ID = process.env.HEDERA_FACILITATOR_ACCOUNT_ID;
    const HEDERA_PRIVATE_KEY = process.env.HEDERA_FACILITATOR_PRIVATE_KEY;

    if (!HEDERA_ACCOUNT_ID || !HEDERA_PRIVATE_KEY) {
      return NextResponse.json(
        { error: "Facilitator not configured" },
        { status: 500 }
      );
    }

    // Determine network from payment requirements
    const network = paymentRequirements.network;
    if (!["hedera-testnet", "hedera-mainnet"].includes(network)) {
      return NextResponse.json(
        { error: "Invalid network" },
        { status: 400 }
      );
    }

    // Create signer for the network
    const signer = createHederaSigner(network, HEDERA_PRIVATE_KEY, HEDERA_ACCOUNT_ID);

    // Verify the payment
    const verifyResponse = await verify(signer, paymentPayload, paymentRequirements);

    return NextResponse.json(verifyResponse);
  } catch (error) {
    console.error("Error in POST /api/facilitator/verify:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 }
    );
  }
}

