import { motion } from "framer-motion";
import { useState, useEffect } from "react";

const selfImageLevels = [
  {
    level: 0,
    name: "Direct Observation",
    observes: "Promise satisfaction, temporal levels, namespace paths",
    icon: "🔍",
  },
  {
    level: 1,
    name: "Pattern Analysis",
    observes: "Configuration completeness, grid status",
    icon: "📊",
  },
  {
    level: 2,
    name: "Meta-Cognitive",
    observes: "Self-awareness quality, convergence factor",
    icon: "🧠",
  },
];

const skills = [
  { name: "inferno-devcontainer", rel: "Source infrastructure — transformed to Plan 9 analogue" },
  { name: "manuscog-cognitive-devkernel", rel: "Source cognitive architecture — enriches Plan 9 kernel" },
  { name: "opencog-inferno-kernel", rel: "Cognitive services — mapped to 9P2000 file servers" },
  { name: "promise-lambda-attention", rel: "Constraint mechanism — promise validation" },
  { name: "function-creator", rel: "Transform engine — Inferno → Plan 9 domain mapping" },
  { name: "tc", rel: "Source domain — file management → namespace operations" },
  { name: "time-crystal-nn", rel: "Source domain — temporal hierarchy architecture" },
  { name: "Autognosis", rel: "Self-awareness — /proc-based hierarchical self-image" },
  { name: "skill-infinity", rel: "Convergence — self-referential fixed point" },
];

function ConvergenceSimulation() {
  const [cycles, setCycles] = useState<{ cycle: number; score: number }[]>([]);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    if (!running) return;
    if (cycles.length >= 8) {
      setRunning(false);
      return;
    }

    const timer = setTimeout(() => {
      const baseScore = 0.625; // 5/8 promises satisfied
      const noise = (Math.random() - 0.5) * 0.001;
      const score = cycles.length === 0
        ? baseScore
        : cycles[cycles.length - 1].score + noise * (1 / (cycles.length + 1));

      setCycles((prev) => [...prev, { cycle: prev.length + 1, score }]);
    }, 600);

    return () => clearTimeout(timer);
  }, [running, cycles]);

  const converged = cycles.length >= 2 &&
    Math.abs(cycles[cycles.length - 1]?.score - cycles[cycles.length - 2]?.score) < 0.001;

  return (
    <div className="glass-panel rounded-lg p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-heading font-semibold text-sm">skill-infinity Convergence</h3>
        <button
          onClick={() => { setCycles([]); setRunning(true); }}
          className="px-3 py-1.5 text-xs font-mono rounded border border-cyan-glow/30 text-cyan-glow hover:bg-cyan-glow/10 transition-colors"
        >
          {running ? "Running..." : "Run Cycles"}
        </button>
      </div>

      {/* Convergence formula */}
      <div className="code-block rounded p-3 mb-4 text-xs">
        <span className="text-muted-foreground">|</span>
        <span className="text-cyan-glow">self_awareness</span>
        <span className="text-muted-foreground">(cycle_n) - </span>
        <span className="text-cyan-glow">self_awareness</span>
        <span className="text-muted-foreground">(cycle_</span>
        <span className="text-muted-foreground">{"{"}</span>
        <span className="text-muted-foreground">n-1</span>
        <span className="text-muted-foreground">{"}"}</span>
        <span className="text-muted-foreground">)| &lt; </span>
        <span className="text-amber-glow">0.001</span>
      </div>

      {/* Cycle results */}
      <div className="space-y-1.5 min-h-[120px]">
        {cycles.map((c) => (
          <motion.div
            key={c.cycle}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-3"
          >
            <span className="font-mono text-xs text-muted-foreground w-16">Cycle {c.cycle}:</span>
            <div className="flex-1 h-1.5 bg-void-lighter rounded-full overflow-hidden">
              <div
                className="h-full bg-cyan-glow rounded-full transition-all duration-500"
                style={{ width: `${c.score * 100}%` }}
              />
            </div>
            <span className="font-mono text-xs text-cyan-glow w-20 text-right">{c.score.toFixed(6)}</span>
          </motion.div>
        ))}
        {converged && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-3 px-3 py-2 rounded bg-green-glow/10 border border-green-glow/20"
          >
            <span className="font-mono text-xs text-green-glow">
              Fixed point reached — self-improvement converged
            </span>
          </motion.div>
        )}
      </div>
    </div>
  );
}

export function AutognosisSection() {
  return (
    <section id="autognosis" className="py-24 relative">
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
            Self-Awareness Engine
          </span>
          <h2 className="font-display font-bold text-4xl sm:text-5xl mt-3 mb-4">
            Autognosis <span className="text-amber-glow">Self-Image</span>
          </h2>
          <p className="text-muted-foreground max-w-2xl text-lg leading-relaxed">
            Three hierarchical levels of self-monitoring mapped to Plan 9's /proc filesystem.
            The system converges to a fixed point when self-awareness stabilizes.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Self-image levels */}
          <div>
            <h3 className="font-heading font-semibold text-xl mb-4">Hierarchical Self-Image</h3>
            <div className="space-y-4 mb-8">
              {selfImageLevels.map((l, i) => (
                <motion.div
                  key={l.level}
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4, delay: 0.1 * i }}
                  className="glass-panel rounded-lg p-5 hover:box-glow-amber transition-all duration-300"
                >
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded border border-amber-glow/30 flex items-center justify-center shrink-0 bg-void/50">
                      <span className="font-mono text-amber-glow text-xs font-bold">L{l.level}</span>
                    </div>
                    <div>
                      <h4 className="font-heading font-semibold text-sm mb-1">{l.name}</h4>
                      <p className="text-xs text-muted-foreground">{l.observes}</p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>

            {/* /proc filesystem */}
            <h3 className="font-heading font-semibold text-xl mb-4">Plan 9 /proc Substrate</h3>
            <div className="code-block rounded-lg p-5">
              <pre className="text-sm leading-relaxed">
<span className="text-cyan-glow">/proc/</span><span className="text-amber-glow">&lt;pid&gt;</span><span className="text-cyan-glow">/</span>{"\n"}
<span className="text-muted-foreground">├── </span><span className="text-foreground">ctl</span><span className="text-muted-foreground">        # Process control</span>{"\n"}
<span className="text-muted-foreground">├── </span><span className="text-foreground">status</span><span className="text-muted-foreground">     # Process status line</span>{"\n"}
<span className="text-muted-foreground">├── </span><span className="text-foreground">note</span><span className="text-muted-foreground">       # Send notes (signals)</span>{"\n"}
<span className="text-muted-foreground">├── </span><span className="text-foreground">mem</span><span className="text-muted-foreground">        # Process memory</span>{"\n"}
<span className="text-muted-foreground">├── </span><span className="text-foreground">text</span><span className="text-muted-foreground">       # Executable text</span>{"\n"}
<span className="text-muted-foreground">├── </span><span className="text-foreground">fd</span><span className="text-muted-foreground">         # Open file descriptors</span>{"\n"}
<span className="text-muted-foreground">└── </span><span className="text-cyan-glow">ns</span><span className="text-muted-foreground">         # Process namespace</span>
              </pre>
            </div>
          </div>

          {/* Convergence simulation + composition */}
          <div>
            <ConvergenceSimulation />

            {/* Skill composition table */}
            <h3 className="font-heading font-semibold text-xl mt-8 mb-4">Skill Composition</h3>
            <div className="glass-panel rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left px-4 py-2 font-mono text-xs text-muted-foreground">Skill</th>
                    <th className="text-left px-4 py-2 font-mono text-xs text-muted-foreground">Relationship</th>
                  </tr>
                </thead>
                <tbody>
                  {skills.map((s) => (
                    <tr key={s.name} className="border-b border-border/30 hover:bg-void-lighter/20 transition-colors">
                      <td className="px-4 py-2 font-mono text-cyan-glow text-xs">{s.name}</td>
                      <td className="px-4 py-2 text-muted-foreground text-xs">{s.rel}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
