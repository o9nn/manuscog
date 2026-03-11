export function Footer() {
  return (
    <footer className="border-t border-border py-12">
      <div className="container">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-8 rounded border border-cyan-glow/40 flex items-center justify-center bg-void-light/50">
                <span className="font-mono text-cyan-glow text-xs font-bold">9</span>
              </div>
              <span className="font-display font-bold text-lg tracking-wide">
                Plan9<span className="text-cyan-glow">Cog</span>
              </span>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed max-w-xs">
              A self-aware cognitive development kernel for Plan 9 from Bell Labs.
              Everything is a file server.
            </p>
          </div>

          <div>
            <h4 className="font-mono text-xs text-cyan-glow uppercase tracking-widest mb-4">Composition</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>inferno-devcontainer</li>
              <li>manuscog-cognitive-devkernel</li>
              <li>function-creator</li>
              <li>promise-lambda-attention</li>
            </ul>
          </div>

          <div>
            <h4 className="font-mono text-xs text-cyan-glow uppercase tracking-widest mb-4">Resources</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>Plan 9 from Bell Labs</li>
              <li>9front</li>
              <li>OpenCog Framework</li>
              <li>9P2000 Protocol</li>
            </ul>
          </div>
        </div>

        <div className="mt-10 pt-6 border-t border-border flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-muted-foreground font-mono">
            skill-creator( function-creator( inferno-devcontainer( manuscog ) =&gt; plan9 ) )
          </p>
          <p className="text-xs text-muted-foreground font-mono">
            /cognitive/autognosis/metrics/convergence → 0.001
          </p>
        </div>
      </div>
    </footer>
  );
}
