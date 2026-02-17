import { motion } from "framer-motion";

const COMPOSITION_IMG = "https://private-us-east-1.manuscdn.com/sessionFile/FDshEBmHlts6l0zq412iE5/sandbox/SAeb7OAxLYOBIAehkl9CvD-img-5_1771313822000_na1fn_Y29tcG9zaXRpb24tZmxvdw.png?x-oss-process=image/resize,w_1920,h_1920/format,webp/quality,q_80&Expires=1798761600&Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9wcml2YXRlLXVzLWVhc3QtMS5tYW51c2Nkbi5jb20vc2Vzc2lvbkZpbGUvRkRzaEVCbUhsdHM2bDB6cTQxMmlFNS9zYW5kYm94L1NBZWI3T0F4TFlPQklBZWhrbDlDdkQtaW1nLTVfMTc3MTMxMzgyMjAwMF9uYTFmbl9ZMjl0Y0c5emFYUnBiMjR0Wm14dmR3LnBuZz94LW9zcy1wcm9jZXNzPWltYWdlL3Jlc2l6ZSx3XzE5MjAsaF8xOTIwL2Zvcm1hdCx3ZWJwL3F1YWxpdHkscV84MCIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTc5ODc2MTYwMH19fV19&Key-Pair-Id=K2HSFNDJXOU9YS&Signature=vTx-kTwFVcGVl32tf7Cy~s8j~-o2QmQzEIHmdchZX7p~q7o0jBX32rEO-2l1F-VVujUoFJ0mtdNmTpaQBCiH0Wi5BGRQzca5ocnqjLJukhTv8Z9CqeeH1fMOx1VsyncC3cj2Q4OArf23J-bMXFmGcgeZhyFfB-b0qHC7ce2owl1uJCepWcFBsO1m5mXZT2Nc-vudvzYszLjwoBROF-ipORABJ1n6NXIeyI0PpjxEnMeNAXTbrqG724p4Bxlp1OxPxPOm5BFw5rGgJB5-wqDe9eY8ruL8O1iM0Q7GeHXNFPXD-WQJSS2BhH3iS1bTT~RElC9-o5uypYQjNQWsK1t01w__";

const layers = [
  {
    id: 0,
    name: "Infrastructure Substrate",
    source: "inferno-devcontainer → Plan 9 devenv",
    color: "text-cyan-glow",
    desc: "QEMU-based devcontainer with Plan 9/9front, acme IDE, CPU grid",
  },
  {
    id: 1,
    name: "Cognitive Enrichment",
    source: "manuscog-cognitive-devkernel",
    color: "text-cyan-glow",
    desc: "Promise-Lambda Attention, Cognitive FS, Temporal Hierarchy, Autognosis",
  },
  {
    id: 2,
    name: "Domain Transform",
    source: 'function-creator => "plan9-analogue"',
    color: "text-amber-glow",
    desc: "Maps every Inferno concept to its Plan 9 equivalent via 9P2000",
  },
  {
    id: 3,
    name: "Packaging",
    source: "skill-creator",
    color: "text-green-glow",
    desc: "SKILL.md, scripts, templates, references — deliverable skill",
  },
];

const transformTable = [
  { inferno: "emu (Inferno emulator)", plan9: "QEMU running Plan 9/9front" },
  { inferno: "Limbo language", plan9: "Plan 9 C (dialect of ANSI C)" },
  { inferno: "Dis VM bytecode", plan9: "Native executables (.out)" },
  { inferno: "Styx protocol", plan9: "9P2000 protocol" },
  { inferno: "Docker cluster", plan9: "QEMU VM grid / CPU servers" },
  { inferno: "Port 6666", plan9: "Port 564" },
];

export function CompositionSection() {
  return (
    <section id="composition" className="py-24 relative">
      <div className="container">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="mb-16"
        >
          <span className="font-mono text-xs text-amber-glow uppercase tracking-widest">
            Layer Architecture
          </span>
          <h2 className="font-display font-bold text-4xl sm:text-5xl mt-3 mb-4">
            Composition <span className="text-cyan-glow">Architecture</span>
          </h2>
          <p className="text-muted-foreground max-w-2xl text-lg leading-relaxed">
            Synthesized from a recursive composition of infrastructure, cognitive enrichment,
            domain transformation, and packaging — each layer building on the last.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">
          {/* Left: Composition flow image */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="relative"
          >
            <div className="glass-panel rounded-lg overflow-hidden p-4">
              <img
                src={COMPOSITION_IMG}
                alt="Composition Architecture Flow"
                className="w-full max-w-sm mx-auto rounded"
                loading="lazy"
              />
            </div>
          </motion.div>

          {/* Right: Layer cards */}
          <div className="space-y-4">
            {layers.map((layer, i) => (
              <motion.div
                key={layer.id}
                initial={{ opacity: 0, x: 30 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: 0.1 * i }}
                className="glass-panel rounded-lg p-5 hover:box-glow-cyan transition-all duration-300"
              >
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded border border-cyan-glow/30 flex items-center justify-center shrink-0 bg-void/50">
                    <span className="font-mono text-cyan-glow text-sm font-bold">L{layer.id}</span>
                  </div>
                  <div>
                    <h3 className="font-heading font-semibold text-lg">{layer.name}</h3>
                    <p className={`font-mono text-xs ${layer.color} mb-2`}>{layer.source}</p>
                    <p className="text-sm text-muted-foreground">{layer.desc}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Transform table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="mt-16"
        >
          <h3 className="font-heading font-semibold text-xl mb-6">
            Domain Transform: <span className="text-amber-glow">Inferno → Plan 9</span>
          </h3>
          <div className="glass-panel rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left px-5 py-3 font-mono text-xs text-muted-foreground uppercase tracking-wider">Inferno Component</th>
                  <th className="text-left px-5 py-3 font-mono text-xs text-muted-foreground uppercase tracking-wider">Plan 9 Analogue</th>
                </tr>
              </thead>
              <tbody>
                {transformTable.map((row, i) => (
                  <tr key={i} className="border-b border-border/50 hover:bg-void-lighter/30 transition-colors">
                    <td className="px-5 py-3 text-muted-foreground">{row.inferno}</td>
                    <td className="px-5 py-3 text-cyan-glow font-mono text-xs">{row.plan9}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
