'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { CheckCircle, XCircle, Clock, Zap, Code, TestTube, Package } from 'lucide-react'
import { Task, ApprovalStatus } from '../types'
import { formatDistanceToNow } from 'date-fns'

interface TaskCardProps {
  task: Task
  onApproval: (taskId: string, status: ApprovalStatus) => void
}

const phaseIcons = {
  project_setup: Code,
  dependency_installation: Package,
  feature_implementation: Zap,
  testing: TestTube,
  complete: CheckCircle
}

const phaseLabels = {
  project_setup: 'Setup',
  dependency_installation: 'Dependencies',
  feature_implementation: 'Implementation',
  testing: 'Testing',
  complete: 'Complete'
}

const phaseColors = {
  project_setup: 'blue',
  dependency_installation: 'purple',
  feature_implementation: 'green',
  testing: 'yellow',
  complete: 'emerald'
}

export default function TaskCard({ task, onApproval }: TaskCardProps) {
  const PhaseIcon = phaseIcons[task.phase]
  const phaseColor = phaseColors[task.phase]
  
  const getStatusColor = (status: ApprovalStatus) => {
    switch (status) {
      case 'approved': return 'text-green-500'
      case 'rejected': return 'text-red-500'
      default: return 'text-yellow-500'
    }
  }

  const getStatusIcon = (status: ApprovalStatus) => {
    switch (status) {
      case 'approved': return <CheckCircle className="h-4 w-4" />
      case 'rejected': return <XCircle className="h-4 w-4" />
      default: return <Clock className="h-4 w-4" />
    }
  }

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="bg-card border border-border rounded-lg p-4 hover:shadow-lg transition-all duration-200"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {/* Task Header */}
          <div className="flex items-center space-x-3 mb-3">
            <div className={`p-2 rounded-lg bg-${phaseColor}-100 dark:bg-${phaseColor}-900/20`}>
              <PhaseIcon className={`h-4 w-4 text-${phaseColor}-600 dark:text-${phaseColor}-400`} />
            </div>
            <div className="flex-1">
              <h3 className="font-medium text-foreground line-clamp-2">{task.task}</h3>
              <div className="flex items-center space-x-2 mt-1">
                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-${phaseColor}-100 text-${phaseColor}-800 dark:bg-${phaseColor}-900 dark:text-${phaseColor}-200`}>
                  {phaseLabels[task.phase]}
                </span>
                <span className={`inline-flex items-center space-x-1 text-xs ${getStatusColor(task.approvalStatus)}`}>
                  {getStatusIcon(task.approvalStatus)}
                  <span className="capitalize">{task.approvalStatus}</span>
                </span>
              </div>
            </div>
          </div>

          {/* Source Message */}
          <div className="mb-3">
            <p className="text-sm text-muted-foreground mb-1">Source:</p>
            <p className="text-sm bg-muted/50 rounded px-3 py-2 border-l-2 border-primary">
              "{task.source}"
            </p>
          </div>

          {/* Timestamp */}
          <div className="text-xs text-muted-foreground">
            Created {formatDistanceToNow(new Date(task.createdAt), { addSuffix: true })}
            {task.completedAt && (
              <span className="ml-2">
                • Completed {formatDistanceToNow(new Date(task.completedAt), { addSuffix: true })}
              </span>
            )}
          </div>
        </div>

        {/* Approval Actions */}
        {task.approvalStatus === 'pending' && (
          <div className="flex flex-col space-y-2 ml-4">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => onApproval(task.id, 'approved')}
              className="approval-button approve"
            >
              <CheckCircle className="h-4 w-4 mr-1" />
              Approve
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => onApproval(task.id, 'rejected')}
              className="approval-button reject"
            >
              <XCircle className="h-4 w-4 mr-1" />
              Reject
            </motion.button>
          </div>
        )}

        {/* Status Indicator for completed tasks */}
        {task.approvalStatus !== 'pending' && (
          <div className="ml-4">
            <div className={`p-2 rounded-full ${task.approvalStatus === 'approved' ? 'bg-green-100 dark:bg-green-900/20' : 'bg-red-100 dark:bg-red-900/20'}`}>
              {task.approvalStatus === 'approved' ? (
                <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400" />
              ) : (
                <XCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
              )}
            </div>
          </div>
        )}
      </div>
    </motion.div>
  )
} 