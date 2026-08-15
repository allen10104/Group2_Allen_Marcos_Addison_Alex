/**
 * Notice API functions for interacting with the backend notice endpoints.
 */

import { apiClient } from "./client";
import type { Notice, NoticeCreatePayload, NoticeUpdatePayload } from "../types/notice";

export async function getNotices(): Promise<Notice[]> {
    const response = await apiClient.get<Notice[]>("/notices");
    return response.data;
}

export async function getNoticeById(noticeId: string): Promise<Notice> {
    const response = await apiClient.get<Notice>(`/notices/${noticeId}`);
    return response.data;
}

export async function createNotice(payload: NoticeCreatePayload): Promise<Notice> {
    const response = await apiClient.post<Notice>("/notices", payload);
    return response.data;
}

export async function updateNotice(noticeId: string, payload: NoticeUpdatePayload): Promise<Notice> {
    const response = await apiClient.put<Notice>(`/notices/${noticeId}`, payload);
    return response.data;
}

export async function deleteNotice(noticeId: string): Promise<void> {
    await apiClient.delete(`/notices/${noticeId}`);
}