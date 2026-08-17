import { apiClient } from './client'
import type { Notice, NoticeCreate, NoticeUpdate } from '../types'

export async function listNotices(params?: {
  q?: string
  author?: string
  author_id?: number
  category?: string
}): Promise<Notice[]> {
  const { data } = await apiClient.get<Notice[]>('/api/v1/notices', { params })
  return data
}

export async function getNotice(id: number): Promise<Notice> {
  const { data } = await apiClient.get<Notice>(`/api/v1/notices/${id}`)
  return data
}

export async function createNotice(payload: NoticeCreate): Promise<Notice> {
  const { data } = await apiClient.post<Notice>('/api/v1/notices', payload)
  return data
}

export async function updateNotice(
  id: number,
  payload: NoticeUpdate,
): Promise<Notice> {
  const { data } = await apiClient.put<Notice>(`/api/v1/notices/${id}`, payload)
  return data
}

export async function deleteNotice(id: number): Promise<void> {
  await apiClient.delete(`/api/v1/notices/${id}`)
}
