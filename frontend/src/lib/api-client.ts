"use client";

import { useAuth } from "@clerk/nextjs";
import { useCallback } from "react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ApiError {
  code: string;
  message: string;
  details?: unknown[];
}

interface ApiResponse<T> {
  data: T;
  meta?: { cursor?: string; has_more?: boolean };
}

export function useApiFetch() {
  const { getToken } = useAuth();

  const apiFetch = useCallback(
    async <T>(path: string, options: RequestInit = {}): Promise<ApiResponse<T>> => {
      const token = await getToken();

      const response = await fetch(`${API_BASE_URL}/api/v1${path}`, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
          "X-Request-Id": crypto.randomUUID(),
          ...options.headers,
        },
      });

      if (!response.ok) {
        const errorBody = await response.json();
        throw errorBody.error as ApiError;
      }

      return response.json();
    },
    [getToken],
  );

  return { apiFetch };
}
