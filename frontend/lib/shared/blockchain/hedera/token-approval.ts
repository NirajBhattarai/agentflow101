/**
 * Token approval utilities for Hedera (HTS tokens)
 *
 * Hedera-specific token approval logic
 */

import { ethers } from "ethers";

// ERC20 ABI for approval operations
const ERC20_APPROVAL_ABI = [
  "function approve(address spender, uint256 amount) external returns (bool)",
  "function allowance(address owner, address spender) external view returns (uint256)",
  "function decimals() view returns (uint8)",
];

/**
 * Get token decimals
 */
export async function getTokenDecimals(
  provider: ethers.Provider,
  tokenAddress: string,
): Promise<number> {
  try {
    const tokenContract = new ethers.Contract(tokenAddress, ERC20_APPROVAL_ABI, provider);
    const decimals = await tokenContract.decimals();
    return Number(decimals);
  } catch (error: any) {
    console.warn(`Could not fetch token decimals, using default 18: ${error.message}`);
    return 18; // Default to 18 decimals
  }
}

/**
 * Check if token approval is needed and sufficient
 */
export async function checkTokenApproval(
  provider: ethers.Provider,
  tokenAddress: string,
  owner: string,
  spender: string,
  amount: bigint,
): Promise<{
  needsApproval: boolean;
  currentAllowance: bigint;
  sufficient: boolean;
}> {
  try {
    const tokenContract = new ethers.Contract(tokenAddress, ERC20_APPROVAL_ABI, provider);
    const currentAllowance = await tokenContract.allowance(owner, spender);
    const needsApproval = currentAllowance < amount;

    return {
      needsApproval,
      currentAllowance: BigInt(currentAllowance.toString()),
      sufficient: !needsApproval,
    };
  } catch (error: any) {
    console.error(`Error checking token approval: ${error.message}`);
    return {
      needsApproval: true,
      currentAllowance: BigInt(0),
      sufficient: false,
    };
  }
}

/**
 * Approve token spending for Hedera
 * Uses fixed gas limit (7M) and no gasPrice
 */
export async function approveToken(
  signer: ethers.Signer,
  tokenAddress: string,
  spender: string,
  amount: bigint,
): Promise<ethers.TransactionResponse> {
  const tokenContract = new ethers.Contract(tokenAddress, ERC20_APPROVAL_ABI, signer);

  // Use the actual amount provided (add 10% buffer for safety)
  const bufferMultiplier = BigInt(110); // 110% = 10% buffer
  const bufferDivisor = BigInt(100);
  const approvalAmount = (amount * bufferMultiplier) / bufferDivisor;

  console.log(`   Approving token ${tokenAddress} for spender ${spender}`);
  console.log(`   Swap amount: ${amount.toString()}`);
  console.log(`   Approval amount (with 10% buffer): ${approvalAmount.toString()}`);

  // Hedera: use fixed gas limit, don't estimate, no gasPrice
  const overrides: ethers.Overrides = {
    gasLimit: 7_000_000, // Max gas for Hedera
  };

  const tx = await tokenContract.approve(spender, approvalAmount, overrides);
  return tx;
}

/**
 * Check and approve token if needed for Hedera
 */
export async function ensureTokenApproval(
  provider: ethers.Provider,
  signer: ethers.Signer,
  tokenAddress: string,
  owner: string,
  spender: string,
  amount: bigint,
): Promise<boolean> {
  let needsApproval = true;
  let currentAllowance = BigInt(0);
  let decimals = 18;

  try {
    const approvalCheck = await checkTokenApproval(provider, tokenAddress, owner, spender, amount);
    needsApproval = approvalCheck.needsApproval;
    currentAllowance = approvalCheck.currentAllowance;
    decimals = await getTokenDecimals(provider, tokenAddress);
  } catch (error: any) {
    console.warn(`   Could not check approval status: ${error.message}`);
  }

  if (!needsApproval) {
    console.log(`   ✅ Token already approved: ${ethers.formatUnits(currentAllowance, decimals)}`);
    return true;
  }

  console.log(`   ⚠️  Token approval needed`);
  if (currentAllowance > 0) {
    console.log(`      Current allowance: ${ethers.formatUnits(currentAllowance, decimals)}`);
  }
  console.log(`      Required: ${ethers.formatUnits(amount, decimals)}`);

  try {
    const approveTx = await approveToken(signer, tokenAddress, spender, amount);
    console.log(`   🔄 Approval transaction sent: ${approveTx.hash}`);

    const receipt = await approveTx.wait();

    if (!receipt || receipt.status !== 1) {
      throw new Error(`Token approval failed with status: ${receipt?.status}`);
    }

    console.log(`   ✅ Token approval confirmed`);
    return true;
  } catch (error: any) {
    console.error(`   ⚠️  Token approval failed: ${error.message}`);
    console.log(`   ℹ️  Hedera tokens may use different approval mechanism`);
    console.log(`   ℹ️  Continuing with swap - contract will handle approval requirement`);
    return false; // Return false but don't throw for Hedera
  }
}
