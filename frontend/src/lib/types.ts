/** Tipos derivados dos Pydantic schemas da API (main, Sprint 2). */

export interface User {
  id: string;
  email: string;
  full_name: string;
  company_id: string;
  role: "admin" | "manager" | "user";
}

export interface Employee {
  id: string;
  name: string;
  registration: string | null;
  cpf: string | null;
  pis: string | null;
  job_title: string | null;
  department: string | null;
  is_active: boolean;
  hired_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface EmployeePayload {
  name: string;
  registration?: string | null;
  cpf?: string | null;
  pis?: string | null;
  job_title?: string | null;
  department?: string | null;
  work_schedule?: Record<string, unknown> | null;
  photo_url?: string | null;
  is_active?: boolean;
  hired_at?: string | null;
  control_id?: number | null;
}

export interface Paginated<T> {
  data: T[];
  meta: {
    total: number;
    page: number;
    per_page: number;
    total_pages: number;
  };
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest extends LoginRequest {
  company_name: string;
  full_name: string;
}

export const SETTINGS_KEYS = [
  "timezone",
  "workday_minutes",
  "tolerance_minutes",
  "lunch_minutes",
  "overtime_enabled",
  "week_start",
] as const;

export type SettingsKey = (typeof SETTINGS_KEYS)[number];
