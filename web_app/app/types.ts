export type ApprovalStatus = 'pending' | 'approved' | 'rejected'

export type TaskPhase = 'project_setup' | 'dependency_installation' | 'feature_implementation' | 'testing' | 'complete'

export interface Task {
  id: string
  task: string
  source: string
  phase: TaskPhase
  approvalStatus: ApprovalStatus
  createdAt: string
  completedAt?: string
  user?: string
}

export interface Message {
  text: string
  user: string
  ts: string
  channel?: string
}

export interface Stats {
  totalTasks: number
  completedTasks: number
  pendingApproval: number
  totalMessages: number
}

export interface ApprovalRequest {
  status: ApprovalStatus
} 