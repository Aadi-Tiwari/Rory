"use client";

import { Effects } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { Particles } from "./particles";
import { VignetteShader } from "./shaders/vignetteShader";

export function ParticleBackground() {
  return (
    <div className="absolute inset-0 z-0">
      <Canvas
        camera={{
          position: [1.26, 2.66, -1.82],
          fov: 50,
          near: 0.01,
          far: 300,
        }}
        style={{ background: "transparent" }}
        gl={{ alpha: true, antialias: false, powerPreference: "low-power", precision: "lowp" }}
        dpr={0.4}
        frameloop="always"
        performance={{ min: 0.2 }}
      >
        <color attach="background" args={["#000"]} />
        <Particles
          speed={0.4}
          aperture={1.79}
          focus={3.8}
          size={128}
          noiseScale={0.6}
          noiseIntensity={0.4}
          timeScale={0.5}
          pointSize={12.0}
          opacity={0.6}
          planeScale={10.0}
        />
        <Effects multisamping={0} disableGamma>
          {/* @ts-ignore */}
          <shaderPass
            args={[VignetteShader]}
            uniforms-darkness-value={1.5}
            uniforms-offset-value={0.4}
          />
        </Effects>
      </Canvas>
    </div>
  );
}
