import { motion } from "framer-motion";
import { useState } from "react";

const NAMESPACE_IMG = "https://private-us-east-1.manuscdn.com/sessionFile/FDshEBmHlts6l0zq412iE5/sandbox/SAeb7OAxLYOBIAehkl9CvD-img-2_1771313829000_na1fn_bmFtZXNwYWNlLXRyZWU.png?x-oss-process=image/resize,w_1920,h_1920/format,webp/quality,q_80&Expires=1798761600&Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9wcml2YXRlLXVzLWVhc3QtMS5tYW51c2Nkbi5jb20vc2Vzc2lvbkZpbGUvRkRzaEVCbUhsdHM2bDB6cTQxMmlFNS9zYW5kYm94L1NBZWI3T0F4TFlPQklBZWhrbDlDdkQtaW1nLTJfMTc3MTMxMzgyOTAwMF9uYTFmbl9ibUZ0WlhOd1lXTmxMWFJ5WldVLnBuZz94LW9zcy1wcm9jZXNzPWltYWdlL3Jlc2l6ZSx3XzE5MjAsaF8xOTIwL2Zvcm1hdCx3ZWJwL3F1YWxpdHkscV84MCIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTc5ODc2MTYwMH19fV19&Key-Pair-Id=K2HSFNDJXOU9YS&Signature=FLALDFQez0bffu1ItNMgkQqk33QZqeiLHqaSbiyuXgUuFfq9GTt0GDo3PAFtRZD0jcxRbuxH3-WebKIg1g35mA3o-HkkduF7YSIx73bwZrFMuZd1J7zABDoWEl~Q3qqIltLwIhBwU3V4SsOuYV65FCzwFWcJIcjmFudXW7MuYJKb39IihbmHxaguUhw6n5-7m5Sq7Mr9ZwqxYrbW41Xo972MjsC6743ju2eSKonwvbbtLbflhKIlTbRsNMQROofU5ocnUILG29Q1mKln2MZ9ds1hbUJvDCYI4Cm1Z3vnzO4sZuml6jT06-Kl74TVRXUQrcqW5txQ1nLzjIbREuaIuw__";

interface NsNode {
  name: string;
  desc: string;
  children?: NsNode[];
}

const namespaceTree: NsNode[] = [
  {
    name: "atomspace",
    desc: "Knowledge graph storage",
    children: [
      { name: "atoms", desc: "ConceptNode, PredicateNode, LinkType instances" },
      { name: "types", desc: "Type hierarchy (inherits-from relations)" },
      { name: "indices", desc: "Hash indices for fast lookup" },
    ],
  },
  {
    name: "inference",
    desc: "PLN reasoning engine",
    children: [
      { name: "rules", desc: "ModusPonens, DeductionRule, etc." },
      { name: "queue", desc: "Pending inference tasks" },
      { name: "results", desc: "Cached inference results with truth values" },
    ],
  },
  {
    name: "attention",
    desc: "ECAN attention allocation",
    children: [
      { name: "bank", desc: "STI/LTI values per atom" },
      { name: "agents", desc: "HebbianUpdating, ImportanceSpreading" },
    ],
  },
  {
    name: "learning",
    desc: "MOSES evolutionary learning",
    children: [
      { name: "populations", desc: "Candidate program populations" },
      { name: "fitness", desc: "Fitness function configurations" },
    ],
  },
  {
    name: "temporal",
    desc: "Time crystal hierarchy",
    children: [
      { name: "levels", desc: "9 time crystal level configs" },
      { name: "phases", desc: "Current phase state per level" },
    ],
  },
  {
    name: "autognosis",
    desc: "Self-awareness engine",
    children: [
      { name: "images", desc: "Hierarchical self-images (L0, L1, L2+)" },
      { name: "insights", desc: "Meta-cognitive insight records" },
      { name: "metrics", desc: "Self-monitoring metric time series" },
    ],
  },
];

const p9Ops = [
  { op: "open", msg: "Topen", meaning: "Acquire handle to cognitive resource" },
  { op: "read", msg: "Tread", meaning: "Query atom value, rule, or metric" },
  { op: "write", msg: "Twrite", meaning: "Update atom truth value, submit task" },
  { op: "create", msg: "Tcreate", meaning: "Create new atom, rule, or agent" },
  { op: "remove", msg: "Tremove", meaning: "Delete atom or deactivate agent" },
  { op: "stat", msg: "Tstat", meaning: "Get atom metadata (type, STI, LTI)" },
  { op: "walk", msg: "Twalk", meaning: "Navigate namespace hierarchy" },
  { op: "clunk", msg: "Tclunk", meaning: "Release handle to cognitive resource" },
];

function TreeNode({ node, depth = 0 }: { node: NsNode; depth?: number }) {
  const [expanded, setExpanded] = useState(depth === 0);

  return (
    <div>
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 py-1.5 px-2 w-full text-left hover:bg-void-lighter/30 rounded transition-colors group"
      >
        <span className="text-cyan-glow font-mono text-xs w-4">
          {node.children ? (expanded ? "▾" : "▸") : "·"}
        </span>
        <span className="font-mono text-sm text-cyan-glow">{node.name}/</span>
        <span className="text-xs text-muted-foreground ml-2 hidden sm:inline">{node.desc}</span>
      </button>
      {expanded && node.children && (
        <div className="ml-6 border-l border-cyan-glow/10">
          {node.children.map((child) => (
            <TreeNode key={child.name} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

export function NamespaceSection() {
  return (
    <section id="namespace" className="py-24 relative">
      {/* Subtle top border */}
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
            9P2000 File Servers
          </span>
          <h2 className="font-display font-bold text-4xl sm:text-5xl mt-3 mb-4">
            Cognitive <span className="text-cyan-glow">Namespace</span>
          </h2>
          <p className="text-muted-foreground max-w-2xl text-lg leading-relaxed">
            In Plan 9, every resource is a file server. The cognitive namespace maps cognitive services
            to 9P2000 file trees that can be mounted, bound, and composed across CPU servers.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
          {/* Left: Interactive namespace tree */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="lg:col-span-3"
          >
            <div className="glass-panel rounded-lg p-5">
              <div className="flex items-center gap-2 mb-4 pb-3 border-b border-border">
                <span className="w-3 h-3 rounded-full bg-green-glow/60" />
                <span className="font-mono text-xs text-muted-foreground">/cognitive/</span>
                <span className="font-mono text-xs text-cyan-glow ml-auto">ls -lR</span>
              </div>
              <div className="space-y-0.5">
                {namespaceTree.map((node) => (
                  <TreeNode key={node.name} node={node} />
                ))}
              </div>
            </div>

            {/* 9P2000 operations table */}
            <div className="glass-panel rounded-lg overflow-hidden mt-6">
              <div className="px-5 py-3 border-b border-border">
                <h3 className="font-heading font-semibold text-sm">9P2000 Protocol Operations</h3>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border/50">
                    <th className="text-left px-5 py-2 font-mono text-xs text-muted-foreground">Op</th>
                    <th className="text-left px-5 py-2 font-mono text-xs text-muted-foreground">Message</th>
                    <th className="text-left px-5 py-2 font-mono text-xs text-muted-foreground">Cognitive Meaning</th>
                  </tr>
                </thead>
                <tbody>
                  {p9Ops.map((row) => (
                    <tr key={row.op} className="border-b border-border/30 hover:bg-void-lighter/20 transition-colors">
                      <td className="px-5 py-2 font-mono text-cyan-glow">{row.op}</td>
                      <td className="px-5 py-2 font-mono text-amber-glow text-xs">{row.msg}</td>
                      <td className="px-5 py-2 text-muted-foreground text-xs">{row.meaning}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>

          {/* Right: Namespace visualization image */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="lg:col-span-2"
          >
            <div className="glass-panel rounded-lg p-4 sticky top-24">
              <img
                src={NAMESPACE_IMG}
                alt="Cognitive Namespace Tree Visualization"
                className="w-full rounded"
                loading="lazy"
              />
              <p className="text-xs text-muted-foreground mt-3 text-center font-mono">
                /cognitive/ namespace hierarchy
              </p>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
