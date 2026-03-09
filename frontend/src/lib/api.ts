import { auth } from "@clerk/nextjs/server";

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

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<ApiResponse<T>> {
  const { getToken } = await auth();
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
}
