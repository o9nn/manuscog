import { motion } from "framer-motion";

const GRID_IMG = "https://private-us-east-1.manuscdn.com/sessionFile/FDshEBmHlts6l0zq412iE5/sandbox/SAeb7OAxLYOBIAehkl9CvD-img-3_1771313824000_na1fn_Z3JpZC10b3BvbG9neQ.png?x-oss-process=image/resize,w_1920,h_1920/format,webp/quality,q_80&Expires=1798761600&Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9wcml2YXRlLXVzLWVhc3QtMS5tYW51c2Nkbi5jb20vc2Vzc2lvbkZpbGUvRkRzaEVCbUhsdHM2bDB6cTQxMmlFNS9zYW5kYm94L1NBZWI3T0F4TFlPQklBZWhrbDlDdkQtaW1nLTNfMTc3MTMxMzgyNDAwMF9uYTFmbl9aM0pwWkMxMGIzQnZiRzluZVEucG5nP3gtb3NzLXByb2Nlc3M9aW1hZ2UvcmVzaXplLHdfMTkyMCxoXzE5MjAvZm9ybWF0LHdlYnAvcXVhbGl0eSxxXzgwIiwiQ29uZGl0aW9uIjp7IkRhdGVMZXNzVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoxNzk4NzYxNjAwfX19XX0_&Key-Pair-Id=K2HSFNDJXOU9YS&Signature=Zqzz7~LeN62zxJvrn2gDQP4oMAkRrVl79Fzr63voAiXuOdKZ1mUlhNF6VemgWS2r0FZuz5uuaQenM-Em2dz0wCHiMLVi3Pxp6EChIgNyWCtsR6Z6ymFNEyaqLJXiGCaQS6RaC0pWZgRrNJnTUfiy1x0cduPNXmstAdAZnRbhCCj-YYpqZB9QOeGjcPQFK~978QSkzS83OmJu5bAt1J6OMsF00aiIIJ~yFnUyUekOhK4Ma1nbDi-UGhtyEi7q27Ey0V0BndsGC5W-Ll3ixroXs36aYQ-6p1T3gsNwaJqaUO43EldC2rxu5vufZAM2ZkSoHQYhtzEkLoEDj0JCVDlNJQ__";

const gridCmds = [
  { cmd: "plan9-grid start [--nodes N]", desc: "Start CPU server grid (default: 3)" },
  { cmd: "plan9-grid stop", desc: "Stop all nodes" },
  { cmd: "plan9-grid status", desc: "Show grid status" },
  { cmd: "plan9-grid connect <node-id>", desc: "Connect via 9P2000" },
  { cmd: "plan9-grid deploy <file.out>", desc: "Deploy executable to all nodes" },
  { cmd: "plan9-grid logs [node-id]", desc: "Tail logs" },
];

const partitions = [
  { server: "cpu0", partition: "Auth/Name + General knowledge", port: "564" },
  { server: "cpu1", partition: "Domain A (perception)", port: "565" },
  { server: "cpu2", partition: "Domain B (language)", port: "566" },
  { server: "cpu3", partition: "Domain C (reasoning)", port: "567" },
];

const topologies = [
  { name: "Star", desc: "Auth/name server coordinates all CPU servers. Simplest to deploy.", use: "Small grids (2-10 servers)" },
  { name: "Mesh", desc: "Every CPU server connects to every other. Maximum redundancy.", use: "High-availability deployments" },
  { name: "Hierarchical", desc: "Multi-level tree for large-scale deployments.", use: "Large grids (10+ servers)" },
];

export function GridSection() {
  return (
    <section id="grid" className="py-24 relative">
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-cyan-glow/20 to-transparent" />

      <div className="container">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="mb-16"
        >
          <span className="font-mono text-xs text-cyan-glow uppercase tracking-widest">
            Distributed Computing
          </span>
          <h2 className="font-display font-bold text-4xl sm:text-5xl mt-3 mb-4">
            CPU Server <span className="text-cyan-glow">Grid</span>
          </h2>
          <p className="text-muted-foreground max-w-2xl text-lg leading-relaxed">
            The distributed CPU server grid uses Docker Compose with QEMU-based Plan 9 instances.
            Scale horizontally by adding more CPU servers, each running cognitive service partitions.
          </p>
        </motion.div>

        {/* Grid topology image */}
        <motion.div
          initial={{ opacity: 0, scale: 0.97 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="glass-panel rounded-lg p-4 mb-12 overflow-hidden"
        >
          <img
            src={GRID_IMG}
            alt="Distributed CPU Server Grid Topology"
            className="w-full rounded max-h-[400px] object-contain"
            loading="lazy"
          />
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Grid topologies */}
          <div>
            <h3 className="font-heading font-semibold text-xl mb-4">Grid Topologies</h3>
            <div className="space-y-3">
              {topologies.map((t, i) => (
                <motion.div
                  key={t.name}
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4, delay: 0.1 * i }}
                  className="glass-panel rounded-lg p-4"
                >
                  <h4 className="font-mono text-sm text-cyan-glow mb-1">{t.name} Topology</h4>
                  <p className="text-sm text-muted-foreground mb-2">{t.desc}</p>
                  <span className="font-mono text-xs text-amber-glow">{t.use}</span>
                </motion.div>
              ))}
            </div>

            {/* Partitioned AtomSpace */}
            <h3 className="font-heading font-semibold text-xl mt-8 mb-4">Partitioned AtomSpace</h3>
            <div className="glass-panel rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left px-4 py-2 font-mono text-xs text-muted-foreground">Server</th>
                    <th className="text-left px-4 py-2 font-mono text-xs text-muted-foreground">Partition</th>
                    <th className="text-left px-4 py-2 font-mono text-xs text-muted-foreground">Port</th>
                  </tr>
                </thead>
                <tbody>
                  {partitions.map((p) => (
                    <tr key={p.server} className="border-b border-border/30 hover:bg-void-lighter/20 transition-colors">
                      <td className="px-4 py-2 font-mono text-cyan-glow">{p.server}</td>
                      <td className="px-4 py-2 text-muted-foreground">{p.partition}</td>
                      <td className="px-4 py-2 font-mono text-amber-glow">{p.port}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* CLI commands */}
          <div>
            <h3 className="font-heading font-semibold text-xl mb-4">Grid CLI</h3>
            <div className="code-block rounded-lg p-5">
              <div className="flex items-center gap-2 mb-4 pb-3 border-b border-border/50">
                <span className="w-3 h-3 rounded-full bg-green-glow/60" />
                <span className="font-mono text-xs text-muted-foreground">plan9-grid</span>
              </div>
              <div className="space-y-3">
                {gridCmds.map((c) => (
                  <div key={c.cmd}>
                    <div className="flex items-start gap-2">
                      <span className="text-green-glow shrink-0">$</span>
                      <span className="text-cyan-glow">{c.cmd}</span>
                    </div>
                    <p className="text-muted-foreground text-xs ml-5 mt-0.5">{c.desc}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Namespace composition example */}
            <h3 className="font-heading font-semibold text-xl mt-8 mb-4">Namespace Composition</h3>
            <div className="code-block rounded-lg p-5">
              <div className="flex items-center gap-2 mb-3 pb-3 border-b border-border/50">
                <span className="w-3 h-3 rounded-full bg-amber-glow/60" />
                <span className="font-mono text-xs text-muted-foreground">rc shell — union mount</span>
              </div>
              <pre className="text-sm leading-relaxed">
<span className="text-muted-foreground"># Create union of all CPU servers' atomspaces</span>{"\n"}
<span className="text-green-glow">for</span><span className="text-foreground">(cpu </span><span className="text-green-glow">in</span><span className="text-foreground"> cpu1 cpu2 cpu3) {"{"}</span>{"\n"}
{"    "}<span className="text-cyan-glow">import</span><span className="text-foreground"> $cpu /cognitive/atomspace /mnt/$cpu/atomspace</span>{"\n"}
{"    "}<span className="text-cyan-glow">bind</span><span className="text-amber-glow"> -a</span><span className="text-foreground"> /mnt/$cpu/atomspace /cognitive/atomspace</span>{"\n"}
<span className="text-foreground">{"}"}</span>{"\n"}
<span className="text-muted-foreground"># Now /cognitive/atomspace shows atoms from ALL servers</span>
              </pre>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
