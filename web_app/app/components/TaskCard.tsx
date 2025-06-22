'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { CheckCircle, XCircle, Clock, Zap, Code, TestTube, Package, Loader2, Play, AlertTriangle } from 'lucide-react'
import { Task, SelectionStatus } from '../types'
import { formatDistanceToNow } from 'date-fns'

interface TaskCardProps {
  task: Task
  onSelection: (taskId: string, status: SelectionStatus) => void
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

export default function TaskCard({ task, onSelection }: TaskCardProps) {
  const [isProcessing, setIsProcessing] = useState(false)
  const [showDependencyWarning, setShowDependencyWarning] = useState(false)
  const [dependencies, setDependencies] = useState<any[]>([])
  const [dependencyWarning, setDependencyWarning] = useState<string | null>(null)
  
  const PhaseIcon = phaseIcons[task.phase]
  const phaseColor = phaseColors[task.phase]
  
  const getStatusColor = (status: SelectionStatus) => {
    switch (status) {
      case 'selected': return 'text-green-500'
      case 'rejected': return 'text-red-500'
      case 'executed': return 'text-purple-500'
      default: return 'text-yellow-500'
    }
  }

  const getStatusIcon = (status: SelectionStatus) => {
    switch (status) {
      case 'selected': return <CheckCircle className="h-4 w-4" />
      case 'rejected': return <XCircle className="h-4 w-4" />
      case 'executed': return <Play className="h-4 w-4" />
      default: return <Clock className="h-4 w-4" />
    }
  }

  const checkDependencies = async (taskId: string) => {
    try {
      const response = await fetch(`/api/tasks/${taskId}/dependencies`)
      if (response.ok) {
        const data = await response.json()
        setDependencies(data.dependencies || [])
        setDependencyWarning(data.warning)
        return data.dependencies?.length > 0
      }
    } catch (error) {
      console.error('Error checking dependencies:', error)
    }
    return false
  }

  const handleSelection = async (status: SelectionStatus) => {
    // Don't allow changing status of executed tasks
    if (task.selectionStatus === 'executed') {
      alert('Cannot change status of executed tasks.')
      return
    }
    
    // Check dependencies before rejecting
    if (status === 'rejected') {
      const hasDependencies = await checkDependencies(task.id)
      if (hasDependencies) {
        setShowDependencyWarning(true)
        return
      }
    }
    
    setIsProcessing(true)
    try {
      await onSelection(task.id, status)
      setIsProcessing(false)
    } catch (error) {
      setIsProcessing(false)
      console.error('Selection failed:', error)
    }
  }

  const confirmRejection = async () => {
    setShowDependencyWarning(false)
    setIsProcessing(true)
    try {
      await onSelection(task.id, 'rejected')
      setIsProcessing(false)
    } catch (error) {
      setIsProcessing(false)
      console.error('Selection failed:', error)
    }
  }

  return (
    <>
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
                  <span className={`inline-flex items-center space-x-1 text-xs ${getStatusColor(task.selectionStatus)}`}>
                    {getStatusIcon(task.selectionStatus)}
                    <span className="capitalize">{task.selectionStatus}</span>
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
              {task.selectedAt && (
                <span className="ml-2">
                  • Selected {formatDistanceToNow(new Date(task.selectedAt), { addSuffix: true })}
                </span>
              )}
              {task.executedAt && (
                <span className="ml-2">
                  • Executed {formatDistanceToNow(new Date(task.executedAt), { addSuffix: true })}
                </span>
              )}
            </div>
          </div>

          {/* Selection Actions */}
          {!isProcessing && task.selectionStatus !== 'executed' && (
            <div className="flex flex-col space-y-2 ml-4">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => handleSelection('selected')}
                className={`approval-button ${task.selectionStatus === 'selected' ? 'approve' : 'pending'}`}
              >
                <CheckCircle className="h-4 w-4 mr-1" />
                Select
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => handleSelection('rejected')}
                className={`approval-button ${task.selectionStatus === 'rejected' ? 'reject' : 'pending'}`}
              >
                <XCircle className="h-4 w-4 mr-1" />
                Reject
              </motion.button>
            </div>
          )}

          {/* Processing State */}
          {isProcessing && (
            <div className="ml-4">
              <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Processing...</span>
              </div>
            </div>
          )}

          {/* Status Indicator for executed tasks */}
          {task.selectionStatus === 'executed' && !isProcessing && (
            <div className="ml-4">
              <div className="p-2 rounded-full bg-purple-100 dark:bg-purple-900/20">
                <Play className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              </div>
            </div>
          )}
        </div>
      </motion.div>

      {/* Dependency Warning Modal */}
      {showDependencyWarning && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-card border border-border rounded-lg p-6 max-w-md mx-4">
            <div className="flex items-center space-x-2 mb-4">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
              <h3 className="text-lg font-semibold">Dependency Warning</h3>
            </div>
            
            <p className="text-sm text-muted-foreground mb-4">
              {dependencyWarning}
            </p>
            
            {dependencies.length > 0 && (
              <div className="mb-4">
                <p className="text-sm font-medium mb-2">Affected tasks:</p>
                <div className="space-y-1">
                  {dependencies.map((dep, index) => (
                    <div key={index} className="text-xs bg-muted/50 rounded px-2 py-1">
                      • {dep.task}
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            <div className="flex space-x-3">
              <button
                onClick={() => setShowDependencyWarning(false)}
                className="flex-1 px-3 py-2 text-sm border border-border rounded-md hover:bg-muted transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={confirmRejection}
                className="flex-1 px-3 py-2 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
              >
                Reject Anyway
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
} 