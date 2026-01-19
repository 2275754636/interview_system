import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AdminState {
  token: string;
  setToken: (token: string) => void;
  clearToken: () => void;
}

export const useAdminStore = create<AdminState>()(
  persist(
    (set) => ({
      token: '',
      setToken: (token) => set({ token: token.trim() }),
      clearToken: () => set({ token: '' }),
    }),
    { name: 'admin-storage' }
  )
);

