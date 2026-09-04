import { motion } from 'framer-motion';

export default function BackgroundBlobs() {
  return (
    <div style={{
      position: 'fixed',
      top: 0, left: 0, right: 0, bottom: 0,
      zIndex: -1,
      overflow: 'hidden',
      pointerEvents: 'none',
      background: 'linear-gradient(to bottom right, #0F0F10, #111112)'
    }}>
      {/* Blob 1: Amber — top-left */}
      <motion.div
        animate={{
          x: [0, 60, -30, 0],
          y: [0, -60, 30, 0],
          scale: [1, 1.15, 0.9, 1]
        }}
        transition={{
          duration: 22,
          repeat: Infinity,
          ease: "easeInOut"
        }}
        style={{
          position: 'absolute',
          top: '15%',
          left: '8%',
          width: '38vw',
          height: '38vw',
          background: 'radial-gradient(circle, rgba(245, 166, 35, 0.12) 0%, rgba(0,0,0,0) 70%)',
          borderRadius: '50%',
          filter: 'blur(60px)'
        }}
      />
      
      {/* Blob 2: Coral — mid-right */}
      <motion.div
        animate={{
          x: [0, -50, 30, 0],
          y: [0, 50, -30, 0],
          scale: [1, 1.1, 0.92, 1]
        }}
        transition={{
          duration: 26,
          repeat: Infinity,
          ease: "easeInOut"
        }}
        style={{
          position: 'absolute',
          top: '35%',
          right: '8%',
          width: '34vw',
          height: '34vw',
          background: 'radial-gradient(circle, rgba(255, 107, 87, 0.10) 0%, rgba(0,0,0,0) 70%)',
          borderRadius: '50%',
          filter: 'blur(60px)'
        }}
      />

      {/* Blob 3: Violet-Gray — bottom-center */}
      <motion.div
        animate={{
          x: [0, 35, -60, 0],
          y: [0, 35, -25, 0],
          scale: [1, 1.2, 0.92, 1]
        }}
        transition={{
          duration: 30,
          repeat: Infinity,
          ease: "easeInOut"
        }}
        style={{
          position: 'absolute',
          bottom: '-8%',
          left: '28%',
          width: '45vw',
          height: '45vw',
          background: 'radial-gradient(circle, rgba(140, 120, 160, 0.10) 0%, rgba(0,0,0,0) 70%)',
          borderRadius: '50%',
          filter: 'blur(80px)'
        }}
      />
    </div>
  );
}
