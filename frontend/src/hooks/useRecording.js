import { useRef, useState } from 'react'
import { apiUrl, assetUrl } from '../config/api'
import useAppStore from '../stores/appStore'

export default function useRecording() {
  const { setIsRecording, setAudioUrl, setLoading, setCuesJson, setCurrentAnimation } = useAppStore()
  const [mediaRecorder, setMediaRecorder] = useState(null)
  const chunksRef = useRef([])

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

      const preferred = 'audio/webm;codecs=opus'
      const mimeType = window.MediaRecorder && MediaRecorder.isTypeSupported(preferred)
        ? preferred
        : (MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : '')

      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)
      setMediaRecorder(recorder)
      chunksRef.current = []

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          chunksRef.current.push(event.data)
        }
      }

      recorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: mimeType || 'audio/webm' })
        chunksRef.current = []

        try {
          setLoading(true)
          const formData = new FormData()
          formData.append('audio', audioBlob, 'recording.webm')

          const response = await fetch(apiUrl('/api/upload_audio'), {
            method: 'POST',
            body: formData,
          })

          if (!response.ok) throw new Error('API request failed')

          const data = await response.json()
          if (data.cues_json) setCuesJson(data.cues_json)
          if (data.audio_url) {
            setAudioUrl(assetUrl(data.audio_url))
            if (setCurrentAnimation) setCurrentAnimation('Greeting')
          }
        } catch (err) {
          console.error('Error sending audio:', err)
        } finally {
          setLoading(false)
        }
      }

      recorder.start()
      setIsRecording(true)
    } catch (error) {
      console.error('Recording error:', error)
      throw error
    }
  }

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop()
      setIsRecording(false)
      // Mikrofon kanalını serbest bırak
      mediaRecorder.stream.getTracks().forEach(t => t.stop())
    }
  }

  return { startRecording, stopRecording }
}

