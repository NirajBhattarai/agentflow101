import { createSlice, PayloadAction } from "@reduxjs/toolkit";

export interface ApprovalStatus {
  tokenAddress: string;
  tokenSymbol: string;
  spender: string;
  amount: string;
  status: "idle" | "checking" | "needs_approval" | "approving" | "approved" | "error";
  error?: string;
}

export interface SwapState {
  approvalStatus: ApprovalStatus | null;
  isSwapping: boolean;
  swapError: string | null;
  txHash: string | null;
}

const initialState: SwapState = {
  approvalStatus: null,
  isSwapping: false,
  swapError: null,
  txHash: null,
};

const swapSlice = createSlice({
  name: "swap",
  initialState,
  reducers: {
    setApprovalStatus: (state, action: PayloadAction<ApprovalStatus | null>) => {
      state.approvalStatus = action.payload;
    },
    setApprovalStatusField: (state, action: PayloadAction<Partial<ApprovalStatus>>) => {
      if (state.approvalStatus) {
        state.approvalStatus = { ...state.approvalStatus, ...action.payload };
      }
    },
    setSwapping: (state, action: PayloadAction<boolean>) => {
      state.isSwapping = action.payload;
    },
    setSwapError: (state, action: PayloadAction<string | null>) => {
      state.swapError = action.payload;
    },
    setTxHash: (state, action: PayloadAction<string | null>) => {
      state.txHash = action.payload;
    },
    resetSwapState: (state) => {
      state.approvalStatus = null;
      state.isSwapping = false;
      state.swapError = null;
      state.txHash = null;
    },
  },
});

export const {
  setApprovalStatus,
  setApprovalStatusField,
  setSwapping,
  setSwapError,
  setTxHash,
  resetSwapState,
} = swapSlice.actions;

export default swapSlice.reducer;
