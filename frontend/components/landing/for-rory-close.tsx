"use client";

import { motion } from "framer-motion";

export function ForRoryClose() {
  return (
    <section className="relative bg-black py-32 lg:py-48 flex items-center justify-center">
      <motion.div
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        transition={{ duration: 3 }}
        viewport={{ once: true, amount: 0.5 }}
        className="text-center"
      >
        <p className="text-4xl lg:text-6xl font-display text-white tracking-wide">
          For Rory.
        </p>
        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 0.3 }}
          transition={{ duration: 2, delay: 1.5 }}
          viewport={{ once: true }}
          className="text-sm font-mono text-white mt-6"
        >
          1999 - 2012
        </motion.p>
      </motion.div>
    </section>
  );
}
