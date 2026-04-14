import React, { useState, useEffect } from 'react'
import axios from 'axios'

export default function Chat(){
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Array<{role:string, content:string}>>([])
  const [loading, setLoading] = useState(false)

  useEffect(()=>{
    // load recent conversation or nothing for now
  }, [])

  const send = async ()=>{
    if(!input.trim()) return
    const prompt = input
    setMessages(prev=>[...prev, {role:'user', content: prompt}])
    setInput('')
    setLoading(true)
    try{
      // Use fetch streaming to consume server-sent event stream response
      const resp = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      })

      if (!resp.ok || !resp.body) {
        throw new Error('Network response error')
      }

      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      let done = false
      let assembled = ''
      // add placeholder assistant message to UI and update it progressively
      setMessages(prev=>[...prev, {role:'assistant', content: ''}])
      let msgIndex = messages.length // index where assistant message was pushed

      while (!done) {
        const { value, done: readerDone } = await reader.read()
        done = readerDone
        if (value) {
          const chunk = decoder.decode(value)
          // server sends SSE `data: {...}\n\n` chunks; try to extract JSON
          const parts = chunk.split(/\n\n/)
          for (const p of parts) {
            const line = p.trim()
            if (!line) continue
            const m = line.replace(/^data:\s*/, '')
            try {
              const obj = JSON.parse(m)
              if (obj.type === 'delta') {
                assembled += obj.text
                setMessages(prev=>{
                  const copy = [...prev]
                  // update last assistant message
                  const idx = copy.findIndex(x => x.role === 'assistant' && x.content === '')
                  if (idx >= 0) {
                    copy[idx] = { ...copy[idx], content: assembled }
                  } else {
                    copy.push({ role: 'assistant', content: assembled })
                  }
                  return copy
                })
              } else if (obj.type === 'done') {
                assembled = obj.text || assembled
                setMessages(prev=>{
                  const copy = [...prev]
                  const idx = copy.findIndex(x => x.role === 'assistant' && (x.content === '' || x.content === assembled))
                  if (idx >= 0) copy[idx] = { ...copy[idx], content: assembled }
                  else copy.push({ role: 'assistant', content: assembled })
                  return copy
                })
              }
            } catch (e) {
              // not json — append raw
              assembled += m
              setMessages(prev=>{
                const copy = [...prev]
                const idx = copy.findIndex(x => x.role === 'assistant' && x.content === '')
                if (idx >= 0) copy[idx] = { ...copy[idx], content: assembled }
                else copy.push({ role: 'assistant', content: assembled })
                return copy
              })
            }
          }
        }
      }
    }catch(e){
      setMessages(prev=>[...prev, {role:'assistant', content: 'Error: failed to reach backend'}])
    }finally{
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded shadow p-4">
      <div className="space-y-3 mb-4 max-h-80 overflow-y-auto">
        {messages.map((m, idx)=>(
          <div key={idx} className={m.role==='user'? 'text-right text-sm':'text-left text-sm'}>
            <div className={m.role==='user'? 'inline-block bg-sky-100 px-3 py-2 rounded':'inline-block bg-slate-100 px-3 py-2 rounded'}>{m.content}</div>
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        <input value={input} onChange={e=>setInput(e.target.value)} className="flex-1 border rounded px-3 py-2" placeholder="Type a message..." />
        <button onClick={send} disabled={loading} className="bg-sky-600 text-white px-4 py-2 rounded">{loading? '...' : 'Send'}</button>
      </div>
    </div>
  )
}
