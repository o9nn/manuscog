import { motion } from "framer-motion";
import { Monitor, Terminal, Server, Cpu, Globe, Shield } from "lucide-react";

const components = [
  { icon: Cpu, name: "Plan 9 / 9front", desc: "Full system via QEMU (cpu, rc, mk, acme)" },
  { icon: Monitor, name: "acme IDE", desc: "Plan 9 native programmer's IDE" },
  { icon: Terminal, name: "Grid CLI", desc: "plan9-grid for start/stop/status/connect" },
  { icon: Terminal, name: "Build CLI", desc: "plan9-build for compile/run/check/clean" },
  { icon: Globe, name: "Grid Monitor", desc: "Flask dashboard on port 9090" },
  { icon: Server, name: "9P2000 Networking", desc: "Ports 564-566 for distributed namespaces" },
];

const ports = [
  { port: "564-566", service: "9P2000 listeners (one per grid node)", proto: "TCP" },
  { port: "8080", service: "Plan 9 web interface", proto: "HTTP" },
  { port: "9090", service: "Grid monitor dashboard", proto: "HTTP" },
];

const ides = [
  { name: "VS Code", launch: "Automatic via devcontainer", best: "Modern editing, extensions, tasks" },
  { name: "acme", launch: "9 acme /workspace/src", best: "Native Plan 9 mouse-driven IDE" },
  { name: "sam", launch: "9 sam file.c", best: "Structural regex editing" },
];

const plan9CDiffs = [
  { feature: "Headers", plan9: '#include <u.h>, <libc.h>', ansi: '#include <stdio.h>' },
  { feature: "Print", plan9: 'print("hello\\n")', ansi: 'printf("hello\\n")' },
  { feature: "Main", plan9: "void main(void)", ansi: "int main(void)" },
  { feature: "Exit", plan9: "exits(0)", ansi: "exit(0)" },
  { feature: "Memory", plan9: "mallocz(n, 1)", ansi: "calloc(1, n)" },
];

export function DevEnvSection() {
  return (
    <section id="devenv" className="py-24 relative">
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
            QEMU Devcontainer
          </span>
          <h2 className="font-display font-bold text-4xl sm:text-5xl mt-3 mb-4">
            Development <span className="text-cyan-glow">Environment</span>
          </h2>
          <p className="text-muted-foreground max-w-2xl text-lg leading-relaxed">
            A complete Plan 9 development setup via QEMU, with plan9port tools, distributed CPU server grid support,
            and CLI tools — all inside a devcontainer.
          </p>
        </motion.div>

        {/* Component grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-12">
          {components.map((c, i) => (
            <motion.div
              key={c.name}
              initial={{ opacity: 0, y: 15 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: 0.05 * i }}
              className="glass-panel rounded-lg p-5 hover:box-glow-cyan transition-all duration-300 group"
            >
              <c.icon size={24} className="text-cyan-glow mb-3 group-hover:scale-110 transition-transform" />
              <h3 className="font-heading font-semibold text-sm mb-1">{c.name}</h3>
              <p className="text-xs text-muted-foreground">{c.desc}</p>
            </motion.div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Port forwarding */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
          >
            <h3 className="font-heading font-semibold text-xl mb-4 flex items-center gap-2">
              <Shield size={18} className="text-cyan-glow" />
              Port Forwarding
            </h3>
            <div className="glass-panel rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left px-4 py-2 font-mono text-xs text-muted-foreground">Port</th>
                    <th className="text-left px-4 py-2 font-mono text-xs text-muted-foreground">Service</th>
                    <th className="text-left px-4 py-2 font-mono text-xs text-muted-foreground">Proto</th>
                  </tr>
                </thead>
                <tbody>
                  {ports.map((p) => (
                    <tr key={p.port} className="border-b border-border/30 hover:bg-void-lighter/20 transition-colors">
                      <td className="px-4 py-2 font-mono text-amber-glow">{p.port}</td>
                      <td className="px-4 py-2 text-muted-foreground">{p.service}</td>
                      <td className="px-4 py-2 font-mono text-cyan-glow text-xs">{p.proto}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* IDE options */}
            <h3 className="font-heading font-semibold text-xl mt-8 mb-4">IDE Options</h3>
            <div className="glass-panel rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left px-4 py-2 font-mono text-xs text-muted-foreground">IDE</th>
                    <th className="text-left px-4 py-2 font-mono text-xs text-muted-foreground">Launch</th>
                    <th className="text-left px-4 py-2 font-mono text-xs text-muted-foreground">Best For</th>
                  </tr>
                </thead>
                <tbody>
                  {ides.map((ide) => (
                    <tr key={ide.name} className="border-b border-border/30 hover:bg-void-lighter/20 transition-colors">
                      <td className="px-4 py-2 font-mono text-cyan-glow">{ide.name}</td>
                      <td className="px-4 py-2 font-mono text-xs text-muted-foreground">{ide.launch}</td>
                      <td className="px-4 py-2 text-muted-foreground text-xs">{ide.best}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>

          {/* Plan 9 C differences */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <h3 className="font-heading font-semibold text-xl mb-4">Plan 9 C vs ANSI C</h3>
            <div className="glass-panel rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left px-4 py-2 font-mono text-xs text-muted-foreground">Feature</th>
                    <th className="text-left px-4 py-2 font-mono text-xs text-muted-foreground">Plan 9 C</th>
                    <th className="text-left px-4 py-2 font-mono text-xs text-muted-foreground">ANSI C</th>
                  </tr>
                </thead>
                <tbody>
                  {plan9CDiffs.map((d) => (
                    <tr key={d.feature} className="border-b border-border/30 hover:bg-void-lighter/20 transition-colors">
                      <td className="px-4 py-2 text-muted-foreground">{d.feature}</td>
                      <td className="px-4 py-2 font-mono text-cyan-glow text-xs">{d.plan9}</td>
                      <td className="px-4 py-2 font-mono text-muted-foreground text-xs">{d.ansi}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Quick start */}
            <h3 className="font-heading font-semibold text-xl mt-8 mb-4">Quick Start</h3>
            <div className="code-block rounded-lg p-5">
              <div className="flex items-center gap-2 mb-3 pb-3 border-b border-border/50">
                <span className="w-3 h-3 rounded-full bg-green-glow/60" />
                <span className="font-mono text-xs text-muted-foreground">plan9-build</span>
              </div>
              <pre className="text-sm leading-relaxed">
<span className="text-muted-foreground"># Compile a Plan 9 C program</span>{"\n"}
<span className="text-green-glow">$</span> <span className="text-cyan-glow">plan9-build compile</span> <span className="text-foreground">src/cogkernel.c</span>{"\n"}
{"\n"}
<span className="text-muted-foreground"># Compile and run</span>{"\n"}
<span className="text-green-glow">$</span> <span className="text-cyan-glow">plan9-build run</span> <span className="text-foreground">src/cogkernel.c</span>{"\n"}
{"\n"}
<span className="text-muted-foreground"># Start the grid</span>{"\n"}
<span className="text-green-glow">$</span> <span className="text-cyan-glow">plan9-grid start</span> <span className="text-amber-glow">--nodes 5</span>
              </pre>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
