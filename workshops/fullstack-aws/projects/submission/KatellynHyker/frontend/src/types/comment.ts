/**
 * Shared types for comment-related data structures.
 */

export type Comment = {
    comment_id: string;
    content: string;
    created_at: string;
    updated_at: string;
    notice_id: string;
    user_id: string;
    author_email: string;
};

export type CommentCreatePayload = {
    content: string;
};

export type CommentUpdatePayload = {
    content: string;
};