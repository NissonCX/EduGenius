'use client';

import React, { useEffect, useState } from 'react';
import { motion, useSpring } from 'framer-motion';

export interface AnimatedNumberProps {
  value: number;
  duration?: number;
  format?: (value: number) => string | number;
  decimals?: number;
  className?: string;
}

export function AnimatedNumber({
  value,
  duration = 800,
  format,
  decimals = 0,
  className = ''
}: AnimatedNumberProps) {
  const [displayValue, setDisplayValue] = useState(0);

  // 使用 spring 动画实现平滑过渡
  const spring = useSpring(displayValue, {
    duration: duration,
    bounce: 0,
    ease: [0.075, 0.82, 0.165, 1] // circOut easing
  });

  useEffect(() => {
    setDisplayValue(value);
  }, [value]);

  // 格式化显示值
  const formattedValue = format
    ? format(Math.round(spring.get() * Math.pow(10, decimals)) / Math.pow(10, decimals))
    : (Math.round(spring.get() * Math.pow(10, decimals)) / Math.pow(10, decimals)).toFixed(decimals);

  return (
    <motion.span
      className={className}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
    >
      {formattedValue}
    </motion.span>
  );
}
