import { motion } from "framer-motion";
import { Check, X } from "lucide-react";

const promises = [
  { name: "plan9-kernel", constraint: "Plan 9 kernel image or QEMU config exists", kv: "OpenCog-Plan9", satisfied: true },
  { name: "plan9-cc", constraint: "Plan 9 C compiler (6c/8c) available", kv: "Plan 9 toolchain", satisfied: true },
  { name: "9p-listener", constraint: "9P2000 port 564 configured", kv: "plan9-devenv", satisfied: true },
  { name: "grid-compose", constraint: "plan9-registry in grid-compose.yml", kv: "plan9-devenv", satisfied: true },
  { name: "cognitive-ns", constraint: "/cognitive/ namespace defined", kv: "OpenCog-Plan9", satisfied: true },
  { name: "devenv-config", constraint: "PLAN9 root in environment", kv: "plan9-devenv", satisfied: true },
  { name: "autognosis-loop", constraint: "Verification in termrc", kv: "Autognosis", satisfied: false },
  { name: "temporal-levels", constraint: "9+ temporal levels defined", kv: "time-crystal-nn", satisfied: true },
];

export function PromiseSection() {
  const satisfied = promises.filter((p) => p.satisfied).length;
  const total = promises.length;
  const pct = Math.round((satisfied / total) * 100);

  return (
    <section id="promises" className="py-24 relative">
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-green-glow/20 to-transparent" />

      <div className="container">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="mb-16"
        >
          <span className="font-mono text-xs text-green-glow uppercase tracking-widest">
            Constraint Satisfaction
          </span>
          <h2 className="font-display font-bold text-4xl sm:text-5xl mt-3 mb-4">
            Promise-Lambda <span className="text-green-glow">Attention</span>
          </h2>
          <p className="text-muted-foreground max-w-2xl text-lg leading-relaxed">
            The kernel validates its configuration through 8 promises. Each promise is a lambda constraint
            that must be satisfied for the cognitive kernel to operate correctly.
          </p>
        </motion.div>

        {/* Status bar */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="glass-panel rounded-lg p-6 mb-8"
        >
          <div className="flex items-center justify-between mb-3">
            <span className="font-mono text-sm text-foreground">Kernel Validation Status</span>
            <span className="font-mono text-sm text-green-glow">{satisfied}/{total} promises satisfied ({pct}%)</span>
          </div>
          <div className="h-2 bg-void-lighter rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              whileInView={{ width: `${pct}%` }}
              viewport={{ once: true }}
              transition={{ duration: 1, ease: "easeOut" }}
              className="h-full bg-green-glow rounded-full"
            />
          </div>
        </motion.div>

        {/* Promise cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {promises.map((p, i) => (
            <motion.div
              key={p.name}
              initial={{ opacity: 0, y: 15 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: 0.05 * i }}
              className={`glass-panel rounded-lg p-4 border-l-2 ${
                p.satisfied ? "border-l-green-glow/60" : "border-l-destructive/60"
              } hover:box-glow-cyan transition-all duration-300`}
            >
              <div className="flex items-start gap-3">
                <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${
                  p.satisfied ? "bg-green-glow/20 text-green-glow" : "bg-destructive/20 text-destructive"
                }`}>
                  {p.satisfied ? <Check size={14} /> : <X size={14} />}
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-sm text-cyan-glow">{p.name}</span>
                    <span className="font-mono text-xs text-muted-foreground px-1.5 py-0.5 rounded bg-void-lighter/50">
                      {p.kv}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground">{p.constraint}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
