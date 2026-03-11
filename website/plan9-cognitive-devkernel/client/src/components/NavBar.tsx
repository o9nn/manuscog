import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X } from "lucide-react";

const navItems = [
  { label: "Architecture", href: "#composition" },
  { label: "Namespace", href: "#namespace" },
  { label: "Temporal", href: "#temporal" },
  { label: "Promises", href: "#promises" },
  { label: "Grid", href: "#grid" },
  { label: "DevEnv", href: "#devenv" },
  { label: "Code", href: "#code" },
  { label: "Autognosis", href: "#autognosis" },
];

export function NavBar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        scrolled
          ? "glass-panel border-b border-cyan-glow/10"
          : "bg-transparent"
      }`}
    >
      <div className="container flex items-center justify-between h-16">
        <a href="#" className="flex items-center gap-3 group">
          <div className="w-8 h-8 rounded border border-cyan-glow/40 flex items-center justify-center bg-void-light/50 group-hover:box-glow-cyan transition-all duration-300">
            <span className="font-mono text-cyan-glow text-xs font-bold">9</span>
          </div>
          <span className="font-display font-bold text-lg tracking-wide text-foreground">
            Plan9<span className="text-cyan-glow">Cog</span>
          </span>
        </a>

        {/* Desktop nav */}
        <div className="hidden lg:flex items-center gap-1">
          {navItems.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="px-3 py-2 text-sm font-mono text-muted-foreground hover:text-cyan-glow transition-colors duration-200"
            >
              {item.label}
            </a>
          ))}
        </div>

        {/* Mobile toggle */}
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="lg:hidden p-2 text-muted-foreground hover:text-cyan-glow"
        >
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="lg:hidden glass-panel border-t border-cyan-glow/10"
          >
            <div className="container py-4 flex flex-col gap-2">
              {navItems.map((item) => (
                <a
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className="px-3 py-2 text-sm font-mono text-muted-foreground hover:text-cyan-glow transition-colors"
                >
                  {item.label}
                </a>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
