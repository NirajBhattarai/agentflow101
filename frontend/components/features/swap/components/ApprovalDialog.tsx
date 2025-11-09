import React from "react";
import { SwapData } from "@/types";

interface ApprovalDialogProps {
  data: SwapData;
  swappingState: "idle" | "swapping" | "done";
  onConfirm: () => void;
  onCancel: () => void;
}

export const ApprovalDialog: React.FC<ApprovalDialogProps> = ({
  data,
  swappingState,
  onConfirm,
  onCancel,
}) => {
  const { transaction, swap_options } = data;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4 shadow-2xl border-2 border-green-200">
        <h3 className="text-xl font-bold text-[#010507] mb-4">Confirm Swap</h3>
        <div className="space-y-3 mb-6">
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-sm text-[#57575B] mb-1">You are swapping</div>
            <div className="text-lg font-bold text-[#010507]">
              {data.amount_in} {data.token_in_symbol} → {data.token_out_symbol}
            </div>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-sm text-[#57575B] mb-1">You will receive (estimated)</div>
            <div className="text-lg font-bold text-green-600">
              {swap_options?.[0]?.amount_out || transaction?.amount_out || "—"}{" "}
              {data.token_out_symbol}
            </div>
          </div>
          {transaction?.swap_fee && (
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="text-sm text-[#57575B] mb-1">Swap Fee</div>
              <div className="text-lg font-bold text-[#010507]">{transaction.swap_fee}</div>
            </div>
          )}
        </div>
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-3 rounded-lg font-semibold text-sm bg-gray-200 text-gray-700 hover:bg-gray-300 transition-all"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={swappingState === "swapping"}
            className={`flex-1 px-4 py-3 rounded-lg font-semibold text-sm transition-all ${
              swappingState === "swapping"
                ? "bg-yellow-500 text-white cursor-not-allowed"
                : "bg-green-600 hover:bg-green-700 text-white shadow-md hover:shadow-lg"
            }`}
          >
            {swappingState === "swapping" ? (
              <span className="flex items-center justify-center gap-2">
                <span className="animate-spin">⏳</span>
                Processing...
              </span>
            ) : (
              "Confirm Swap"
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
