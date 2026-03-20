/**
 * Content slice — creative brief, product selection, generated content.
 * Typed createSlice with granular selectors.
 */
import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import type { CreativeBrief, Product, GeneratedContent } from '../types';

interface ContentState {
  pendingBrief: CreativeBrief | null;
  confirmedBrief: CreativeBrief | null;
  selectedProducts: Product[];
  availableProducts: Product[];
  generatedContent: GeneratedContent | null;
}

const initialState: ContentState = {
  pendingBrief: null,
  confirmedBrief: null,
  selectedProducts: [],
  availableProducts: [],
  generatedContent: null,
};

const contentSlice = createSlice({
  name: 'content',
  initialState,
  reducers: {
    setPendingBrief(state, action: PayloadAction<CreativeBrief | null>) {
      state.pendingBrief = action.payload;
    },
    setConfirmedBrief(state, action: PayloadAction<CreativeBrief | null>) {
      state.confirmedBrief = action.payload;
    },
    setSelectedProducts(state, action: PayloadAction<Product[]>) {
      state.selectedProducts = action.payload;
    },
    setAvailableProducts(state, action: PayloadAction<Product[]>) {
      state.availableProducts = action.payload;
    },
    setGeneratedContent(state, action: PayloadAction<GeneratedContent | null>) {
      state.generatedContent = action.payload;
    },
    resetContent(state) {
      state.pendingBrief = null;
      state.confirmedBrief = null;
      state.selectedProducts = [];
      state.availableProducts = [];
      state.generatedContent = null;
    },
  },
});

export const {
  setPendingBrief,
  setConfirmedBrief,
  setSelectedProducts,
  setAvailableProducts,
  setGeneratedContent,
  resetContent,
} = contentSlice.actions;
export default contentSlice.reducer;
