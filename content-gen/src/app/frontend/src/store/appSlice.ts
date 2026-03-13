/**
 * App slice — application-level state (user info, config, feature flags, UI toggles).
 * createSlice + createAsyncThunk replaces manual dispatch + string constants.
 * Granular selectors — each component subscribes only to the state it needs.
 */
import { createSlice, createAsyncThunk, type PayloadAction } from '@reduxjs/toolkit';

/* ------------------------------------------------------------------ */
/*  Generation-status enum                                             */
/* ------------------------------------------------------------------ */

/**
 * Finite set of generation-status values.  Components that read
 * `generationStatus` can compare against these constants instead of
 * relying on magic strings.
 *
 * `IDLE` means "no status to display".  Every other member maps to a
 * user-facing label via {@link GENERATION_STATUS_LABELS}.
 */
export enum GenerationStatus {
  IDLE = '',
  UPDATING_BRIEF = 'UPDATING_BRIEF',
  PROCESSING_QUESTION = 'PROCESSING_QUESTION',
  FINDING_PRODUCTS = 'FINDING_PRODUCTS',
  REGENERATING_IMAGE = 'REGENERATING_IMAGE',
  PROCESSING_REQUEST = 'PROCESSING_REQUEST',
  ANALYZING_BRIEF = 'ANALYZING_BRIEF',
  STARTING_GENERATION = 'STARTING_GENERATION',
  PROCESSING_RESULTS = 'PROCESSING_RESULTS',
  /** Used for heartbeat polling where the label is dynamic. */
  POLLING = 'POLLING',
}

/** Display strings shown in the UI for each status. */
const GENERATION_STATUS_LABELS: Record<GenerationStatus, string> = {
  [GenerationStatus.IDLE]: '',
  [GenerationStatus.UPDATING_BRIEF]: 'Updating creative brief...',
  [GenerationStatus.PROCESSING_QUESTION]: 'Processing your question...',
  [GenerationStatus.FINDING_PRODUCTS]: 'Finding products...',
  [GenerationStatus.REGENERATING_IMAGE]: 'Regenerating image with your changes...',
  [GenerationStatus.PROCESSING_REQUEST]: 'Processing your request...',
  [GenerationStatus.ANALYZING_BRIEF]: 'Analyzing creative brief...',
  [GenerationStatus.STARTING_GENERATION]: 'Starting content generation...',
  [GenerationStatus.PROCESSING_RESULTS]: 'Processing results...',
  [GenerationStatus.POLLING]: 'Generating content...',
};

/* ------------------------------------------------------------------ */
/*  Async Thunks                                                      */
/* ------------------------------------------------------------------ */

export const fetchAppConfig = createAsyncThunk(
  'app/fetchAppConfig',
  async () => {
    const { getAppConfig } = await import('../api');
    const config = await getAppConfig();
    return config;
  },
);

export const fetchUserInfo = createAsyncThunk(
  'app/fetchUserInfo',
  async () => {
    const { platformClient } = await import('../api/httpClient');
    const response = await platformClient.raw('/.auth/me');
    if (!response.ok) return { userId: 'anonymous', userName: '' };

    const payload = await response.json();
    const claims: { typ: string; val: string }[] = payload[0]?.user_claims || [];

    const objectId = claims.find(
      (c) => c.typ === 'http://schemas.microsoft.com/identity/claims/objectidentifier',
    )?.val || 'anonymous';

    const name = claims.find((c) => c.typ === 'name')?.val || '';

    return { userId: objectId, userName: name };
  },
);

/* ------------------------------------------------------------------ */
/*  Slice                                                             */
/* ------------------------------------------------------------------ */

interface AppState {
  userId: string;
  userName: string;
  isLoading: boolean;
  imageGenerationEnabled: boolean;
  showChatHistory: boolean;
  /** Current generation status enum value. */
  generationStatus: GenerationStatus;
  /** Dynamic label override (used with GenerationStatus.POLLING). */
  generationStatusLabel: string;
}

const initialState: AppState = {
  userId: '',
  userName: '',
  isLoading: false,
  imageGenerationEnabled: true,
  showChatHistory: true,
  generationStatus: GenerationStatus.IDLE,
  generationStatusLabel: '',
};

const appSlice = createSlice({
  name: 'app',
  initialState,
  reducers: {
    setIsLoading(state, action: PayloadAction<boolean>) {
      state.isLoading = action.payload;
    },
    setGenerationStatus(
      state,
      action: PayloadAction<GenerationStatus | { status: GenerationStatus; label: string }>,
    ) {
      if (typeof action.payload === 'string') {
        state.generationStatus = action.payload;
        state.generationStatusLabel = GENERATION_STATUS_LABELS[action.payload];
      } else {
        state.generationStatus = action.payload.status;
        state.generationStatusLabel = action.payload.label;
      }
    },
    toggleChatHistory(state) {
      state.showChatHistory = !state.showChatHistory;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchAppConfig.fulfilled, (state, action) => {
        state.imageGenerationEnabled = action.payload.enable_image_generation;
      })
      .addCase(fetchAppConfig.rejected, (state) => {
        state.imageGenerationEnabled = true; // default when fetch fails
      })
      .addCase(fetchUserInfo.fulfilled, (state, action) => {
        state.userId = action.payload.userId;
        state.userName = action.payload.userName;
      })
      .addCase(fetchUserInfo.rejected, (state) => {
        state.userId = 'anonymous';
        state.userName = '';
      });
  },
});

export const { setIsLoading, setGenerationStatus, toggleChatHistory } =
  appSlice.actions;
export default appSlice.reducer;
