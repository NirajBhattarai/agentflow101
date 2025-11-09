/**
 * SwapCard UI Helper Functions
 *
 * Centralized utility functions for SwapCard component styling and display
 */

/**
 * Get chain badge color class
 */
export function getChainColor(chain: string | undefined): string {
  if (!chain) {
    return "bg-gradient-to-r from-gray-500 to-gray-600"; // Default color
  }
  const chainLower = chain.toLowerCase();
  if (chainLower === "hedera") {
    return "bg-gradient-to-r from-purple-500 to-indigo-500";
  }
  if (chainLower === "polygon") {
    return "bg-gradient-to-r from-blue-500 to-purple-500";
  }
  return "bg-gradient-to-r from-gray-500 to-gray-600";
}

/**
 * Get status badge color classes
 */
export function getStatusColor(status: string): string {
  const statusLower = status.toLowerCase();
  if (statusLower === "completed") {
    return "bg-green-100 text-green-800 border-green-300";
  }
  if (statusLower === "pending") {
    return "bg-yellow-100 text-yellow-800 border-yellow-300";
  }
  if (statusLower === "failed") {
    return "bg-red-100 text-red-800 border-red-300";
  }
  return "bg-gray-100 text-gray-800 border-gray-300";
}

/**
 * Get DEX icon emoji
 */
export function getDexIcon(dex: string): string {
  const dexLower = dex.toLowerCase();
  if (dexLower.includes("saucer")) return "🍽️";
  if (dexLower.includes("heli")) return "🚁";
  if (dexLower.includes("quick")) return "⚡";
  if (dexLower.includes("uniswap")) return "🦄";
  return "💱";
}
