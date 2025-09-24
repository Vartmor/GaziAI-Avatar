// frontend/src/components/Avatar/useLipSync.js
import { useEffect, useState } from 'react'

export default function useLipSync(audioUrl) {
  const [isSpeaking, setIsSpeaking] = useState(false)

  useEffect(() => {
    if (!audioUrl) return

    setIsSpeaking(true)
    const audio = new Audio(audioUrl)
    audio.play()

    audio.onended = () => {
      setIsSpeaking(false)
    }

    return () => {
      audio.pause()
      setIsSpeaking(false)
    }
  }, [audioUrl])

  return isSpeaking
}