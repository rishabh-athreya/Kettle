'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import { 
  Coffee, 
  CheckCircle, 
  XCircle, 
  Clock, 
  MessageSquare, 
  Zap,
  RefreshCw,
  TrendingUp,
  Play,
  Trash2
} from 'lucide-react'
import TaskCard from './components/TaskCard'
import MessageCard from './components/MessageCard'
import StatsCard from './components/StatsCard'
import ResearchResourceCard, { ResearchResource } from './components/ResearchResourceCard'
import { Task, Message, SelectionStatus } from './types'

export default function Dashboard() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(true)
  const [executing, setExecuting] = useState(false)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())
  const [stats, setStats] = useState({
    totalTasks: 0,
    selectedTasks: 0,
    pendingSelection: 0,
    executedTasks: 0,
    totalMessages: 0
  })
  const [resources, setResources] = useState<ResearchResource[]>([])
  const [writingTasks, setWritingTasks] = useState<Task[]>([])
  
  useEffect(() => {
    fetchData()
    fetchResearchResources()
    fetchWritingTasks()
    // Set up polling for real-time updates - reduced to 10 seconds
    const interval = setInterval(() => {
      console.log('Auto-refreshing data...')
      fetchData()
      fetchResearchResources()
      fetchWritingTasks()
    }, 10000)
    return () => clearInterval(interval)
  }, [])

  const fetchData = async () => {
    try {
      console.log('Fetching data from API...')
      const [tasksRes, messagesRes] = await Promise.all([
        fetch('/api/tasks'),
        fetch('/api/messages')
      ])
      
      if (tasksRes.ok) {
        const tasksData = await tasksRes.json()
        console.log(`Fetched ${tasksData.length} tasks`)
        setTasks(tasksData)
        setStats(prev => ({
          ...prev,
          totalTasks: tasksData.length,
          selectedTasks: tasksData.filter((t: Task) => t.selectionStatus === 'selected').length,
          pendingSelection: tasksData.filter((t: Task) => t.selectionStatus === 'pending').length,
          executedTasks: tasksData.filter((t: Task) => t.selectionStatus === 'executed').length
        }))
      } else {
        console.error('Failed to fetch tasks:', tasksRes.status)
      }
      
      if (messagesRes.ok) {
        const messagesData = await messagesRes.json()
        console.log(`Fetched ${messagesData.messages?.length || 0} messages`)
        setMessages(messagesData.messages || [])
        setStats(prev => ({
          ...prev,
          totalMessages: messagesData.messages?.length || 0
        }))
      } else {
        console.error('Failed to fetch messages:', messagesRes.status)
      }
      
      setLastUpdate(new Date())
    } catch (error) {
      console.error('Error fetching data:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchResearchResources = async () => {
    try {
      const res = await fetch('/api/research-resources')
      if (res.ok) {
        const data = await res.json()
        setResources(data)
      }
    } catch (error) {
      console.error('Error fetching research resources:', error)
    }
  }

  const fetchWritingTasks = async () => {
    try {
      const res = await fetch('/api/writing_tasks')
      if (res.ok) {
        const data = await res.json()
        setWritingTasks(data)
      }
    } catch (error) {
      console.error('Error fetching writing tasks:', error)
    }
  }

  const handleTaskSelection = async (taskId: string, status: SelectionStatus) => {
    try {
      const response = await fetch(`/api/tasks/${taskId}/select`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
      })

      if (response.ok) {
        // Always re-fetch from backend to ensure UI is in sync
        await fetchData()
      } else {
        console.error('Failed to update task selection')
        alert('Failed to update task selection. Please try again.')
      }
    } catch (error) {
      console.error('Error updating task selection:', error)
      alert('Error updating task selection. Please try again.')
    }
  }

  const handleExecuteSelected = async () => {
    const selectedTasks = tasks.filter(task => task.selectionStatus === 'selected')
    
    if (selectedTasks.length === 0) {
      alert('No tasks selected for execution. Please select some tasks first.')
      return
    }

    setExecuting(true)
    try {
      const response = await fetch('/api/execute-selected', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      
      const result = await response.json()
      
      if (result.success) {
        alert(`Successfully executed ${result.executedTasks} tasks!`)
        await fetchData() // Refresh to show updated statuses
      } else {
        console.error('Execution failed:', result.error)
        alert(`Execution failed: ${result.error}`)
      }
    } catch (error) {
      console.error('Error executing tasks:', error)
      alert('Error executing tasks. Check console for details.')
    } finally {
      setExecuting(false)
    }
  }

  const handleReset = async () => {
    if (!confirm('Are you sure you want to reset all tasks and messages? This will clear everything.')) {
      return
    }
    
    try {
      // Clear tasks and messages by setting them to empty
      const tasksResponse = await fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'reset' })
      })
      
      const messagesResponse = await fetch('/api/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'reset' })
      })
      
      const mediaResponse = await fetch('/api/media', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'reset' })
      })
      
      if (tasksResponse.ok && messagesResponse.ok && mediaResponse.ok) {
        alert('Successfully reset tasks, messages, and research resources!')
        await fetchData() // Refresh the UI
        await fetchResearchResources() // Refresh research resources
      } else {
        alert('Failed to reset data. Please try again.')
      }
    } catch (error) {
      console.error('Error resetting data:', error)
      alert('Error resetting data. Check console for details.')
    }
  }

  const handleOpenAllResources = () => {
    if (resources.length === 0) return
    
    let openedCount = 0
    let failedCount = 0
    const totalResources = resources.filter(r => r.url).length
    
    resources.forEach((resource, index) => {
      if (resource.url) {
        try {
          // Add a small delay to prevent browser from blocking multiple popups
          setTimeout(() => {
            const newWindow = window.open(resource.url, '_blank', 'noopener,noreferrer')
            if (newWindow) {
              openedCount++
            } else {
              failedCount++
              console.warn(`Failed to open: ${resource.url}`)
            }
            
            // Show final count after all attempts
            if (index === resources.length - 1) {
              if (openedCount > 0) {
                console.log(`Successfully opened ${openedCount} resources`)
              }
              if (failedCount > 0) {
                console.warn(`Failed to open ${failedCount} resources (possibly blocked by browser or unavailable)`)
              }
              
              // Show user-friendly alert
              let message = `Opened ${openedCount} of ${totalResources} resources in new browser tabs.`
              if (failedCount > 0) {
                message += `\n\n${failedCount} resources failed to open (possibly blocked by browser popup blocker or unavailable URLs).`
                message += '\n\nCheck the browser console for details.'
              }
              alert(message)
            }
          }, index * 100) // 100ms delay between each open attempt
        } catch (error) {
          failedCount++
          console.error(`Error opening ${resource.url}:`, error)
        }
      }
    })
  }

  const handleSelectAll = async () => {
    const pendingTasks = tasks.filter(task => task.selectionStatus === 'pending')
    
    if (pendingTasks.length === 0) {
      alert('No pending tasks to select.')
      return
    }

    try {
      // Select all pending tasks
      await Promise.all(
        pendingTasks.map(task => 
          fetch(`/api/tasks/${task.id}/select`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'selected' })
          })
        )
      )
      
      // Refresh data to show updated statuses
      await fetchData()
      alert(`Successfully selected ${pendingTasks.length} tasks!`)
    } catch (error) {
      console.error('Error selecting all tasks:', error)
      alert('Error selecting all tasks. Please try again.')
    }
  }

  // Render research/writing section (simplified for clarity)
  const renderResearchSection = () => (
    <div className="mt-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold">Research Resources</h2>
        <button
          onClick={handleOpenAllResources}
          disabled={resources.length === 0}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:opacity-50 text-white rounded-md transition-colors"
        >
          <span>Open All in Browser</span>
        </button>
      </div>
      {/* Writing report link, if present */}
      {writingTasks.map((task, idx) =>
        task.report_path ? (
          <div key={idx} className="mb-2">
            <a
              href={`/api/writing/${encodeURIComponent(task.report_path.split('/').pop() || '')}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              📄 View LaTeX Report: {task.task}
            </a>
          </div>
        ) : null
      )}
      {/* Render research resources as widgets */}
      {resources.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          <span className="block mb-2">No research resources found yet.</span>
          <span className="text-xs">Research resources will appear here after research tasks are processed.</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {resources.map((resource, idx) => (
            <ResearchResourceCard key={resource.url + idx} resource={resource} />
          ))}
        </div>
      )}
    </div>
  )

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-6 w-6 animate-spin text-primary" />
          <span className="text-lg">Loading Kettle Dashboard...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="flex items-center justify-center w-10 h-10 bg-primary rounded-lg">
                <Coffee className="h-6 w-6 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-foreground">Kettle AI</h1>
                <p className="text-sm text-muted-foreground">AI-Powered Project Automation</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleExecuteSelected}
                disabled={executing || stats.selectedTasks === 0}
                className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-800 disabled:opacity-50 text-white rounded-md transition-colors"
              >
                <Play className={`h-4 w-4 ${executing ? 'animate-spin' : ''}`} />
                <span>{executing ? 'Executing...' : `Execute Selected (${stats.selectedTasks})`}</span>
              </motion.button>
              <button
                onClick={handleReset}
                className="flex items-center space-x-2 px-4 py-2 bg-secondary hover:bg-secondary/80 rounded-md transition-colors"
              >
                <Trash2 className="h-4 w-4" />
                <span>Reset</span>
              </button>
            </div>
          </div>
          <div className="mt-2 text-xs text-muted-foreground">
            Last updated: {lastUpdate.toLocaleTimeString()} • Auto-refresh every 10 seconds
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8">
        {/* Coding Tasks Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Task History */}
          <div className="lg:col-span-2">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <div className="bg-card rounded-lg border border-border p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-semibold text-foreground">Task Selection</h2>
                  <div className="flex items-center space-x-3">
                    <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                      <TrendingUp className="h-4 w-4" />
                      <span>Select tasks to execute</span>
                    </div>
                    {tasks.filter(task => task.selectionStatus === 'pending').length > 0 && (
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={handleSelectAll}
                        className="approval-button approve"
                      >
                        <CheckCircle className="h-4 w-4 mr-1" />
                        Select All
                      </motion.button>
                    )}
                  </div>
                </div>
                <div className="space-y-4">
                  {tasks.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <Coffee className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>No tasks yet. Kettle is monitoring Slack for new messages...</p>
                    </div>
                  ) : (
                    tasks.map((task, index) => (
                      <motion.div
                        key={task.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.3, delay: index * 0.1 }}
                      >
                        <TaskCard
                          task={task}
                          onSelection={handleTaskSelection}
                        />
                      </motion.div>
                    ))
                  )}
                </div>
              </div>
            </motion.div>
          </div>
          {/* Recent Messages */}
          <div>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <div className="bg-card rounded-lg border border-border p-6">
                <h2 className="text-xl font-semibold text-foreground mb-6">Recent Messages</h2>
                <div className="space-y-4">
                  {messages.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>No messages yet</p>
                    </div>
                  ) : (
                    messages.slice(0, 5).map((message, index) => (
                      <motion.div
                        key={message.ts}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.3, delay: index * 0.1 }}
                      >
                        <MessageCard message={message} />
                      </motion.div>
                    ))
                  )}
                </div>
              </div>
            </motion.div>
          </div>
        </div>
        {/* Research Resources Section */}
        {renderResearchSection()}
      </div>
    </div>
  )
} 