import { configureStore } from "@reduxjs/toolkit";
import swapReducer from "./slices/swapSlice";
import bridgeReducer from "./slices/bridgeSlice";

export const store = configureStore({
  reducer: {
    swap: swapReducer,
    bridge: bridgeReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
