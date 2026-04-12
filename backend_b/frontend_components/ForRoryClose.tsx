import { motion } from "framer-motion";

export default function ForRoryClose() {
  return (
    <div className="fixed inset-0 bg-black flex items-center justify-center z-50">
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 2.5 }}
        className="text-white text-3xl font-light tracking-wide"
      >
        For Rory.
      </motion.p>
    </div>
  );
}
