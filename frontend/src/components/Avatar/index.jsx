import { useEffect, useMemo, useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';
import { useFBX, useAnimations } from '@react-three/drei';
import * as THREE from 'three';
import useAppStore from '../../stores/appStore';

// Rhubarb viseme -> candidate morph targets (Ready Player Me first)
const visemeCandidates = {
  // Silence / closed
  X: ['viseme_PP', 'viseme_sil', 'rest'],
  // Basic mouth shapes
  A: ['viseme_PP', 'viseme_M', 'viseme_sil', 'rest'],
  B: ['viseme_kk', 'viseme_E', 'viseme_I'],
  C: ['viseme_I', 'viseme_E'],
  D: ['viseme_AA', 'viseme_aa'],
  E: ['viseme_O', 'viseme_U', 'viseme_E'],
  F: ['viseme_U', 'viseme_O'],
  // Extended shapes
  G: ['viseme_FF', 'viseme_FV'],
  H: ['viseme_TH', 'viseme_CH', 'viseme_L', 'viseme_RR'],
};

export default function Avatar() {
  // Config: keep body idle during speech while lips move
  const KEEP_IDLE_WHILE_SPEAKING = true;
  // Config: use random lips instead of cue-driven lipsync
  const RANDOM_LIPSYNC_WHILE_SPEAKING = true;
  const groupRef = useRef();
  const audioRef = useRef(null);
  const waveUntilRef = useRef(0);
  const [model, setModel] = useState(null);
  // mesh.uuid -> { letter -> index }
  const morphIndexCache = useRef(new Map());
  const waveBoneRef = useRef(null);
  const waveBoneInitRef = useRef(null);
  const visemeKeysRef = useRef([]); // discovered viseme keys on meshes
  const randomMouthKeyRef = useRef(null);
  const nextMouthSwitchAtRef = useRef(0);
  const { audioUrl, cuesJson, currentAnimation, isSpeaking } = useAppStore();

  // GLB model yükleme
  useEffect(() => {
    const loader = new GLTFLoader();
    let isMounted = true;

    loader.load(
      '/models/646d9dcdc8a5f5bddbfac913.glb',
      (gltf) => {
        if (!isMounted) return;

        // Model yüklendikten sonra morph target dictionary'yi kontrol et
        gltf.scene.traverse((child) => {
          if (child.isMesh && child.morphTargetDictionary) {
            console.log('Morph targets:', child.morphTargetDictionary);
            try {
              const keys = Object.keys(child.morphTargetDictionary)
                .filter(k => /^viseme_/i.test(k));
              if (keys.length) {
                const set = new Set(visemeKeysRef.current);
                keys.forEach(k => set.add(k));
                visemeKeysRef.current = Array.from(set);
              }
            } catch {}
          }
        });

        setModel(gltf);
      },
      undefined,
      (err) => {
        console.error('Model yüklenemedi:', err);
      }
    );

    return () => {
      isMounted = false;
    };
  }, []);

  // FBX animasyonlarını yükleme
  const { animations: idleAnim } = useFBX('/animations/Idle.fbx');
  const { animations: greetingAnim } = useFBX('/animations/Standing Greeting.fbx');

  // Ham klipler ve isim
  const idleRaw = idleAnim[0] ? idleAnim[0] : null;
  const greetRaw = greetingAnim[0] ? greetingAnim[0] : null;
  if (idleRaw) idleRaw.name = 'Idle';
  if (greetRaw) greetRaw.name = 'Greeting';

  // Ãƒâ€Ã‚Â°sim normalizasyonu
  const normalize = (s) => (s || '').toLowerCase().replace(/[^a-z0-9]/g, '');

  // Manuel adaylar (bazı riglerde farklılıklar için)
  const manualCandidates = (baseNorm) => {
    const map = {
      armature: ['mixamorig:hips', 'hips', 'root', 'armature'],
      hips: ['mixamorig:hips', 'wolf3d_hips', 'hips'],
      spine: ['mixamorig:spine', 'spine'],
      spine1: ['mixamorig:spine1', 'spine1'],
      spine2: ['mixamorig:spine2', 'spine2'],
      neck: ['mixamorig:neck', 'neck'],
      head: ['mixamorig:head', 'head'],
      lefteye: ['mixamorig:lefteye', 'eyel', 'wolf3d_eyel'],
      righteye: ['mixamorig:righteye', 'eyer', 'wolf3d_eyer'],
      leftshoulder: ['mixamorig:leftshoulder', 'leftshoulder'],
      rightshoulder: ['mixamorig:rightshoulder', 'rightshoulder'],
      leftarm: ['mixamorig:leftarm', 'leftarm'],
      rightarm: ['mixamorig:rightarm', 'rightarm'],
      leftforearm: ['mixamorig:leftforearm', 'leftforearm'],
      rightforearm: ['mixamorig:rightforearm', 'rightforearm'],
      lefthand: ['mixamorig:lefthand', 'lefthand', 'wolf3d_hand_l'],
      righthand: ['mixamorig:righthand', 'righthand', 'wolf3d_hand_r'],
      leftupleg: ['mixamorig:leftupleg', 'leftupleg'],
      rightupleg: ['mixamorig:rightupleg', 'rightupleg'],
      leftleg: ['mixamorig:leftleg', 'leftleg'],
      rightleg: ['mixamorig:rightleg', 'rightleg'],
      leftfoot: ['mixamorig:leftfoot', 'leftfoot'],
      rightfoot: ['mixamorig:rightfoot', 'rightfoot'],
      lefttoebase: ['mixamorig:lefttoebase', 'lefttoebase'],
      righttoebase: ['mixamorig:righttoebase', 'righttoebase'],
    };
    return map[baseNorm] || [];
  };

  // Retarget edilmiş klipleri üret ve doğrudan useAnimations'a ver
  const retargetedClips = useMemo(() => {
    if (!model?.scene) return [];
    const nameMap = new Map();
    model.scene.traverse((obj) => { if (obj && obj.name) nameMap.set(normalize(obj.name), obj.name); });
    const pickActual = (baseName) => {
      const baseNorm = normalize(baseName);
      let actual = nameMap.get(baseNorm);
      if (actual) return actual;
      for (const cand of manualCandidates(baseNorm)) {
        const cNorm = normalize(cand);
        const hit = nameMap.get(cNorm);
        if (hit) return hit;
      }
      for (const [norm, real] of nameMap.entries()) {
        if (norm.endsWith(baseNorm) || baseNorm.endsWith(norm)) return real;
      }
      return null;
    };
    const retarget = (clip) => {
      if (!clip) return null;
      const c = clip.clone();
      c.tracks = c.tracks.map((track) => {
        const parts = track.name.split('.');
        const base = parts.shift();
        const suffix = parts.join('.');
        const actual = pickActual(base);
        if (!actual) return track;
        const t = track.clone();
        t.name = `${actual}.${suffix}`;
        return t;
      });
      c.name = clip.name;
      return c;
    };
    const idle = retarget(idleRaw);
    const greet = retarget(greetRaw);
    return [idle, greet].filter(Boolean);
  }, [model, idleRaw, greetRaw]);

  const { actions, mixer } = useAnimations(retargetedClips, groupRef);

  // Manage playing Greeting action on demand
  const greetingPlayingRef = useRef(false);
  useEffect(() => {
    if (!actions || !mixer) return;
    const idle = actions['Idle'];
    const greet = actions['Greeting'];

    if (currentAnimation === 'Greeting' && greet && !greetingPlayingRef.current) {
      greetingPlayingRef.current = true;
      // If FBX greeting exists, play it once
      try {
        greet.reset();
        greet.setLoop(THREE.LoopOnce, 1);
        greet.clampWhenFinished = true;
        greet.fadeIn(0.2).play();
        if (idle) idle.fadeOut(0.2);
      } catch {}

      const onFinished = (e) => {
        if (e.action === greet) {
          try { greet.fadeOut(0.2); } catch {}
          try { if (idle) idle.reset().fadeIn(0.3).play(); } catch {}
          greetingPlayingRef.current = false;
          try { useAppStore.setState({ currentAnimation: 'Idle' }); } catch {}
          mixer.removeEventListener('finished', onFinished);
        }
      };
      mixer.addEventListener('finished', onFinished);

      // Also schedule procedural wave as a fallback if no greeting clip
      if (!greet) {
        try {
          const now = (typeof performance !== 'undefined' ? performance.now() : Date.now());
          waveUntilRef.current = now + 1800;
        } catch {}
        try { useAppStore.setState({ currentAnimation: 'Idle' }); } catch {}
      }
    }
  }, [currentAnimation, actions, mixer]);

  // If speaking starts, abort greeting and ensure Idle is ready
  useEffect(() => {
    if (!actions) return;
    const idle = actions['Idle'];
    const greet = actions['Greeting'];
    if (isSpeaking) {
      try { greet?.stop(); } catch {}
      greetingPlayingRef.current = false;
      // Force animation state back to Idle so the scheduler can re-trigger Greeting later
      try { useAppStore.setState({ currentAnimation: 'Idle' }); } catch {}
      // Ensure Idle stays active and weighted (no reset to avoid snapping)
      try {
        if (idle) {
          idle.enabled = true;
          idle.play();
          // If it was faded out by Greeting, bring it back quickly
          if (typeof idle.getEffectiveWeight === 'function') {
            if (idle.getEffectiveWeight() < 0.85) idle.fadeIn(0.2);
          } else {
            idle.fadeIn?.(0.2);
          }
        }
      } catch {}
    }
  }, [isSpeaking, actions]);

  // Wave için sağ el/önkol kemiğini tespit et (varsa)
  useEffect(() => {
    if (!model?.scene) return;
    let found = null;
    const candidates = ['righthand', 'rightwrist', 'handr', 'wolf3d_hand_r', 'mixamorig:righthand'];
    model.scene.traverse((obj) => {
      if (found || !obj?.name) return;
      const n = normalize(obj.name);
      if (candidates.some(c => n.includes(normalize(c)))) found = obj;
    });
    if (found) {
      waveBoneRef.current = found;
      waveBoneInitRef.current = found.rotation.clone();
    }
  }, [model]);

  // (Eski) retarget effect kaldırıldı; retargetedClips doğrudan useAnimations'a veriliyor.

  // Idle her zaman oynasın
  useEffect(() => {
    if (!actions) return;
    const idle = actions['Idle'];
    if (idle) {
      idle.reset().fadeIn(0.3).play();
      idle.setLoop(THREE.LoopRepeat, Infinity);
      idle.clampWhenFinished = false;
    }
  }, [actions]);



  // Ses oynatma ve konuşma durumu
  useEffect(() => {
    // önce var olan ses kaynağını temizle
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = '';
      audioRef.current = null;
    }

    if (!audioUrl) return;

    const audio = new Audio(audioUrl);
    try { audio.preload = 'auto'; } catch {}
    try { audio.crossOrigin = 'anonymous'; } catch {}
    audioRef.current = audio;
    // Basit wave efekti süresi (ms)
    // wave on speech removed

    // Konuşmayı başlat
    useAppStore.setState({ isSpeaking: true });

    audio.play().catch((err) => {
      console.error('Ses oynatma hatası:', err);
      useAppStore.setState({ isSpeaking: false });
    });

    audio.onplay = () => { cueIndexRef.current = 0; };

    audio.onended = () => { useAppStore.setState({ isSpeaking: false }); try { if (audioRef.current === audio) audioRef.current = null; } catch {} };
    audio.onerror = () => { try { audio.pause(); } catch {}; useAppStore.setState({ isSpeaking: false }); };
    audio.onstalled = () => { try { audio.pause(); } catch {}; useAppStore.setState({ isSpeaking: false }); };

    // Safety fallback: stop speaking even if 'ended' never fires
    let safetyTimer = setTimeout(() => {
      if (audioRef.current === audio && !audio.ended) {
        try { audio.pause(); } catch {}
        useAppStore.setState({ isSpeaking: false });
      }
    }, 20000);
    audio.onloadedmetadata = () => {
      try {
        if (isFinite(audio.duration) && audio.duration > 0) {
          clearTimeout(safetyTimer);
          safetyTimer = setTimeout(() => {
            if (audioRef.current === audio && !audio.ended) {
              try { audio.pause(); } catch {}
              useAppStore.setState({ isSpeaking: false });
            }
          }, (audio.duration + 1) * 1000);
        }
      } catch {}
    };

    return () => {
      audio.pause();
      try { clearTimeout(safetyTimer); } catch {}
    };
  }, [audioUrl, cuesJson]);

  // Safely parse lipsync JSON from cuesJson
  const parsedLipsync = useMemo(() => {
    try {
      if (!cuesJson) return null;
      if (typeof cuesJson === 'string') return JSON.parse(cuesJson);
      if (typeof cuesJson === 'object') return cuesJson;
      return null;
    } catch (e) {
      console.error('Lipsync JSON parse error:', e);
      return null;
    }
  }, [cuesJson]);

  // Keep track of current mouth cue index for robust progression
  const cueIndexRef = useRef(0);

  // Konuşmadan bağımsız: belirli aralıklarla (8-20 sn) Greeting tetikle
  useEffect(() => {
    let timer;
    const schedule = () => {
      const delay = 8000 + Math.random() * 12000;
      timer = setTimeout(() => {
        const st = useAppStore.getState();
        if (!st.isSpeaking) {
          useAppStore.setState({ currentAnimation: 'Greeting' });
          try { waveUntilRef.current = (typeof performance !== 'undefined' ? performance.now() : Date.now()) + 1200; } catch {}
        }
        schedule();
      }, delay);
    };
    schedule();
    return () => clearTimeout(timer);
  }, []);

  // Lipsync ve morph target güncellemeleri
  useFrame((state, delta) => {
    const speaking = !!(audioRef.current && !audioRef.current.paused && !audioRef.current.ended);
    // Keep Idle pose when speaking: freeze Idle at current time and continue applying bindings
    if (mixer) {
      if (speaking) {
        if (KEEP_IDLE_WHILE_SPEAKING) {
          try { actions?.['Idle'] && (actions['Idle'].paused = false); } catch {}
          mixer.update(delta);
        } else {
          try { actions?.['Idle'] && (actions['Idle'].paused = true); } catch {}
          mixer.update(0);
        }
      } else {
        try { actions?.['Idle'] && (actions['Idle'].paused = false); } catch {}
        mixer.update(delta);
      }
    }
    if (!groupRef.current || !model?.scene) return;

    // Prosedürel idle + wave fallback
    const t = state.clock.getElapsedTime();
    if (speaking) {
      groupRef.current.rotation.y = 0;
      // Ensure Idle action stays strongly weighted while speaking
      try {
        const idle = actions?.['Idle'];
        if (idle) {
          idle.enabled = true;
          idle.paused = false;
          if (typeof idle.setEffectiveWeight === 'function') {
            idle.setEffectiveWeight(1);
          } else {
            idle.weight = 1;
          }
          idle.play();
        }
      } catch {}
      if (waveBoneRef.current && waveBoneInitRef.current) {
        const r = waveBoneRef.current.rotation;
        r.x = THREE.MathUtils.lerp(r.x, waveBoneInitRef.current.x, 0.5);
        r.y = THREE.MathUtils.lerp(r.y, waveBoneInitRef.current.y, 0.5);
      } else {
        groupRef.current.rotation.z = 0;
      }
    } else {
    const baseSway = 0.02 * Math.sin(t * 0.8);
    const now = (typeof performance !== 'undefined' ? performance.now() : Date.now());
    const waving = !greetingPlayingRef.current && now < waveUntilRef.current;
    const wave = waving ? 0.4 * Math.sin(t * 6.0) : 0;
    groupRef.current.rotation.y = baseSway;
    // El sallama: uygun kemik varsa onu döndür, yoksa grup rotasyonuna küçük etki ver
    if (waveBoneRef.current && waveBoneInitRef.current) {
      const targetX = waving ? wave : 0;
      const targetY = waving ? wave * 0.5 : 0;
      const r = waveBoneRef.current.rotation;
      r.x = THREE.MathUtils.lerp(r.x, waveBoneInitRef.current.x + targetX, 0.3);
      r.y = THREE.MathUtils.lerp(r.y, waveBoneInitRef.current.y + targetY, 0.3);
    } else {
      groupRef.current.rotation.z = waving ? 0.1 * Math.sin(t * 4.0) : 0;
    }
    }

    // Mevcut ses zamanı
    const currentTime = audioRef.current ? audioRef.current.currentTime : 0;

    const scene = model.scene;

    // Tüm visemeleri 0'a doğru yumuşat
    scene.traverse((child) => {
      if (child.isMesh && child.morphTargetInfluences && child.morphTargetDictionary) {
        for (let i = 0; i < child.morphTargetInfluences.length; i++) {
          const current = child.morphTargetInfluences[i] || 0;
          child.morphTargetInfluences[i] = THREE.MathUtils.lerp(current, 0, 0.25);
        }
      }
    });

    
    // Random lipsync path while speaking
    if (speaking && RANDOM_LIPSYNC_WHILE_SPEAKING) {
      const nowMs = (typeof performance !== 'undefined' ? performance.now() : Date.now());
      if (nowMs >= nextMouthSwitchAtRef.current) {
        const keys = visemeKeysRef.current && visemeKeysRef.current.length
          ? visemeKeysRef.current
          : ['viseme_PP','viseme_kk','viseme_I','viseme_AA','viseme_O','viseme_U','viseme_FF','viseme_TH','viseme_E'];
        const filtered = keys.filter(k => !/viseme_sil/i.test(k));
        const pool = filtered.length ? filtered : keys;
        const pick = pool[Math.floor(Math.random() * pool.length)];
        randomMouthKeyRef.current = pick;
        nextMouthSwitchAtRef.current = nowMs + (90 + Math.random() * 110);
      }
      const activeKey = randomMouthKeyRef.current;
      if (activeKey) {
        scene.traverse((child) => {
          if (child.isMesh && child.morphTargetInfluences && child.morphTargetDictionary) {
            const dict = child.morphTargetDictionary;
            const keys = Object.keys(dict);
            const hit = dict[activeKey] !== undefined ? activeKey : keys.find(k => k.toLowerCase() === activeKey.toLowerCase());
            if (hit) {
              const idx = dict[hit];
              const cur = child.morphTargetInfluences[idx] || 0;
              child.morphTargetInfluences[idx] = THREE.MathUtils.lerp(cur, 0.85, 0.9);
            }
          }
        });
      }
      return;
    }

    if (!parsedLipsync || !parsedLipsync.mouthCues || !audioRef.current) return;

    // Aktif mouth cue'u robust ilerleyen index ile bul (epsilon toleranslı)
    const cues = parsedLipsync.mouthCues || [];
    if (!cues.length) return;
    let i = cueIndexRef.current;
    const eps = 0.005;
    while (i < cues.length - 1 && currentTime > (Number(cues[i].end) + eps)) i++;
    while (i > 0 && currentTime < (Number(cues[i].start) - eps)) i--;
    cueIndexRef.current = i;
    const activeCue = cues[i];
    if (currentTime < (Number(activeCue.start) - eps) || currentTime > (Number(activeCue.end) + eps)) return;
const letter = activeCue.value;

    // Aktif viseme'i 1.0'a doğru yumuşat
    scene.traverse((child) => {
      if (child.isMesh && child.morphTargetInfluences && child.morphTargetDictionary) {
        const idx = (()=>{
          const dict = child.morphTargetDictionary;
          const cands = (visemeCandidates[letter] || []);
          const keys = Object.keys(dict);
          for (let i = 0; i < cands.length; i++) {
            const cand = cands[i];
            if (dict[cand] !== undefined) return dict[cand];
            const foundKey = keys.find(k => k.toLowerCase() === cand.toLowerCase());
            if (foundKey) return dict[foundKey];
          }
          return undefined;
        })();
        if (idx !== undefined) {
          const current = child.morphTargetInfluences[idx] || 0;
          child.morphTargetInfluences[idx] = THREE.MathUtils.lerp(current, 1, 0.9);
        }
      }
    });

  });

  return (
    <group ref={groupRef} dispose={null}>
      {model && <primitive object={model.scene} />}
    </group>
  );

}
