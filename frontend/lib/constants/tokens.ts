/**
 * Token lists and configurations for all chains
 *
 * Centralized token definitions used across the application
 */

export interface Token {
  symbol: string;
  name: string;
  chain?: string;
  address?: string;
  type?: "native" | "token";
}

// Hedera tokens
export const HEDERA_TOKENS: Token[] = [
  { symbol: "HBAR", name: "Hedera Hashgraph", chain: "hedera", type: "native" },
  { symbol: "USDC", name: "USD Coin", chain: "hedera", type: "token" },
  { symbol: "USDT", name: "Tether USD", chain: "hedera", type: "token" },
  { symbol: "WHBAR", name: "Wrapped HBAR", chain: "hedera", type: "token" },
  { symbol: "ETH", name: "Wrapped Ethereum", chain: "hedera", type: "token" },
  { symbol: "WETH", name: "Wrapped ETH", chain: "hedera", type: "token" },
  { symbol: "BTC", name: "Wrapped Bitcoin", chain: "hedera", type: "token" },
  { symbol: "SAUCE", name: "SaucerSwap Token", chain: "hedera", type: "token" },
  { symbol: "LINK", name: "Chainlink", chain: "hedera", type: "token" },
  { symbol: "AVAX", name: "Avalanche", chain: "hedera", type: "token" },
];

// Polygon tokens
export const POLYGON_TOKENS: Token[] = [
  { symbol: "MATIC", name: "Polygon", chain: "polygon", type: "native" },
  { symbol: "USDC", name: "USD Coin", chain: "polygon", type: "token" },
  { symbol: "USDT", name: "Tether USD", chain: "polygon", type: "token" },
  { symbol: "WMATIC", name: "Wrapped MATIC", chain: "polygon", type: "token" },
  { symbol: "DAI", name: "Dai Stablecoin", chain: "polygon", type: "token" },
  { symbol: "ETH", name: "Wrapped Ethereum", chain: "polygon", type: "token" },
  { symbol: "WBTC", name: "Wrapped Bitcoin", chain: "polygon", type: "token" },
  { symbol: "WETH", name: "Wrapped ETH", chain: "polygon", type: "token" },
  { symbol: "LINK", name: "Chainlink", chain: "polygon", type: "token" },
  { symbol: "AAVE", name: "Aave Token", chain: "polygon", type: "token" },
  { symbol: "UNI", name: "Uniswap", chain: "polygon", type: "token" },
  { symbol: "CRV", name: "Curve DAO Token", chain: "polygon", type: "token" },
];

// All tokens combined
export const ALL_TOKENS: Token[] = [...HEDERA_TOKENS, ...POLYGON_TOKENS];

// Bridgeable tokens (tokens that can be bridged)
// Note: EtaBridge only supports USDC for bridging between Hedera and Polygon
export const BRIDGEABLE_TOKENS: Token[] = [{ symbol: "USDC", name: "USD Coin" }];

// Standard token pairs for liquidity queries
export const STANDARD_PAIRS = [
  "HBAR/USDC",
  "HBAR/USDT",
  "MATIC/USDC",
  "MATIC/USDT",
  "ETH/USDC",
  "ETH/USDT",
  "WBTC/USDC",
  "USDC/USDT",
  "DAI/USDC",
  "AAVE/USDC",
  "UNI/USDC",
  "LINK/USDC",
  "HBAR/MATIC",
  "ETH/MATIC",
];

// Balance form tokens (with addresses)
export const BALANCE_TOKENS: Token[] = [
  { symbol: "HBAR", name: "Hedera Hashgraph", address: "0.0.0", type: "native" },
  {
    symbol: "MATIC",
    name: "Polygon",
    address: "0x0000000000000000000000000000000000000000",
    type: "native",
  },
  {
    symbol: "USDC",
    name: "USD Coin",
    address: "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    type: "token",
  },
  {
    symbol: "USDT",
    name: "Tether USD",
    address: "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
    type: "token",
  },
  {
    symbol: "ETH",
    name: "Ethereum",
    address: "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
    type: "token",
  },
  {
    symbol: "WBTC",
    name: "Wrapped Bitcoin",
    address: "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
    type: "token",
  },
  {
    symbol: "DAI",
    name: "Dai Stablecoin",
    address: "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
    type: "token",
  },
  {
    symbol: "AAVE",
    name: "Aave Token",
    address: "0xD6DF932A45C0f255f85145f286eA0b292B21C90B",
    type: "token",
  },
  {
    symbol: "UNI",
    name: "Uniswap",
    address: "0xb33EaAd8d922B1083446DC23f610c2567fB5180f",
    type: "token",
  },
  {
    symbol: "LINK",
    name: "Chainlink",
    address: "0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39",
    type: "token",
  },
];

/**
 * Get tokens for a specific chain
 */
export function getTokensForChain(chain: string): Token[] {
  if (chain === "hedera") return HEDERA_TOKENS;
  if (chain === "polygon") return POLYGON_TOKENS;
  return ALL_TOKENS;
}

/**
 * Get token by symbol and chain
 */
export function getToken(symbol: string, chain?: string): Token | undefined {
  const tokens = chain ? getTokensForChain(chain) : ALL_TOKENS;
  return tokens.find((t) => t.symbol.toUpperCase() === symbol.toUpperCase());
}
