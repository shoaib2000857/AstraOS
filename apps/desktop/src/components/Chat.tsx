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
      const resp = await axios.post('/api/chat/', { prompt })
      const reply = resp.data.reply
      setMessages(prev=>[...prev, {role:'assistant', content: reply}])
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
