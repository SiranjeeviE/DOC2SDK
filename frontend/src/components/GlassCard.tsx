import { motion, type HTMLMotionProps } from 'framer-motion';
import { type CSSProperties, type ReactNode } from 'react';

interface GlassCardProps extends Omit<HTMLMotionProps<'div'>, 'style'> {
  children: ReactNode;
  style?: CSSProperties;
}

export default function GlassCard({ children, style, ...rest }: GlassCardProps) {
  return (
    <motion.div
      className="glass-card"
      whileHover={{
        borderColor: 'rgba(255, 255, 255, 0.20)',
      }}
      transition={{ duration: 0.18, ease: 'easeOut' }}
      style={style}
      {...rest}
    >
      {children}
    </motion.div>
  );
}
