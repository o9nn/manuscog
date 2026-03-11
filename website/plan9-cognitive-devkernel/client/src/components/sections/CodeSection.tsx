import { motion } from "framer-motion";
import { useState, useMemo } from "react";

const codeFiles = [
  {
    name: "cogkernel.c",
    label: "Cognitive Kernel Demo",
    lines: [
      { text: '#include <u.h>', type: 'include' },
      { text: '#include <libc.h>', type: 'include' },
      { text: '', type: 'blank' },
      { text: '/* Truth value for atoms */', type: 'comment' },
      { text: 'typedef struct TruthValue TruthValue;', type: 'code' },
      { text: 'struct TruthValue {', type: 'code' },
      { text: '    double strength;', type: 'code' },
      { text: '    double confidence;', type: 'code' },
      { text: '};', type: 'code' },
      { text: '', type: 'blank' },
      { text: '/* Check if a cognitive namespace path is mounted */', type: 'comment' },
      { text: 'int', type: 'code' },
      { text: 'nsmounted(char *path)', type: 'code' },
      { text: '{', type: 'code' },
      { text: '    Dir *d;', type: 'code' },
      { text: '    d = dirstat(path);', type: 'code' },
      { text: '    if(d == nil)', type: 'code' },
      { text: '        return 0;', type: 'code' },
      { text: '    free(d);', type: 'code' },
      { text: '    return 1;', type: 'code' },
      { text: '}', type: 'code' },
      { text: '', type: 'blank' },
      { text: 'void', type: 'code' },
      { text: 'main(int, char**)', type: 'code' },
      { text: '{', type: 'code' },
      { text: '    TruthValue tv;', type: 'code' },
      { text: '    char *services[] = {', type: 'code' },
      { text: '        "/cognitive/atomspace",', type: 'string' },
      { text: '        "/cognitive/inference",', type: 'string' },
      { text: '        "/cognitive/attention",', type: 'string' },
      { text: '        "/cognitive/learning",', type: 'string' },
      { text: '    };', type: 'code' },
      { text: '    int i;', type: 'code' },
      { text: '', type: 'blank' },
      { text: '    print("+==========================================+\\n");', type: 'code' },
      { text: '    print("|  OpenCog-Plan9 Cognitive Kernel Demo      |\\n");', type: 'code' },
      { text: '    print("+==========================================+\\n\\n");', type: 'code' },
      { text: '', type: 'blank' },
      { text: '    /* Demonstrate AtomSpace operations */', type: 'comment' },
      { text: '    tv = (TruthValue){1.0, 0.9};', type: 'code' },
      { text: '    print("[1] ConceptNode \'cat\' <%.2f, %.2f>\\n",', type: 'code' },
      { text: '        tv.strength, tv.confidence);', type: 'code' },
      { text: '', type: 'blank' },
      { text: '    /* Check cognitive services */', type: 'comment' },
      { text: '    print("\\n[2] Cognitive services status:\\n");', type: 'code' },
      { text: '    for(i = 0; i < nelem(services); i++){', type: 'code' },
      { text: '        if(nsmounted(services[i]))', type: 'code' },
      { text: '            print("  + %s -- active\\n", services[i]);', type: 'code' },
      { text: '        else', type: 'code' },
      { text: '            print("  o %s -- not mounted\\n", services[i]);', type: 'code' },
      { text: '    }', type: 'code' },
      { text: '', type: 'blank' },
      { text: '    exits(nil);', type: 'code' },
      { text: '}', type: 'code' },
    ],
  },
  {
    name: "cogkernel_autognosis.c",
    label: "Autognosis Module",
    lines: [
      { text: '#include <u.h>', type: 'include' },
      { text: '#include <libc.h>', type: 'include' },
      { text: '', type: 'blank' },
      { text: '/* Temporal hierarchy levels */', type: 'comment' },
      { text: 'enum {', type: 'code' },
      { text: '    LEVEL_ATOM_OPS      = 0,   /* 8ms */', type: 'code' },
      { text: '    LEVEL_PATTERN_MATCH = 1,   /* 26ms */', type: 'code' },
      { text: '    LEVEL_INFERENCE     = 2,   /* 52ms */', type: 'code' },
      { text: '    LEVEL_ATTENTION     = 3,   /* 110ms */', type: 'code' },
      { text: '    LEVEL_LEARNING      = 4,   /* 160ms */', type: 'code' },
      { text: '    LEVEL_NAMESPACE     = 5,   /* 250ms */', type: 'code' },
      { text: '    LEVEL_GRID          = 6,   /* 330ms */', type: 'code' },
      { text: '    LEVEL_OBSERVATION   = 7,   /* 500ms */', type: 'code' },
      { text: '    LEVEL_SELF_IMAGE    = 8,   /* 1000ms */', type: 'code' },
      { text: '    NUM_LEVELS          = 9,', type: 'code' },
      { text: '};', type: 'code' },
      { text: '', type: 'blank' },
      { text: 'int level_period_ms[] = {', type: 'code' },
      { text: '    8, 26, 52, 110, 160, 250, 330, 500, 1000', type: 'code' },
      { text: '};', type: 'code' },
      { text: '', type: 'blank' },
      { text: '/* Self-image data structure */', type: 'comment' },
      { text: 'typedef struct SelfImage SelfImage;', type: 'code' },
      { text: 'struct SelfImage {', type: 'code' },
      { text: '    int level;', type: 'code' },
      { text: '    double confidence;', type: 'code' },
      { text: '    char hash[17];', type: 'code' },
      { text: '};', type: 'code' },
      { text: '', type: 'blank' },
      { text: '/* Observer process: collects metrics at L7 */', type: 'comment' },
      { text: 'void', type: 'code' },
      { text: 'observe(int pipefd)', type: 'code' },
      { text: '{', type: 'code' },
      { text: '    for(;;){', type: 'code' },
      { text: '        sleep(level_period_ms[LEVEL_OBSERVATION]);', type: 'code' },
      { text: '        /* Collect cognitive namespace metrics */', type: 'comment' },
      { text: '    }', type: 'code' },
      { text: '}', type: 'code' },
      { text: '', type: 'blank' },
      { text: '/* Build self-image from observations */', type: 'comment' },
      { text: 'void', type: 'code' },
      { text: 'build_self_image(int pipefd)', type: 'code' },
      { text: '{', type: 'code' },
      { text: '    for(;;){', type: 'code' },
      { text: '        sleep(level_period_ms[LEVEL_SELF_IMAGE]);', type: 'code' },
      { text: '        /* Level 0: Direct observation */', type: 'comment' },
      { text: '        /* Level 1: Pattern analysis */', type: 'comment' },
      { text: '        /* Level 2: Meta-cognitive */', type: 'comment' },
      { text: '    }', type: 'code' },
      { text: '}', type: 'code' },
    ],
  },
  {
    name: "mkfile",
    label: "Build Configuration",
    lines: [
      { text: '</$PLAN9/src/mkmk.proto', type: 'include' },
      { text: '', type: 'blank' },
      { text: 'TARG=cogkernel', type: 'code' },
      { text: 'OFILES=\\', type: 'code' },
      { text: '    cogkernel.$O\\', type: 'code' },
      { text: '    cogkernel_autognosis.$O\\', type: 'code' },
      { text: '', type: 'blank' },
      { text: '</usr/local/plan9/src/mkone', type: 'include' },
      { text: '', type: 'blank' },
      { text: '# Build cognitive kernel', type: 'comment' },
      { text: 'all:V:', type: 'code' },
      { text: '    mk cogkernel', type: 'string' },
      { text: '    mk cogkernel_autognosis', type: 'string' },
      { text: '', type: 'blank' },
      { text: '# Deploy to grid', type: 'comment' },
      { text: 'deploy:V:', type: 'code' },
      { text: '    plan9-grid deploy cogkernel.out', type: 'string' },
      { text: '    plan9-grid deploy cogkernel_autognosis.out', type: 'string' },
      { text: '', type: 'blank' },
      { text: '# Run validation', type: 'comment' },
      { text: 'validate:V:', type: 'code' },
      { text: '    python3 cognitive_plan9kernel.py validate .', type: 'string' },
      { text: '', type: 'blank' },
      { text: 'clean:V:', type: 'code' },
      { text: '    rm -f *.[68] *.out', type: 'string' },
    ],
  },
];

const keywords = new Set([
  'void', 'int', 'char', 'double', 'struct', 'typedef', 'enum',
  'for', 'if', 'else', 'switch', 'case', 'return', 'const', 'static',
]);

const builtins = new Set([
  'print', 'exits', 'sysfatal', 'rfork', 'pipe', 'close', 'sleep',
  'free', 'nelem', 'dirstat', 'mallocz', 'nsmounted', 'nil',
  'RFPROC', 'RFMEM', 'LEVEL_ATOM_OPS', 'LEVEL_PATTERN_MATCH',
  'LEVEL_INFERENCE', 'LEVEL_ATTENTION', 'LEVEL_LEARNING',
  'LEVEL_NAMESPACE', 'LEVEL_GRID', 'LEVEL_OBSERVATION',
  'LEVEL_SELF_IMAGE', 'NUM_LEVELS',
]);

function tokenize(text: string, type: string) {
  if (type === 'comment') return <span className="text-muted-foreground/60 italic">{text}</span>;
  if (type === 'include') return <span className="text-green-glow">{text}</span>;
  if (type === 'string') return <span className="text-green-glow">{text}</span>;
  if (type === 'blank') return <span>{"\u00A0"}</span>;

  // Tokenize code lines
  const tokens: React.ReactNode[] = [];
  const regex = /(\s+|[{}();,=<>*\[\]&|!+\-\/\\.]|"[^"]*"|'[^']*'|\/\*.*?\*\/|\w+)/g;
  let match;
  let key = 0;

  while ((match = regex.exec(text)) !== null) {
    const token = match[0];
    if (token.startsWith('"') || token.startsWith("'")) {
      tokens.push(<span key={key++} className="text-green-glow">{token}</span>);
    } else if (token.startsWith('/*')) {
      tokens.push(<span key={key++} className="text-muted-foreground/60 italic">{token}</span>);
    } else if (keywords.has(token)) {
      tokens.push(<span key={key++} className="text-amber-glow">{token}</span>);
    } else if (builtins.has(token)) {
      tokens.push(<span key={key++} className="text-cyan-glow">{token}</span>);
    } else if (/^\d/.test(token)) {
      tokens.push(<span key={key++} className="text-amber-glow">{token}</span>);
    } else {
      tokens.push(<span key={key++}>{token}</span>);
    }
  }

  return <>{tokens}</>;
}

function CodeViewer({ lines }: { lines: { text: string; type: string }[] }) {
  return (
    <div className="p-5 max-h-[500px] overflow-y-auto">
      <pre className="text-sm leading-relaxed">
        {lines.map((line, i) => (
          <div key={i} className="flex">
            <span className="text-muted-foreground/40 w-8 text-right mr-4 select-none shrink-0 text-xs leading-relaxed">
              {i + 1}
            </span>
            <span>{tokenize(line.text, line.type)}</span>
          </div>
        ))}
      </pre>
    </div>
  );
}

export function CodeSection() {
  const [activeFile, setActiveFile] = useState(0);

  return (
    <section id="code" className="py-24 relative">
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
            Plan 9 C Source
          </span>
          <h2 className="font-display font-bold text-4xl sm:text-5xl mt-3 mb-4">
            Kernel <span className="text-green-glow">Source Code</span>
          </h2>
          <p className="text-muted-foreground max-w-2xl text-lg leading-relaxed">
            The cognitive kernel is written in Plan 9 C — a clean dialect of ANSI C with
            Plan 9 system calls for namespace management, process forking, and 9P2000 file operations.
          </p>
        </motion.div>

        {/* Code viewer */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="code-block rounded-lg overflow-hidden"
        >
          {/* File tabs */}
          <div className="flex items-center border-b border-border bg-void/50">
            {codeFiles.map((file, i) => (
              <button
                key={file.name}
                onClick={() => setActiveFile(i)}
                className={`px-4 py-2.5 text-xs font-mono transition-colors border-b-2 ${
                  activeFile === i
                    ? "text-cyan-glow border-b-cyan-glow bg-void-lighter/30"
                    : "text-muted-foreground border-b-transparent hover:text-foreground hover:bg-void-lighter/20"
                }`}
              >
                {file.name}
              </button>
            ))}
            <div className="ml-auto px-4 py-2.5 text-xs font-mono text-muted-foreground">
              {codeFiles[activeFile].label}
            </div>
          </div>

          {/* Code content */}
          <CodeViewer lines={codeFiles[activeFile].lines} />

          {/* Compile command */}
          <div className="border-t border-border px-5 py-3 bg-void/50 flex items-center gap-2">
            <span className="text-green-glow text-xs">$</span>
            <span className="font-mono text-xs text-muted-foreground">
              {activeFile === 2
                ? "mk all"
                : `6c ${codeFiles[activeFile].name} && 6l -o ${codeFiles[activeFile].name.replace('.c', '')} ${codeFiles[activeFile].name.replace('.c', '.6')}`
              }
            </span>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
