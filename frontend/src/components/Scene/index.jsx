import { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import Avatar from '../Avatar';

export default function Scene() {
  return (
    <div style={{ width: '100%', height: '100%', minHeight: 0, minWidth: 0 }}>
      <Canvas
        shadows
        dpr={[1, 2]}
        camera={{ position: [0, 0, 5], fov: 35 }}
        gl={{ antialias: true }}
      >
        <color attach="background" args={['#4a5568']} />
        <ambientLight intensity={0.5} />
        <directionalLight
          position={[10, 10, 5]}
          intensity={1}
          castShadow
          shadow-mapSize-width={1024}
          shadow-mapSize-height={1024}
        />
        <Suspense fallback={null}>
          <Avatar />
        </Suspense>
        <OrbitControls makeDefault />
      </Canvas>
    </div>
  );
}