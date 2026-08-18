// This file contains the API functions for the SyncUp frontend application.
// It provides functions to interact with the backend API, including user authentication, notice management,
// and invite code generation. Each function uses the configured Axios client to make HTTP requests to the backend endpoints.

import { client } from "./client";

// Logs in a user by sending their email and password to the backend API.
export async function login(email, password) {
  const { data } = await client.post("/auth/login", { email, password });
  return data;
}
// Logs out a user by clearing their access and refresh tokens from local storage.
export async function register(email, password, role, inviteCode) {
  const { data } = await client.post("/auth/register", {
    email,
    password,
    role,
    invite_code: inviteCode || null,
  });
  return data;
}
// Verifies a manager's email and code by sending them to the backend API.
export async function verifyManager(email, code) {
  const { data } = await client.post("/auth/verify-manager", { email, code });
  return data;
}
// Fetches the profile (including email) of whoever the current access token belongs to.
// Needed because the JWT itself only carries id + role, not email.
export async function getMe() {
  const { data } = await client.get("/auth/me");
  return data;
}
// Refreshes the access token using the refresh token stored in local storage.
export async function createEmployee(email, password) {
  const { data } = await client.post("/users", { email, password, role: "EMPLOYEE" });
  return data;
}
// Retrieves the current user's information from the backend API.
export async function getFeed() {
  const { data } = await client.get("/notices");
  return data;
}
// Retrieves the current user's information from the backend API.
export async function submitNotice(title, body, category) {
  const { data } = await client.post("/notices", { title, body, category });
  return data;
}
// Retrieves the current user's information from the backend API.
export async function approveNotice(id) {
  const { data } = await client.post(`/notices/${id}/approve`);
  return data;
}
// Retrieves the current user's information from the backend API.
export async function rejectNotice(id) {
  const { data } = await client.post(`/notices/${id}/reject`);
  return data;
}
// Retrieves the current user's information from the backend API.
export async function acknowledgeNotice(id) {
  const { data } = await client.post(`/notices/${id}/ack`);
  return data;
}
// Retrieves the read status of a specific notice by its ID from the backend API.
export async function getReadStatus(id) {
  const { data } = await client.get(`/notices/${id}/read-status`);
  return data;
}
// Retrieves the list of invite codes from the backend API.
export async function createInviteCode(targetEmail) {
  const { data } = await client.post("/admin/invite-codes", { target_email: targetEmail });
  return data;
}