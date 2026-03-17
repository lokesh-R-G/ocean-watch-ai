import { Waves } from "lucide-react";

const Footer = () => {
  return (
    <footer className="glass-card rounded-none border-x-0 border-b-0 px-6 py-4">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-2">
          <Waves className="h-4 w-4 text-primary" />
          <p className="text-xs text-muted-foreground">
            <span className="text-foreground font-medium">
              AI Ocean Plastic Monitoring System
            </span>{" "}
            — Tracking and predicting ocean plastic movement in the Bay of
            Bengal using satellite imagery and AI-driven analysis.
          </p>
        </div>
        <p className="text-[10px] text-muted-foreground font-mono">
          © 2026 AOPMS · Bay of Bengal Initiative
        </p>
      </div>
    </footer>
  );
};

export default Footer;
