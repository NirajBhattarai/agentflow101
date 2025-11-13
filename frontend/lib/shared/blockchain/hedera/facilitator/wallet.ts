/**
 * Hedera Wallet Utilities
 * 
 * Utilities for creating and managing Hedera signers and clients
 */

import { AccountId, Client, PrivateKey } from "@hashgraph/sdk";

/**
 * Represents a Hedera signer with all necessary components for transaction signing.
 */
export type HederaSigner = {
  client: Client;
  accountId: AccountId;
  privateKey: PrivateKey;
};

/**
 * Creates a Hedera client connected to the specified network.
 */
export function createHederaConnectedClient(network: string): Client {
  if (network === "hedera-testnet") {
    return Client.forTestnet();
  } else if (network === "hedera-mainnet") {
    return Client.forMainnet();
  } else {
    throw new Error(`Unsupported Hedera network: ${network}`);
  }
}

/**
 * Creates a Hedera signer from private key string.
 */
export function createHederaSigner(
  network: string,
  privateKeyString: string,
  accountId: string
): HederaSigner {
  const client = createHederaConnectedClient(network);
  const privateKey = PrivateKey.fromStringECDSA(privateKeyString);
  const hederaAccountId = AccountId.fromString(accountId);

  client.setOperator(hederaAccountId, privateKey);

  return {
    client,
    accountId: hederaAccountId,
    privateKey
  };
}

/**
 * Checks if the given object is a valid Hedera signer.
 */
export function isHederaSigner(wallet: any): wallet is HederaSigner {
  return wallet != null &&
    typeof wallet.client !== 'undefined' &&
    typeof wallet.accountId !== 'undefined' &&
    typeof wallet.privateKey !== 'undefined';
}

