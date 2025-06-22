'use client'

import React from 'react'
import { MessageSquare, User } from 'lucide-react'
import { Message } from '../types'
import { formatDistanceToNow } from 'date-fns'

interface MessageCardProps {
  message: Message
}

export default function MessageCard({ message }: MessageCardProps) {
  return (
    <div className="bg-muted/30 rounded-lg p-3 border border-border hover:bg-muted/50 transition-colors">
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0">
          <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
            <User className="h-4 w-4 text-primary" />
          </div>
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm font-medium text-foreground">
              User {message.user.slice(-4)}
            </span>
            <span className="text-xs text-muted-foreground">
              {formatDistanceToNow(new Date(parseFloat(message.ts) * 1000), { addSuffix: true })}
            </span>
          </div>
          
          <p className="text-sm text-muted-foreground line-clamp-3">
            {message.text}
          </p>
        </div>
      </div>
    </div>
  )
} 