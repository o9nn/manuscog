/**
 * Plan 9 Cognitive DevKernel — Home Page
 * Design: "Dark Namespace" — Cybernetic deep-space interface
 * Colors: void black, cyan glow, amber glow, green glow
 * Fonts: Rajdhani (display), Space Grotesk (body), Geist Mono (code)
 */

import { HeroSection } from "@/components/sections/HeroSection";
import { CompositionSection } from "@/components/sections/CompositionSection";
import { NamespaceSection } from "@/components/sections/NamespaceSection";
import { TemporalSection } from "@/components/sections/TemporalSection";
import { PromiseSection } from "@/components/sections/PromiseSection";
import { GridSection } from "@/components/sections/GridSection";
import { DevEnvSection } from "@/components/sections/DevEnvSection";
import { CodeSection } from "@/components/sections/CodeSection";
import { AutognosisSection } from "@/components/sections/AutognosisSection";
import { NavBar } from "@/components/NavBar";
import { Footer } from "@/components/Footer";

export default function Home() {
  return (
    <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
      <NavBar />
      <main>
        <HeroSection />
        <CompositionSection />
        <NamespaceSection />
        <TemporalSection />
        <PromiseSection />
        <GridSection />
        <DevEnvSection />
        <CodeSection />
        <AutognosisSection />
      </main>
      <Footer />
    </div>
  );
}
