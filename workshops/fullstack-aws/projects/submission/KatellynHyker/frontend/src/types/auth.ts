/**
 * Shared types for authentication-related data structures.
 */

export type User = {
    user_id: string;
    email: string;
    created_at: string;
};

export type AuthResponse = {
    user: User;
    access_token: string;
    token_type: string;
};

export type LoginCredentials = {
    email: string;
    password: string;
};

export type RegisterCredentials = {
    email: string;
    password: string;
};