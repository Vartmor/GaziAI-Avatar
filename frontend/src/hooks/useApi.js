// frontend/src/hooks/useApi.js
import { useState } from 'react'
import { apiUrl, assetUrl } from '../config/api'

export default function useApi() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const sendAudio = async (audioBlob) => {
    setLoading(true)
    setError(null)
    try {
      const formData = new FormData()
      formData.append('audio', audioBlob, 'recording.wav')

      const response = await fetch(apiUrl('/api/upload_audio'), {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('API request failed')
      }

      const data = await response.json()
      if (data?.audio_url) {
        data.audio_url = assetUrl(data.audio_url)
      }
      return data
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  return { loading, error, sendAudio }
}