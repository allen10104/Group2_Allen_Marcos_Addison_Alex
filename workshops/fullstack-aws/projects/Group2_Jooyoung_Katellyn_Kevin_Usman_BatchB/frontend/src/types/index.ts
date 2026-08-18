export type Category = 'Announcement' | 'Event' | 'General' | 'Other'

export interface User {
  id: number
  name: string
  email: string
  is_admin: boolean
}

export interface Notice {
  id: number
  title: string
  content: string
  category: string
  date: string
  author: string
  author_id: number
}

export interface NoticeCreate {
  title: string
  content: string
  category: Category
  date?: string | null
}

export interface NoticeUpdate {
  title?: string
  content?: string
  category?: Category
  date?: string | null
}

export interface TokenResponse {
  access_token: string
  token_type: string
}
