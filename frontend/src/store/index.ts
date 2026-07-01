import { configureStore } from '@reduxjs/toolkit';

// Simple store definition to support state access
export const store = configureStore({
  reducer: {
    // We keep state simple as API data is driven by local components state
    app: (state = { loaded: true }) => state
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
