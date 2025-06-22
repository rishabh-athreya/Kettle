'use client'

import React, { useState, useEffect } from 'react'
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
  Download
} from 'lucide-react'
import TaskCard from './components/TaskCard'
import MessageCard from './components/MessageCard'
import StatsCard from './components/StatsCard'
import { Task, Message, ApprovalStatus } from './types'

export default function Dashboard() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [stats, setStats] = useState({
    totalTasks: 0,
    completedTasks: 0,
    pendingApproval: 0,
    totalMessages: 0
  })

  useEffect(() => {
    fetchData()
    // Set up polling for real-time updates
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  const fetchData = async () => {
    try {
      const [tasksRes, messagesRes] = await Promise.all([
        fetch('/api/tasks'),
        fetch('/api/messages')
      ])
      
      if (tasksRes.ok) {
        const tasksData = await tasksRes.json()
        setTasks(tasksData)
        setStats(prev => ({
          ...prev,
          totalTasks: tasksData.length,
          completedTasks: tasksData.filter((t: Task) => t.approvalStatus === 'approved').length,
          pendingApproval: tasksData.filter((t: Task) => t.approvalStatus === 'pending').length
        }))
      }
      
      if (messagesRes.ok) {
        const messagesData = await messagesRes.json()
        setMessages(messagesData.messages || [])
        setStats(prev => ({
          ...prev,
          totalMessages: messagesData.messages?.length || 0
        }))
      }
    } catch (error) {
      console.error('Error fetching data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleManualRefresh = async () => {
    setRefreshing(true)
    try {
      const response = await fetch('/api/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      
      const result = await response.json()
      
      if (result.success) {
        // Wait a moment for the pipeline to complete, then fetch new data
        setTimeout(() => {
          fetchData()
        }, 2000)
      } else {
        console.error('Refresh failed:', result.error)
        alert(`Refresh failed: ${result.error}`)
      }
    } catch (error) {
      console.error('Error refreshing data:', error)
      alert('Error refreshing data. Check console for details.')
    } finally {
      setRefreshing(false)
    }
  }

  const handleApproval = async (taskId: string, status: ApprovalStatus) => {
    try {
      const response = await fetch(`/api/tasks/${taskId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
      })
      
      if (response.ok) {
        setTasks(prev => prev.map(task => 
          task.id === taskId ? { ...task, approvalStatus: status } : task
        ))
        setStats(prev => ({
          ...prev,
          completedTasks: status === 'approved' ? prev.completedTasks + 1 : prev.completedTasks,
          pendingApproval: prev.pendingApproval - 1
        }))
      }
    } catch (error) {
      console.error('Error updating task approval:', error)
    }
  }

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
                onClick={handleManualRefresh}
                disabled={refreshing}
                className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-800 text-white rounded-md transition-colors"
              >
                <Download className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
                <span>{refreshing ? 'Fetching...' : 'Fetch Slack'}</span>
              </motion.button>
              <button
                onClick={fetchData}
                className="flex items-center space-x-2 px-4 py-2 bg-secondary hover:bg-secondary/80 rounded-md transition-colors"
              >
                <RefreshCw className="h-4 w-4" />
                <span>Refresh</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatsCard
            title="Total Tasks"
            value={stats.totalTasks}
            icon={Zap}
            color="blue"
          />
          <StatsCard
            title="Completed"
            value={stats.completedTasks}
            icon={CheckCircle}
            color="green"
          />
          <StatsCard
            title="Pending Approval"
            value={stats.pendingApproval}
            icon={Clock}
            color="yellow"
          />
          <StatsCard
            title="Messages"
            value={stats.totalMessages}
            icon={MessageSquare}
            color="purple"
          />
        </div>

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
                  <h2 className="text-xl font-semibold text-foreground">Task History</h2>
                  <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                    <TrendingUp className="h-4 w-4" />
                    <span>Real-time updates</span>
                  </div>
                </div>
                
                <div className="space-y-4">
                  {tasks.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <Coffee className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>No tasks yet. Click "Fetch Slack" to get started!</p>
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
                          onApproval={handleApproval}
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
                      <p>No messages yet. Click "Fetch Slack" to load messages!</p>
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
      </div>
    </div>
  )
} 