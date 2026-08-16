/**
 * User API functions for interacting with the backend user/follow endpoints.
 */

import { apiClient } from "./client";
import type { User } from "../types/auth";

export async function getUsers(search?: string): Promise<User[]> {
    const response = await apiClient.get<User[]>("/users", {
        params: search ? { search } : undefined,
    });
    return response.data;
}

export async function getFollowing(userId: string): Promise<User[]> {
    const response = await apiClient.get<User[]>(`/users/${userId}/following`);
    return response.data;
}

export async function getFollowers(userId: string): Promise<User[]> {
    const response = await apiClient.get<User[]>(`/users/${userId}/followers`);
    return response.data;
}

export async function followUser(userId: string): Promise<void> {
    await apiClient.post(`/users/${userId}/follow`);
}

export async function unfollowUser(userId: string): Promise<void> {
    await apiClient.delete(`/users/${userId}/unfollow`);
}