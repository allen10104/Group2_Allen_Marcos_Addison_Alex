/**
 * Shared types for notice-related data structures.
 */

export type Notice = {
    notice_id: string;
    title: string;
    content: string;
    created_at: string;
    updated_at: string;
    user_id: string;
};

export type NoticeCreatePayload = {
    title: string;
    content: string;
};

export type NoticeUpdatePayload = {
    title?: string;
    content?: string;
};