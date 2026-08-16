/**
 * Auth API functions for interacting with the backend authentication endpoints.
 */

import { apiClient } from "./client";
import type { AuthResponse, LoginCredentials, RegisterCredentials } from "../types/auth";

export async function loginRequest(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>("/auth/login", credentials);
    return response.data;
}

export async function registerRequest(credentials: RegisterCredentials): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>("/auth/register", credentials);
    return response.data;
}