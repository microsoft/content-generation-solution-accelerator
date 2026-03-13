/**
 * Typed Redux hooks for type-safe store access throughout the app.
 * Use useAppDispatch and useAppSelector instead of raw useDispatch/useSelector.
 */
import { useDispatch, useSelector } from 'react-redux';
import type { RootState, AppDispatch } from './store';

export const useAppDispatch = useDispatch.withTypes<AppDispatch>();
export const useAppSelector = useSelector.withTypes<RootState>();
