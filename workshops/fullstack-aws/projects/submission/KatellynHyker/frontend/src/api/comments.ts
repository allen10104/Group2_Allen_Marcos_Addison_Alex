/**
 * Comment API functions for interacting with the backend comment endpoints.
 */

import { apiClient } from "./client";
import type { Comment, CommentCreatePayload, CommentUpdatePayload } from "../types/comment";

export async function getComments(noticeId: string): Promise<Comment[]> {
    const response = await apiClient.get<Comment[]>(`/notice/${noticeId}/comments`);
    return response.data;
}

export async function createComment(noticeId: string, payload: CommentCreatePayload): Promise<Comment> {
    const response = await apiClient.post<Comment>(`/notice/${noticeId}/comments`, payload);
    return response.data;
}

export async function updateComment(commentId: string, payload: CommentUpdatePayload): Promise<Comment> {
    const response = await apiClient.put<Comment>(`/comments/${commentId}`, payload);
    return response.data;
}

export async function deleteComment(commentId: string): Promise<void> {
    await apiClient.delete(`/comments/${commentId}`);
}