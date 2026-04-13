import React from 'react'
import Chat from './components/Chat'

export default function App(){
  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-3xl">
        <h1 className="text-2xl font-semibold mb-4">AstraOS — Chat</h1>
        <Chat />
      </div>
    </div>
  )
}
