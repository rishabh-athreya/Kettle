export type SelectionStatus = 'pending' | 'selected' | 'rejected' | 'executed'

export type TaskPhase = 'project_setup' | 'dependency_installation' | 'feature_implementation' | 'testing' | 'complete'

export interface Task {
  id: string
  task: string
  source: string
  phase: TaskPhase
  selectionStatus: SelectionStatus
  createdAt: string
  selectedAt?: string
  executedAt?: string
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
  selectedTasks: number
  pendingSelection: number
  executedTasks: number
  totalMessages: number
}

export interface SelectionRequest {
  status: SelectionStatus
} 