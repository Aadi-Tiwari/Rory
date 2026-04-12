import { motion } from "framer-motion";

interface Props {
  trend: number[];
  driftAlert: boolean;
}

export default function ClusterDriftSparkline({ trend, driftAlert }: Props) {
  if (!trend || trend.length === 0) return null;

  const width = 200;
  const height = 40;
  const max = Math.max(...trend, 1);
  const points = trend
    .map((v, i) => {
      const x = trend.length === 1 ? width / 2 : (i / (trend.length - 1)) * width;
      const y = height - (v / max) * height;
      return `${x},${y}`;
    })
    .join(" ");

  const gradientStops = trend.map((v, i) => {
    const offset = trend.length === 1 ? 50 : (i / (trend.length - 1)) * 100;
    const red = Math.floor(v * 255);
    const green = Math.floor((1 - v) * 180);
    return (
      <stop
        key={i}
        offset={`${offset}%`}
        stopColor={`rgb(${red}, ${green}, 60)`}
      />
    );
  });

  return (
    <div className="mt-2">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-slate-500">Trajectory</span>
        {driftAlert && (
          <motion.span
            animate={{ opacity: [1, 0.5, 1] }}
            transition={{ duration: 1.2, repeat: Infinity }}
            className="text-xs font-semibold text-red-600"
          >
            ⚠ Accelerating
          </motion.span>
        )}
      </div>
      <svg width={width} height={height} className="block">
        <defs>
          <linearGradient id="driftGrad" x1="0" y1="0" x2="1" y2="0">
            {gradientStops}
          </linearGradient>
        </defs>
        {trend.length > 1 ? (
          <motion.polyline
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1.2, ease: "easeOut" }}
            points={points}
            fill="none"
            stroke="url(#driftGrad)"
            strokeWidth={2.5}
            strokeLinecap="round"
          />
        ) : (
          <circle
            cx={width / 2}
            cy={height / 2}
            r={4}
            fill={`rgb(${Math.floor(trend[0] * 255)}, ${Math.floor((1 - trend[0]) * 180)}, 60)`}
          />
        )}
      </svg>
      {trend.length === 1 && (
        <span className="text-[10px] text-slate-400">first visit</span>
      )}
    </div>
  );
}
