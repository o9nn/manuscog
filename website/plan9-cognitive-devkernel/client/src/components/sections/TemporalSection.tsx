import { motion } from "framer-motion";

const TEMPORAL_IMG = "https://private-us-east-1.manuscdn.com/sessionFile/FDshEBmHlts6l0zq412iE5/sandbox/SAeb7OAxLYOBIAehkl9CvD-img-4_1771313826000_na1fn_dGVtcG9yYWwtcmluZ3M.png?x-oss-process=image/resize,w_1920,h_1920/format,webp/quality,q_80&Expires=1798761600&Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9wcml2YXRlLXVzLWVhc3QtMS5tYW51c2Nkbi5jb20vc2Vzc2lvbkZpbGUvRkRzaEVCbUhsdHM2bDB6cTQxMmlFNS9zYW5kYm94L1NBZWI3T0F4TFlPQklBZWhrbDlDdkQtaW1nLTRfMTc3MTMxMzgyNjAwMF9uYTFmbl9kR1Z0Y0c5eVlXd3RjbWx1WjNNLnBuZz94LW9zcy1wcm9jZXNzPWltYWdlL3Jlc2l6ZSx3XzE5MjAsaF8xOTIwL2Zvcm1hdCx3ZWJwL3F1YWxpdHkscV84MCIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTc5ODc2MTYwMH19fV19&Key-Pair-Id=K2HSFNDJXOU9YS&Signature=NTLKJCW199s0IlH5tC77dBzYpffzZFCp2mCJegB1xVhArRKMCYU80eZTceyg4ve9YTWBJ2Z5~LVDLpaVTgIigNat~KgByMqZ81fJVhRPhYMSmcLecBUzpitEaBBn8iwSIWgct32WWySez7ccBte2zc6WC3ZuvhACkY92vFuFl6AO4weWqrUBwA6EcicT2ePTw06pucY0w55UkXkfEzkP~H7QtBvJuqEcM2TxpAAg1IRrUwjOgJa0mfbCaREqh~Y-xuhPec4P9v0EtokD068G0gyYwo~8uBoFJmhothkpL1dhc7OApZEPX06GnHlSrLqxi7dOke1JIddMTmK~rAqkTA__";

const levels = [
  { level: 0, name: "atom-ops", period: "8ms", service: "AtomSpace CRUD", mechanism: "/srv file read/write", color: "bg-cyan-glow" },
  { level: 1, name: "pattern-match", period: "26ms", service: "Pattern matching", mechanism: "grep over /cognitive/atomspace", color: "bg-cyan-glow" },
  { level: 2, name: "inference-step", period: "52ms", service: "PLN inference", mechanism: "/cognitive/inference file server", color: "bg-cyan-glow" },
  { level: 3, name: "attention-tick", period: "110ms", service: "ECAN attention", mechanism: "/cognitive/attention agents", color: "bg-cyan-glow/80" },
  { level: 4, name: "learning-batch", period: "160ms", service: "MOSES learning", mechanism: "/cognitive/learning populations", color: "bg-amber-glow/70" },
  { level: 5, name: "namespace-sync", period: "250ms", service: "Namespace sync", mechanism: "mount/bind across CPU servers", color: "bg-amber-glow/80" },
  { level: 6, name: "grid-pulse", period: "330ms", service: "Grid heartbeat", mechanism: "/net/tcp keepalive", color: "bg-amber-glow" },
  { level: 7, name: "autognosis-obs", period: "500ms", service: "Autognosis observation", mechanism: "/proc introspection", color: "bg-amber-glow" },
  { level: 8, name: "self-image", period: "1000ms", service: "Self-image rebuild", mechanism: "Full namespace walk", color: "bg-amber-glow" },
];

export function TemporalSection() {
  return (
    <section id="temporal" className="py-24 relative">
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-amber-glow/20 to-transparent" />

      <div className="container">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="mb-16"
        >
          <span className="font-mono text-xs text-amber-glow uppercase tracking-widest">
            Time Crystal Architecture
          </span>
          <h2 className="font-display font-bold text-4xl sm:text-5xl mt-3 mb-4">
            Temporal <span className="text-amber-glow">Hierarchy</span>
          </h2>
          <p className="text-muted-foreground max-w-2xl text-lg leading-relaxed">
            The 9-level time crystal neuron architecture maps to kernel service scheduling.
            Each level operates at a different temporal frequency, from 8ms atom operations to 1-second self-image rebuilds.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">
          {/* Left: Temporal rings image */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="flex justify-center"
          >
            <div className="glass-panel rounded-lg p-6 max-w-md">
              <img
                src={TEMPORAL_IMG}
                alt="9-Level Temporal Hierarchy Rings"
                className="w-full rounded"
                loading="lazy"
              />
              <p className="text-xs text-muted-foreground mt-4 text-center font-mono">
                L0 (8ms) → L8 (1000ms) concentric temporal rings
              </p>
            </div>
          </motion.div>

          {/* Right: Level bars */}
          <div className="space-y-3">
            {levels.map((l, i) => (
              <motion.div
                key={l.level}
                initial={{ opacity: 0, x: 30 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: 0.05 * i }}
                className="glass-panel rounded-lg p-4 hover:box-glow-amber transition-all duration-300"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded border border-amber-glow/30 flex items-center justify-center shrink-0 bg-void/50">
                    <span className="font-mono text-amber-glow text-xs font-bold">L{l.level}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-mono text-sm text-foreground">{l.name}</span>
                      <span className="font-mono text-xs text-amber-glow">{l.period}</span>
                    </div>
                    {/* Period bar */}
                    <div className="h-1.5 bg-void-lighter rounded-full overflow-hidden mb-1.5">
                      <motion.div
                        initial={{ width: 0 }}
                        whileInView={{ width: `${Math.min(10 + l.level * 10, 100)}%` }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.8, delay: 0.1 * i }}
                        className={`h-full rounded-full ${l.color}`}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-muted-foreground">{l.service}</span>
                      <span className="text-xs text-muted-foreground font-mono hidden sm:inline">{l.mechanism}</span>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
