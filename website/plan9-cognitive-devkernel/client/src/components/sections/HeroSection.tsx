import { motion } from "framer-motion";

const HERO_BG = "https://private-us-east-1.manuscdn.com/sessionFile/FDshEBmHlts6l0zq412iE5/sandbox/SAeb7OAxLYOBIAehkl9CvD-img-1_1771313809000_na1fn_aGVyby1iZw.png?x-oss-process=image/resize,w_1920,h_1920/format,webp/quality,q_80&Expires=1798761600&Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9wcml2YXRlLXVzLWVhc3QtMS5tYW51c2Nkbi5jb20vc2Vzc2lvbkZpbGUvRkRzaEVCbUhsdHM2bDB6cTQxMmlFNS9zYW5kYm94L1NBZWI3T0F4TFlPQklBZWhrbDlDdkQtaW1nLTFfMTc3MTMxMzgwOTAwMF9uYTFmbl9hR1Z5YnkxaVp3LnBuZz94LW9zcy1wcm9jZXNzPWltYWdlL3Jlc2l6ZSx3XzE5MjAsaF8xOTIwL2Zvcm1hdCx3ZWJwL3F1YWxpdHkscV84MCIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTc5ODc2MTYwMH19fV19&Key-Pair-Id=K2HSFNDJXOU9YS&Signature=G5V92RWTJcq3RdKq1pesgnuIRHmV3jOdymz~oi9HJkLX2WOQyKeK0RC9eiQm3fFQjGH9-4o-r6Z2mgwH8t3i-f8ImCSrad4NC6Frtv6mmdHPqIj0YALvl7Cx6onHj7cE1kjku8KXiXdb8Ukh7eLsuimx8ewVNNrD03mHuLPMV9DehZViFTREPKAQ2AG5arF7G6R2nbYvk43swwmmTSiS1~kb3EtxkOPNqMdQPAVdPe6wOCXDsxHGPQgAS5osC4qpT4otO~qSbPdj2LZb0nIFu80S9mxW2HydVAqfeCF~-97M1KJOCw4y~cwvm6sthNVK-HiIHvdzSlfKCVo6j5XJXw__";

export function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background image */}
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: `url(${HERO_BG})` }}
      />
      {/* Overlay gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-background/40 via-background/60 to-background" />

      {/* Scanline overlay */}
      <div className="absolute inset-0 scanlines pointer-events-none" />

      <div className="relative z-10 container text-center px-4">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        >
          {/* Tag line */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-cyan-glow/20 bg-void-light/50 mb-8">
            <span className="w-2 h-2 rounded-full bg-green-glow animate-pulse" />
            <span className="font-mono text-xs text-cyan-glow tracking-wider">
              COGNITIVE KERNEL ACTIVE
            </span>
          </div>

          {/* Main title */}
          <h1 className="font-display font-bold text-5xl sm:text-6xl md:text-7xl lg:text-8xl tracking-tight mb-6">
            <span className="text-foreground">Plan 9</span>
            <br />
            <span className="text-cyan-glow glow-cyan">Cognitive DevKernel</span>
          </h1>

          {/* Subtitle */}
          <p className="max-w-2xl mx-auto text-lg sm:text-xl text-muted-foreground leading-relaxed mb-8">
            A self-aware cognitive development kernel for Plan 9 from Bell Labs.
            Every cognitive service is a file server. Every namespace binding is a cognitive connection.
          </p>

          {/* Expression */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5, duration: 0.6 }}
            className="code-block inline-block px-6 py-3 rounded-lg text-sm"
          >
            <span className="text-green-glow">skill-creator</span>
            <span className="text-muted-foreground">(</span>
            <span className="text-amber-glow">function-creator</span>
            <span className="text-muted-foreground">(</span>
            <span className="text-cyan-glow">inferno-devcontainer</span>
            <span className="text-muted-foreground">(</span>
            <span className="text-foreground">manuscog</span>
            <span className="text-muted-foreground">) =&gt; </span>
            <span className="text-cyan-glow">"plan9"</span>
            <span className="text-muted-foreground">))</span>
          </motion.div>
        </motion.div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2 }}
          className="absolute bottom-10 left-1/2 -translate-x-1/2"
        >
          <motion.div
            animate={{ y: [0, 8, 0] }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
            className="w-6 h-10 rounded-full border-2 border-cyan-glow/30 flex items-start justify-center p-1.5"
          >
            <div className="w-1.5 h-2.5 rounded-full bg-cyan-glow/60" />
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
