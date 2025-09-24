import { create } from 'zustand'
import { apiUrl, assetUrl } from '../config/api'

const useAppStore = create((set) => ({
  // State
  isRecording: false,
  audioUrl: null,
  isSpeaking: false,
  cvResults: {},
  error: null,
  loading: false,
  cuesJson: null,
  currentAnimation: 'Idle',
  activeGame: 'none', // 'none' | 'math' | 'rps'

  // Actions
  setIsRecording: (isRecording) => set({ isRecording }),
  setAudioUrl: (audioUrl) => set({ audioUrl }),
  setIsSpeaking: (isSpeaking) => set({ isSpeaking }),
  setCvResults: (cvResults) => set({ cvResults }),
  setError: (error) => set({ error }),
  setLoading: (loading) => set({ loading }),
  setCuesJson: (cuesJson) => set({ cuesJson }),
  setCurrentAnimation: (anim) => set({ currentAnimation: anim }),
  setActiveGame: (game) => set({ activeGame: game || 'none' }),

  // Optional: sendAudio helper (no playback here)
  sendAudio: async (audioBlob) => {
    set({ loading: true, error: null })
    try {
      const formData = new FormData()
      formData.append('audio', audioBlob, 'recording.webm')

      const response = await fetch(apiUrl('/api/upload_audio'), {
        method: 'POST',
        body: formData,
      })
      if (!response.ok) throw new Error('API request failed')

      const data = await response.json()
      if (data.audio_url && data.cues_json) {
        set({ audioUrl: assetUrl(data.audio_url), cuesJson: data.cues_json })
      }
      return data
    } catch (err) {
      set({ error: err.message })
      throw err
    } finally {
      set({ loading: false })
    }
  },

  // CV results fetch
  fetchCvResults: async () => {
    try {
      const response = await fetch(apiUrl('/api/get_detection_results'))
      const data = await response.json()
      if (data.success) set({ cvResults: data })
      return data
    } catch (err) {
      console.error('CV results error:', err)
      set({ error: 'CV sonuçları alınamadı' })
    }
  }
}))

export default useAppStore
