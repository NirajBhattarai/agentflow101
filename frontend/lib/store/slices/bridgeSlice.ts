import { createSlice, PayloadAction } from "@reduxjs/toolkit";

export interface ApprovalStatus {
  tokenAddress: string;
  tokenSymbol: string;
  spender: string;
  amount: string;
  status: "idle" | "checking" | "needs_approval" | "approving" | "approved" | "error";
  error?: string;
}

export interface BridgeState {
  approvalStatus: ApprovalStatus | null;
  isBridging: boolean;
  bridgeError: string | null;
  txHash: string | null;
}

const initialState: BridgeState = {
  approvalStatus: null,
  isBridging: false,
  bridgeError: null,
  txHash: null,
};

const bridgeSlice = createSlice({
  name: "bridge",
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
    setBridging: (state, action: PayloadAction<boolean>) => {
      state.isBridging = action.payload;
    },
    setBridgeError: (state, action: PayloadAction<string | null>) => {
      state.bridgeError = action.payload;
    },
    setTxHash: (state, action: PayloadAction<string | null>) => {
      state.txHash = action.payload;
    },
    resetBridgeState: (state) => {
      state.approvalStatus = null;
      state.isBridging = false;
      state.bridgeError = null;
      state.txHash = null;
    },
  },
});

export const {
  setApprovalStatus,
  setApprovalStatusField,
  setBridging,
  setBridgeError,
  setTxHash,
  resetBridgeState,
} = bridgeSlice.actions;

export default bridgeSlice.reducer;
