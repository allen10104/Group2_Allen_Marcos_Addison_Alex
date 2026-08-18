/**
 * Like API functions for interacting with the backend like endpoints.
 */

import { apiClient } from "./client";
import type { LikeSummary } from "../types/like";

export async function getLikeSummary(noticeId: string): Promise<LikeSummary> {
    const response = await apiClient.get<LikeSummary>(`/notice/${noticeId}/likes`);
    return response.data;
}

export async function likeNotice(noticeId: string): Promise<void> {
    await apiClient.post(`/notice/${noticeId}/like`);
}

export async function unlikeNotice(noticeId: string): Promise<void> {
    await apiClient.delete(`/notice/${noticeId}/like`);
}